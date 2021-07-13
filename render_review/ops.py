import sys
import math
import subprocess
import shutil
from pathlib import Path
from typing import Set, Union, Optional, List, Dict, Any, Tuple

import bpy

from render_review import vars, prefs, opsdata, util, kitsu

from render_review.exception import NoImageSequenceAvailableException
from render_review.log import LoggerFactory
from render_review.geo_seq import SequenceRect
from render_review.geo import Grid, NestedRectangle

logger = LoggerFactory.getLogger(name=__name__)


class RR_OT_sqe_create_review_session(bpy.types.Operator):
    """
    Look in tomain render folder of shot defined by context.scene.rr.render_dir_path.
    It will search all available folder for preview sequences (.jpg / .png). Each found image
    sequence will be loaded in the sequence editor. Has enable blender_kitsu option that will
    create a linked metastrip for the loaded shot on the top most channel.
    """

    bl_idname = "rr.sqe_create_review_session"
    bl_label = "Create Review Session"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return bool(context.scene.rr.is_render_dir_valid)

    def execute(self, context: bpy.types.Context) -> Set[str]:
        addon_prefs = prefs.addon_prefs_get(context)
        image_data_blocks: bpy.types.Image = []
        render_dir = Path(context.scene.rr.render_dir_path)
        shot_folders: List[Path] = []

        # if render is sequence folder user wants to review whole seqeuence
        if opsdata.is_sequence_dir(render_dir):
            shot_folders.extend(list(render_dir.iterdir()))
        else:
            shot_folders.append(render_dir)

        shot_folders.sort(key=lambda d: d.name)
        prev_frame_end: int = 0

        for shot_folder in shot_folders:

            logger.info("Processing %s", shot_folder.name)

            imported_sequences: bpy.types.ImageSequence = []

            # find existing output dirs
            shot_name = opsdata.get_shot_name_from_dir(shot_folder)
            output_dirs = [
                d
                for d in shot_folder.iterdir()
                if d.is_dir() and "__intermediate" not in d.name
            ]
            output_dirs = sorted(output_dirs, key=lambda d: d.name)

            # 070_0010_A.lighting is the latest render > with current structure
            # this folder is [0] in output dirs > needs to be moved to [-1]
            output_dirs.append(output_dirs[0])
            output_dirs.pop(0)

            # init sqe
            if not context.scene.sequence_editor:
                context.scene.sequence_editor_create()

            # load preview seqeunces in vse
            for idx, dir in enumerate(output_dirs):
                # compose frames found text
                frames_found_text = opsdata.gen_frames_found_text(dir)

                try:
                    # get best preview files sequence
                    image_sequence = opsdata.get_best_preview_sequence(dir)

                except NoImageSequenceAvailableException:
                    # if no preview files available create an empty image strip
                    # this assumes that when a folder is there exr sequences are available to inspect
                    logger.warning("%s found no preview sequence", dir.name)
                    exr_files = opsdata.gather_files_by_suffix(
                        dir, output=list, search_suffixes=[".exr"]
                    )

                    if not exr_files:
                        logger.error("%s found no exr or preview sequence", dir.name)
                        continue

                    logger.info("%s found %i exr frames", dir.name, len(image_sequence))
                    image_sequence = exr_files[0]

                else:
                    logger.info(
                        "%s found %i preview frames", dir.name, len(image_sequence)
                    )

                finally:

                    # get frame start
                    frame_start = prev_frame_end or int(image_sequence[0].stem)

                    # create new image strip
                    strip = context.scene.sequence_editor.sequences.new_image(
                        dir.name,
                        image_sequence[0].as_posix(),
                        idx + 1,
                        frame_start,
                    )

                    # extend strip elements with all the available frames
                    for f in image_sequence[1:]:
                        strip.elements.append(f.name)

                    """
                    # create image datablock to read metadata like resolution
                    img = bpy.data.images.load(
                        image_sequence[0].as_posix(), check_existing=True
                    )
                    img.name = image_sequence[0].parent.name + "_PREVIEW"
                    img.source = "SEQUENCE"
                    image_data_blocks.append(img)
                    """

                    # set strip properties
                    strip.mute = True if image_sequence[0].suffix == ".exr" else False
                    strip.rr.shot_name = shot_folder.name
                    strip.rr.is_render = True
                    strip.rr.frames_found_text = frames_found_text

                    imported_sequences.append(strip)

            # query the strip that is the longest for metastrip and prev_frame_end
            imported_sequences.sort(key=lambda s: s.frame_final_duration)
            strip_longest = imported_sequences[-1]

            # perform kitsu operations if enabled
            if addon_prefs.enable_blender_kitsu and imported_sequences:

                if kitsu.is_auth_and_project():

                    shot_name = shot_folder.name
                    sequence_name = shot_folder.parent.name

                    # create metastrip
                    metastrip = kitsu.create_meta_strip(context, strip_longest)

                    # link metastrip
                    kitsu.link_strip_by_name(
                        context, metastrip, shot_name, sequence_name
                    )

                else:
                    logger.error(
                        "Unable to perform kitsu operations. No active project or no authorized"
                    )

            prev_frame_end = strip_longest.frame_final_end

        # set scene resolution to resolution of laoded image
        context.scene.render.resolution_x = vars.RESOLUTION[0]
        context.scene.render.resolution_y = vars.RESOLUTION[1]

        # change frame range and frame start
        opsdata.fit_frame_range_to_strips(context)
        context.scene.frame_current = context.scene.frame_start

        # scan for approved renders, will modify strip.rr.is_approved prop
        # which controls the custom gpu overlay
        opsdata.update_is_approved(context)
        util.redraw_ui()

        self.report(
            {"INFO"},
            f"Imported {len(imported_sequences)} Render Sequences",
        )

        return {"FINISHED"}


