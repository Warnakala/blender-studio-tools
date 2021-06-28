import sys
import subprocess
import shutil
import json
from pathlib import Path
from typing import Set, Union, Optional, List, Dict, Any

import bpy

from render_review import vars, prefs, opsdata, util
from render_review.log import LoggerFactory


logger = LoggerFactory.getLogger(name=__name__)


class RR_OT_sqe_create_review_session(bpy.types.Operator):
    """"""

    bl_idname = "rr.sqe_create_review_session"
    bl_label = "Create Review Session"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return bool(context.scene.rr.is_render_dir_valid)

    def execute(self, context: bpy.types.Context) -> Set[str]:

        imported_valid_sequence: bpy.types.ImageSequence = []
        imported_invalid_sequence: bpy.types.ImageSequence = []
        image_data_blocks: bpy.types.Image = []

        # find existing output dirs
        render_dir = Path(context.scene.rr.render_dir_path)
        shot_name = context.scene.rr.shot_name

        output_dirs = [
            d
            for d in render_dir.iterdir()
            if d.is_dir() and "__intermediate" not in d.name
        ]
        output_dirs = sorted(output_dirs, key=lambda d: d.name)

        # 070_0010_A.lighting is the latest render > with current structure
        # this folder is [0] in output dirs > needs to be moved to [-1]
        output_dirs.append(output_dirs[0])
        output_dirs.pop(0)

        output_dirs_str = "\n".join([d.name for d in output_dirs])
        logger.info(f"Found {len(output_dirs)} output dirs:\n{output_dirs_str}")

        # init sqe
        if not context.scene.sequence_editor:
            context.scene.sequence_editor_create()

        # load preview seqeunces in vse
        for idx, dir in enumerate(output_dirs):
            # gather all preview files that eiher end with .jpg or .png
            files_dict = opsdata.gather_files_by_suffix(
                dir, output=dict, search_suffixes=[".jpg", ".png", ".exr"]
            )
            files_list = []
            frames_found_text = ""
            for suffix, file_list in files_dict.items():
                if suffix in [".jpg", ".png"]:
                    files_list.append(file_list)
                frames_found_text += f" | {suffix}: {len(file_list)}"

            # replace first occurence, we dont want that at the beginning
            frames_found_text = frames_found_text.replace(
                " | ",
                "",
            )

            if files_list:
                # if preview files were found (could be either jpg or png) takt the one with
                # more frame
                preview_files = sorted(files_list, key=lambda l: len(l))[-1]
                logger.info("%s found %i frames", dir.name, len(preview_files))

                # load image seqeunce if found
                strip = context.scene.sequence_editor.sequences.new_image(
                    dir.name,
                    preview_files[0].as_posix(),
                    idx + 1,
                    int(preview_files[0].stem),
                )
                # extend strip elements with all the frames
                for f in preview_files[1:]:
                    strip.elements.append(f.name)

                # create image datablock to read metadata like resolution
                img = bpy.data.images.load(
                    preview_files[0].as_posix(), check_existing=True
                )
                img.name = preview_files[0].parent.name + "_PREVIEW"
                img.source = "SEQUENCE"
                image_data_blocks.append(img)

                imported_valid_sequence.append(strip)

            else:
                # add empty image sequence
                strip = context.scene.sequence_editor.sequences.new_image(
                    dir.name,
                    "",
                    idx + 1,
                    101,
                )
                strip.directory = dir.as_posix() + "/"
                imported_invalid_sequence.append(strip)

            # set strip properties
            strip.rr.is_render = True
            strip.rr.frames_found_text = frames_found_text

        # set scene resolution to resolution of laoded image
        context.scene.render.resolution_x = vars.RESOLUTION[0]
        context.scene.render.resolution_y = vars.RESOLUTION[1]

        # scan for approved renders
        opsdata.update_is_approved(context)
        util.redraw_ui()

        self.report(
            {"INFO"},
            f"Imported {len(imported_invalid_sequence) + len(imported_valid_sequence)} Render Sequences",
        )

        return {"FINISHED"}


class RR_OT_setup_review_workspace(bpy.types.Operator):
    """"""

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
                print(area.type)
                if area.type == "FILE_BROWSER":
                    area.type = "IMAGE_EDITOR"

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
        image_editor = cls._get_image_editor(context)
        return bool(
            active_strip.type == "IMAGE" and active_strip.rr.is_render and image_editor
        )

    def execute(self, context: bpy.types.Context) -> Set[str]:
        active_strip = context.scene.sequence_editor.active_strip
        image_editor = self._get_image_editor(context)
        output_dir = Path(bpy.path.abspath(active_strip.directory))

        # find exr sequence
        exr_seq = [
            f for f in output_dir.iterdir() if f.is_file() and f.suffix == ".exr"
        ]
        if not exr_seq:
            self.report({"ERROR"}, f"Found no exr sequence in: {output_dir.as_posix()}")
            return {"CANCELLED"}

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

        return {"FINISHED"}

    @classmethod
    def _get_image_editor(self, context: bpy.types.Context) -> Optional[bpy.types.Area]:

        image_editor = None

        for area in bpy.context.screen.areas:
            if area.type == "IMAGE_EDITOR":
                image_editor = area

        return image_editor


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
    """"""

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
        return context.window_manager.invoke_props_dialog(self, width=600)

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
    """"""

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
    """"""

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


# ----------------REGISTER--------------


classes = [
    RR_OT_sqe_create_review_session,
    RR_OT_setup_review_workspace,
    RR_OT_sqe_inspect_exr_sequence,
    RR_OT_sqe_clear_exr_inspect,
    RR_OT_sqe_approve_render,
    RR_OT_sqe_update_is_approved,
    RR_OT_open_path,
]


def register():

    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