class RR_OT_setup_review_workspace(bpy.types.Operator):
    """
    Deletes all non Video Editing Workspaces. Appends Video Editing workspace
    Replaces File Browser area with Image Editor.
    """

    bl_idname = "rr.setup_review_workspace"
    bl_label = "Setup Review Workspace"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context: bpy.types.Context) -> Set[str]:

        # remove non video editing workspaces
        for ws in bpy.data.workspaces:
            if ws.name != "Video Editing":
                bpy.ops.workspace.delete({"workspace": ws})

        # add / load video editing workspace
        if "Video Editing" not in [ws.name for ws in bpy.data.workspaces]:
            blender_version = bpy.app.version  # gets (3, 0, 0)
            blender_version_str = f"{blender_version[0]}.{blender_version[1]}"
            ws_filepath = (
                Path(bpy.path.abspath(bpy.app.binary_path)).parent
                / blender_version_str
                / "scripts/startup/bl_app_templates_system/Video_Editing/startup.blend"
            )
            bpy.ops.workspace.append_activate(
                idname="Video Editing",
                filepath=ws_filepath.as_posix(),
            )
        else:
            context.window.workspace = bpy.data.workspaces["Video Editing"]

        # change video editing workspace media browser to image editor
        for window in context.window_manager.windows:
            screen = window.screen

            for area in screen.areas:
                if area.type == "FILE_BROWSER":
                    area.type = "IMAGE_EDITOR"

        # init sqe
        if not context.scene.sequence_editor:
            context.scene.sequence_editor_create()

        self.report({"INFO"}, "Setup Render Review Workspace")

        return {"FINISHED"}


class RR_OT_sqe_inspect_exr_sequence(bpy.types.Operator):
    """"""

    bl_idname = "rr.sqe_inspect_exr_sequence"
    bl_label = "Inspect EXR"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        active_strip = context.scene.sequence_editor.active_strip
        image_editor = opsdata.get_image_editor(context)
        return bool(
            active_strip
            and active_strip.type == "IMAGE"
            and active_strip.rr.is_render
            and image_editor
        )

    def execute(self, context: bpy.types.Context) -> Set[str]:
        active_strip = context.scene.sequence_editor.active_strip
        image_editor = opsdata.get_image_editor(context)
        output_dir = Path(bpy.path.abspath(active_strip.directory))

        # find exr sequence
        exr_seq = [
            f for f in output_dir.iterdir() if f.is_file() and f.suffix == ".exr"
        ]
        if not exr_seq:
            self.report({"ERROR"}, f"Found no exr sequence in: {output_dir.as_posix()}")
            return {"CANCELLED"}

        exr_seq.sort(key=lambda p: p.name)
        exr_seq_frame_start = int(exr_seq[0].stem)
        offset = exr_seq_frame_start - active_strip.frame_final_start

        # remove all images with same filepath that are already laoded
        img_to_rm: bpy.types.Image = []
        for img in bpy.data.images:
            if Path(bpy.path.abspath(img.filepath)) == exr_seq[0]:
                img_to_rm.append(img)

        for img in img_to_rm:
            bpy.data.images.remove(img)

        # create new image datablock
        image = bpy.data.images.load(exr_seq[0].as_posix(), check_existing=True)
        image.name = exr_seq[0].parent.name + "_RENDER"
        image.source = "SEQUENCE"
        image.colorspace_settings.name = "Linear"

        # set active image
        image_editor.spaces.active.image = image
        image_editor.spaces.active.image_user.frame_duration = 5000
        image_editor.spaces.active.image_user.frame_offset = offset

        return {"FINISHED"}


class RR_OT_sqe_clear_exr_inspect(bpy.types.Operator):
    """"""

    bl_idname = "rr.sqe_clear_exr_inspect"
    bl_label = "Clear EXR Inspect"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        image_editor = cls._get_image_editor(context)
        return bool(image_editor and image_editor.spaces.active.image)

    def execute(self, context: bpy.types.Context) -> Set[str]:
        image_editor = self._get_image_editor(context)
        image_editor.spaces.active.image = None
        return {"FINISHED"}

    @classmethod
    def _get_image_editor(self, context: bpy.types.Context) -> Optional[bpy.types.Area]:

        image_editor = None

        for area in bpy.context.screen.areas:
            if area.type == "IMAGE_EDITOR":
                image_editor = area

        return image_editor


class RR_OT_sqe_approve_render(bpy.types.Operator):
    """
    Copies the selected strip render from the farm_output to the frame_storage.
    Existing render in frame_storage will be renamed for extra backup.
    """

    bl_idname = "rr.sqe_approve_render"
    bl_label = "Approve Render"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        active_strip = context.scene.sequence_editor.active_strip
        addon_prefs = prefs.addon_prefs_get(bpy.context)

        return bool(
            addon_prefs.is_frame_storage_valid
            and active_strip
            and active_strip.type == "IMAGE"
            and active_strip.rr.is_render
        )

    def execute(self, context: bpy.types.Context) -> Set[str]:

        active_strip = context.scene.sequence_editor.active_strip
        strip_dir = Path(bpy.path.abspath(active_strip.directory))
        frame_storage_path = opsdata.get_frame_storage_path(active_strip)
        frame_storage_backup_path = opsdata.get_frame_storage_backup_path(active_strip)
        metadata_path = opsdata.get_frame_storage_metadata_path(active_strip)

        # create frame storage path if not exists yet
        if frame_storage_path.exists():

            # delete backup if exists
            if frame_storage_backup_path.exists():
                shutil.rmtree(frame_storage_backup_path)

            # rename current to backup
            frame_storage_path.rename(frame_storage_backup_path)
            logger.info(
                "Created backup: %s > %s",
                frame_storage_path.name,
                frame_storage_backup_path.name,
            )
        else:
            frame_storage_path.mkdir(parents=True)
            logger.info(
                "Created dir in frame storage: %s", frame_storage_path.as_posix()
            )

        # copy dir
        shutil.copytree(
            strip_dir,
            frame_storage_path,
            dirs_exist_ok=True,
        )
        logger.info(
            "Copied: %s \nTo: %s", strip_dir.as_posix(), frame_storage_path.as_posix()
        )

        # udpate metadata json
        if not metadata_path.exists():
            metadata_path.touch()
            opsdata.save_to_json(
                {"source_current": strip_dir.as_posix(), "source_backup": ""},
                metadata_path,
            )
            logger.info("Created metadata.json: %s", metadata_path.as_posix())
        else:
            json_dict = opsdata.load_json(metadata_path)
            # soure backup will get value from old source current
            json_dict["source_backup"] = json_dict["source_current"]
            # source current will get value from strip dir
            json_dict["source_current"] = strip_dir.as_posix()

            opsdata.save_to_json(json_dict, metadata_path)

        # scan for approved renders
        opsdata.update_is_approved(context)
        util.redraw_ui()

        # log
        self.report({"INFO"}, f"Updated {frame_storage_path.name} in frame storage")
        logger.info("Updated metadata in: %s", metadata_path.as_posix())

        return {"FINISHED"}

    def invoke(self, context, event):
        active_strip = context.scene.sequence_editor.active_strip
        frame_storage_path = opsdata.get_frame_storage_path(active_strip)
        width = 200 + len(frame_storage_path.as_posix()) * 5
        return context.window_manager.invoke_props_dialog(self, width=width)

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        active_strip = context.scene.sequence_editor.active_strip
        strip_dir = Path(bpy.path.abspath(active_strip.directory))
        frame_storage_path = opsdata.get_frame_storage_path(active_strip)

        layout.separator()
        layout.row(align=True).label(text="From Farm Output:", icon="RENDER_ANIMATION")
        layout.row(align=True).label(text=strip_dir.as_posix())

        layout.separator()
        layout.row(align=True).label(text="To Frame Storage:", icon="FILE_TICK")
        layout.row(align=True).label(text=frame_storage_path.as_posix())

        layout.separator()
        layout.row(align=True).label(text="Update Frame Storage?")


class RR_OT_sqe_update_is_approved(bpy.types.Operator):
    """
    Scans sequence editor and checks for each render strip if it is approved
    by reading the metadata.json file.
    """

    bl_idname = "rr.update_is_approved"
    bl_label = "Update is Approved"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return bool(context.scene.sequence_editor.sequences_all)

    def execute(self, context: bpy.types.Context) -> Set[str]:
        approved_strips = opsdata.update_is_approved(context)

        if approved_strips:
            self.report(
                {"INFO"},
                f"Found approved {'render' if len(approved_strips) == 1 else 'renders'}: {', '.join(s.name for s in approved_strips)}",
            )
        else:
            self.report({"INFO"}, "Found no approved renders")
        return {"FINISHED"}


class RR_OT_open_path(bpy.types.Operator):
    """
    Opens cls.filepath in explorer. Supported for win / mac / linux.
    """

    bl_idname = "rr.open_path"
    bl_label = "Open Path"

    filepath: bpy.props.StringProperty(  # type: ignore
        name="Filepath",
        description="Filepath that will be opened in explorer",
        default="",
    )

    def execute(self, context: bpy.types.Context) -> Set[str]:

        if not self.filepath:
            self.report({"ERROR"}, "Can't open empty path in explorer")
            return {"CANCELLED"}

        filepath = Path(self.filepath)
        if filepath.is_file():
            filepath = filepath.parent

        if not filepath.exists():
            filepath = self._find_latest_existing_folder(filepath)

        if sys.platform == "darwin":
            subprocess.check_call(["open", filepath.as_posix()])

        elif sys.platform == "linux2" or sys.platform == "linux":
            subprocess.check_call(["xdg-open", filepath.as_posix()])

        elif sys.platform == "win32":
            os.startfile(filepath.as_posix())

        else:
            self.report(
                {"ERROR"}, f"Can't open explorer. Unsupported platform {sys.platform}"
            )
            return {"CANCELLED"}

        return {"FINISHED"}

    def _find_latest_existing_folder(self, path: Path) -> Path:
        if path.exists() and path.is_dir():
            return path
        else:
            return self._find_latest_existing_folder(path.parent)


class RR_OT_sqe_isolate_strip_exit(bpy.types.Operator):
    """
    Exits isolat strip view.
    """

    bl_idname = "rr.sqe_isolate_strip_exit"
    bl_label = "Unmute all strips"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context: bpy.types.Context) -> Set[str]:

        for i in context.scene.rr.isolate_view:
            try:
                strip = context.scene.sequence_editor.sequences[i.name]
            except KeyError:
                logger.error("Exit isolate view: Strip does not exist %s", i.name)
                continue

            strip.mute = i.mute

        # clear all items
        context.scene.rr.isolate_view.clear()

        return {"FINISHED"}


class RR_OT_sqe_isolate_strip_enter(bpy.types.Operator):
    """
    Hides all other strips except for the selected strips in sequence editor.
    """

    bl_idname = "rr.sqe_isolate_strip_enter"
    bl_label = "Isolate Strip"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        active_strip = context.scene.sequence_editor.active_strip
        return bool(active_strip)

    def execute(self, context: bpy.types.Context) -> Set[str]:

        sequences = list(context.scene.sequence_editor.sequences_all)

        if context.scene.rr.isolate_view.items():
            bpy.ops.rr.sqe_isolate_strip_exit()

        # mute all and save state to restore later
        for s in sequences:
            # save this state to restore it later
            item = context.scene.rr.isolate_view.add()
            item.name = s.name
            item.mute = s.mute
            s.mute = True

        # unmute selected
        for s in context.selected_sequences:
            s.mute = False

        return {"FINISHED"}


class RR_OT_sqe_push_to_edit(bpy.types.Operator):
    """
    This operator pushes the active render strip to the edit. Only .mp4 files will be pushed to edit.
    If the .mp4 file is not existent but the preview .jpg sequence is in the render folder. This operator
    creates an .mp4 with ffmpeg. The .mp4 file will be named after the flamenco naming convention, but when
    copied over to the edit storage it will be renamed and gets a version string.

    """

    bl_idname = "rr.sqe_push_to_edit"
    bl_label = "Push to edit"
    bl_description = ""

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        active_strip = context.scene.sequence_editor.active_strip
        return bool(
            active_strip and active_strip.type == "IMAGE" and active_strip.rr.is_render
        )

    def execute(self, context: bpy.types.Context) -> Set[str]:
        active_strip = context.scene.sequence_editor.active_strip

        render_dir = Path(bpy.path.abspath(active_strip.directory))
        edit_storage_dir = Path(opsdata.get_edit_storage_path(active_strip))
        shot_name = edit_storage_dir.parent.name
        metadata_path = edit_storage_dir / "metadata.json"

        # -------------GET MP4 OR CREATE WITH FFMPEG ---------------
        # try to get render_mp4_path will throw error if no jpg files are available
        try:
            mp4_path = Path(opsdata.get_farm_output_mp4_path(active_strip))
        except NoImageSequenceAvailableException:
            # no jpeg files available
            self.report(
                {"ERROR"}, f"No preview files available in {render_dir.as_posix()}"
            )
            return {"CANCELLED"}

        # if mp4 path does not exists use ffmpeg to create preview file
        if not mp4_path.exists():
            preview_files = opsdata.get_best_preview_sequence(render_dir)
            fffmpeg_command = f"ffmpeg -start_number {int(preview_files[0].stem)} -framerate {vars.FPS} -i {render_dir.as_posix()}/%06d{preview_files[0].suffix} -c:v libx264 -preset medium -crf 23 -pix_fmt yuv420p {mp4_path.as_posix()}"
            logger.info("Creating .mp4 with ffmpeg")
            subprocess.call(fffmpeg_command, shell=True)
            logger.info("Created .mp4: %s", mp4_path.as_posix())
        else:
            logger.info("Found existing .mp4 file: %s", mp4_path.as_posix())

        # --------------COPY MP4 TO EDIT STORAGE ----------------

        # create edit path if not exists yet
        if not edit_storage_dir.exists():
            edit_storage_dir.mkdir(parents=True)
            logger.info("Created dir in edit storage: %s", edit_storage_dir.as_posix())

        # get edit_filepath
        edit_filepath = self.get_edit_filepath(active_strip)

        # copy mp4 to edit filepath
        shutil.copy2(mp4_path.as_posix(), edit_filepath.as_posix())
        logger.info(
            "Copied: %s \nTo: %s", mp4_path.as_posix(), edit_filepath.as_posix()
        )

        # ----------------UPDATE METADATA.JSON ------------------

        # create metadata json
        if not metadata_path.exists():
            metadata_path.touch()
            logger.info("Created metadata.json: %s", metadata_path.as_posix())
            opsdata.save_to_json({}, metadata_path)

        # udpate metadata json
        json_obj = opsdata.load_json(metadata_path)
        json_obj[edit_filepath.name] = mp4_path.as_posix()
        opsdata.save_to_json(
            json_obj,
            metadata_path,
        )
        logger.info("Updated metadata in: %s", metadata_path.as_posix())

        # log
        self.report(
            {"INFO"},
            f"Pushed to edit: {edit_filepath.as_posix()}",
        )
        return {"FINISHED"}

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        active_strip = context.scene.sequence_editor.active_strip
        edit_filepath = self.get_edit_filepath(active_strip)

        try:
            mp4_path = Path(opsdata.get_farm_output_mp4_path(active_strip))
        except NoImageSequenceAvailableException:
            layout.separator()
            layout.row(align=True).label(
                text="No preview files available", icon="ERROR"
            )
            return

        text = "From Farm Output:"
        if not mp4_path.exists():
            text = "From Farm Output (will be created with ffmpeg):"

        layout.separator()
        layout.row(align=True).label(text=text, icon="RENDER_ANIMATION")
        layout.row(align=True).label(text=mp4_path.as_posix())

        layout.separator()
        layout.row(align=True).label(text="To Edit Storage:", icon="FILE_TICK")
        layout.row(align=True).label(text=edit_filepath.as_posix())

        layout.separator()
        layout.row(align=True).label(text="Copy to Edit Storage?")

    def invoke(self, context, event):
        active_strip = context.scene.sequence_editor.active_strip
        try:
            mp4_path = Path(opsdata.get_farm_output_mp4_path(active_strip))
        except NoImageSequenceAvailableException:
            width = 200
        else:
            width = 200 + len(mp4_path.as_posix()) * 5
        return context.window_manager.invoke_props_dialog(self, width=width)

    def get_edit_filepath(self, strip: bpy.types.ImageSequence) -> Path:
        render_dir = Path(bpy.path.abspath(strip.directory))
        edit_storage_dir = Path(opsdata.get_edit_storage_path(strip))

        # find latest edit version
        existing_files: List[Path] = []
        increment = "v001"
        if edit_storage_dir.exists():
            for file in edit_storage_dir.iterdir():
                if not file.is_file():
                    continue

                if not file.name.startswith(opsdata.get_shot_dot_task_type(render_dir)):
                    continue

                version = util.get_version(file.name)
                if not version:
                    continue

                if (
                    file.name.replace(version, "")
                    == f"{opsdata.get_shot_dot_task_type(render_dir)}..mp4"
                ):
                    existing_files.append(file)

            existing_files.sort(key=lambda f: f.name)

            # get version string
            if len(existing_files) > 0:
                latest_version = util.get_version(existing_files[-1].name)
                increment = "v{:03}".format(int(latest_version.replace("v", "")) + 1)

        # compose edit filepath of new mp4 file
        edit_filepath = (
            edit_storage_dir
            / f"{opsdata.get_shot_dot_task_type(render_dir)}.{increment}.mp4"
        )
        return edit_filepath


class RR_OT_make_contactsheet(bpy.types.Operator):
    """ """

    bl_idname = "rr.make_contactsheet"
    bl_label = "Make Contact Sheet"
    bl_description = ""

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return bool(context.scene.sequence_editor.sequences_all)

    def execute(self, context: bpy.types.Context) -> Set[str]:

        sequences: List[bpy.types.Sequence] = context.selected_sequences

        if not sequences:
            # if nothing selected take a continious row of the top most sequences
            sequences = opsdata.get_top_level_strips_continious(context)

            # select sequences
            bpy.ops.sequencer.select_all(action="DESELECT")
            for s in sequences:
                s.select = True

        row_count = None
        start_frame = 1

        if len(sequences) > 31:  # one color strip will be added later as background
            self.report(
                {"ERROR"},
                f"Can only process max 31 strips. Selected Sequences: {len(sequences)}",
            )
            return {"CANCELLED"}

        # get contactsheet metadata
        sqe_editor = opsdata.get_sqe_editor(context)
        orig_proxy_render_size = sqe_editor.spaces.active.proxy_render_size
        orig_use_proxies = sqe_editor.spaces.active.use_proxies

        # create new scene
        scene_orig = bpy.context.scene
        bpy.ops.scene.new(type="FULL_COPY")  # changes active scene, makes copy
        scene_tmp = bpy.context.scene
        scene_tmp.name = "contactsheet"
        logger.info("Create tmp scene for contactsheet: %s", scene_tmp.name)

        # save contactsheet metadata
        sqe_editor = opsdata.get_sqe_editor(context)
        sqe_editor.spaces.active.proxy_render_size = "PROXY_25"
        sqe_editor.spaces.active.use_proxies = True
        scene_tmp.rr.is_contactsheet = True
        scene_tmp.rr.contactsheet_meta.scene = scene_orig
        scene_tmp.rr.contactsheet_meta.use_proxies = orig_use_proxies
        scene_tmp.rr.contactsheet_meta.proxy_render_size = orig_proxy_render_size

        # get sequences in new scene
        seq_rm: List[bpy.types.Sequence] = [
            s
            for s in scene_tmp.sequence_editor.sequences_all
            if not s.select
            or s.type not in ["IMAGE", "MOVIE"]
            or (s.type == "IMAGE" and s.elements[0].filename.endswith(".exr"))
        ]

        for s in seq_rm:
            scene_tmp.sequence_editor.sequences.remove(s)

        sequences = list(scene_tmp.sequence_editor.sequences_all)
        sequences.sort(key=self.get_sorting_tuple)

        # Place black color strip in channel 1
        color_strip = context.scene.sequence_editor.sequences.new_effect(
            "background", "COLOR", 1, start_frame, frame_end=start_frame + 1
        )
        color_strip.color = (0, 0, 0)

        # Place all sequences on top of each other and make them start at the same frame.
        for idx, seq in enumerate(sequences):
            seq.channel = (idx + 1) + 1
            seq.frame_start = start_frame
            seq.blend_type = "ALPHA_OVER"

        # elongate all strips to the strip with the longest duration
        tmp_sequences = sorted(sequences, key=lambda s: s.frame_final_end)
        tmp_sequences.insert(0, color_strip)
        max_end: int = tmp_sequences[-1].frame_final_end
        for strip in tmp_sequences:
            if strip.frame_final_end < max_end:
                strip.frame_final_end = max_end

        # scene settings
        # change frame range and frame start
        self.set_render_settings(context)
        self.set_output_path(context)
        self.set_sqe_area_settings(context)

        # create content list for grid
        if context.scene.rr.use_custom_rows:
            row_count = context.scene.rr.rows

        sqe_rects: List[SequenceRect] = [SequenceRect(seq) for seq in sequences]
        content: List[NestedRectangle] = [
            NestedRectangle(0, 0, srect.width, srect.height, child=srect)
            for srect in sqe_rects
        ]
        grid = Grid.from_content(
            0,
            0,
            context.scene.rr.contactsheet_x,
            context.scene.rr.contactsheet_y,
            content,
            row_count=row_count,
        )
        grid.scale_content(0.9)

        return {"FINISHED"}

    def get_sorting_tuple(self, strip: bpy.types.Sequence) -> Tuple[int, int]:
        return (strip.frame_final_start, strip.channel)

    def set_sqe_area_settings(self, context: bpy.types.Context) -> None:
        sqe_editor = opsdata.get_sqe_editor(context)
        sqe_editor.spaces.active.proxy_render_size = "PROXY_25"
        sqe_editor.spaces.active.use_proxies = True

    def set_render_settings(self, context: bpy.types.Context) -> None:
        opsdata.fit_frame_range_to_strips(context)
        context.scene.frame_current = context.scene.frame_start
        context.scene.render.resolution_x = context.scene.rr.contactsheet_x
        context.scene.render.resolution_y = context.scene.rr.contactsheet_y
        context.scene.render.image_settings.file_format = "PNG"
        context.scene.render.image_settings.color_mode = "RGB"
        context.scene.render.image_settings.color_depth = "8"
        context.scene.render.image_settings.compression = 15

    def set_output_path(self, context: bpy.types.Context) -> None:
        addon_prefs = prefs.addon_prefs_get(context)
        cs_dir = Path(addon_prefs.contactsheet_dir)
        render_dir = Path(context.scene.rr.render_dir_path)

        if not render_dir:
            logger.warning(
                "Failed to set output settings. Invalid context.scene.rr.render_dir"
            )
            return

        if not cs_dir:
            logger.warning(
                "Failed to set output settings. Invalid addon_prefs.contactsheet_dir"
            )
            return

        if opsdata.is_shot_dir(render_dir):
            seqeunce_name = render_dir.parent.name

        elif opsdata.is_sequence_dir(render_dir):
            seqeunce_name = render_dir.name

        # set output path
        context.scene.render.filepath = cs_dir.joinpath(
            f"{seqeunce_name}_contactsheet.png"
        ).as_posix()


class RR_OT_exit_contactsheet(bpy.types.Operator):
    """ """

    bl_idname = "rr.exit_contactsheet"
    bl_label = "Exit Contact Sheet"
    bl_description = ""

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return bool(context.scene.rr.is_contactsheet)

    def execute(self, context: bpy.types.Context) -> Set[str]:
        cs_scene = context.scene
        cs_scene_name = cs_scene.name

        # change active scene to orig scene before cs
        context.window.scene = context.scene.rr.contactsheet_meta.scene

        # restore proxy settings from rr.contactsheet_meta
        sqe_editor = opsdata.get_sqe_editor(context)
        sqe_editor.spaces.active.proxy_render_size = (
            cs_scene.rr.contactsheet_meta.proxy_render_size
        )
        sqe_editor.spaces.active.use_proxies = cs_scene.rr.contactsheet_meta.use_proxies

        # remove cs scene
        bpy.data.scenes.remove(cs_scene)

        self.report({"INFO"}, f"Exited and deleted scene: {cs_scene_name}")

        return {"FINISHED"}


# ----------------REGISTER--------------


classes = [
    RR_OT_sqe_create_review_session,
    RR_OT_setup_review_workspace,
    RR_OT_sqe_inspect_exr_sequence,
    RR_OT_sqe_clear_exr_inspect,
    RR_OT_sqe_approve_render,
    RR_OT_sqe_update_is_approved,
    RR_OT_open_path,
    RR_OT_sqe_isolate_strip_enter,
    RR_OT_sqe_isolate_strip_exit,
    RR_OT_sqe_push_to_edit,
    RR_OT_make_contactsheet,
    RR_OT_exit_contactsheet,
]

addon_keymap_items = []


def register():
    global addon_keymap_items

    for cls in classes:
        bpy.utils.register_class(cls)

    # register hotkeys
    keymap = bpy.context.window_manager.keyconfigs.addon.keymaps.new(name="Window")

    # isolate strip
    addon_keymap_items.append(
        keymap.keymap_items.new("rr.sqe_isolate_strip_enter", value="PRESS", type="ONE")
    )

    # umute all
    addon_keymap_items.append(
        keymap.keymap_items.new(
            "rr.sqe_isolate_strip_exit", value="PRESS", type="ONE", alt=True
        )
    )
    for kmi in addon_keymap_items:
        logger.info(
            "Registered new hotkey: %s : %s", kmi.type, kmi.properties.bl_rna.name
        )


def unregister():
    global addon_keymap_items
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    # remove hotkeys
    keymap = bpy.context.window_manager.keyconfigs.addon.keymaps["Window"]
    for kmi in addon_keymap_items:
        logger.info("Remove  hotkey: %s : %s", kmi.type, kmi.properties.bl_rna.name)
        keymap.keymap_items.remove(kmi)

    addon_keymap_items.clear()
