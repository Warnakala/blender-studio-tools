from pathlib import Path
from typing import Set, Union, Optional, List, Dict

import bpy

from render_review import vars
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
            if d.is_dir()
            and "__intermediate" not in d.name
            and d.name != f"{shot_name}.lighting"
        ]
        output_dirs = sorted(output_dirs, key=lambda d: d.name)

        output_dirs_str = "\n".join([d.name for d in output_dirs])
        logger.info(f"Found {len(output_dirs)} output dirs:\n{output_dirs_str}")

        # init sqe
        if not context.scene.sequence_editor:
            context.scene.sequence_editor_create()

        # load preview seqeunces in vse
        for idx, dir in enumerate(output_dirs):
            # check if previe sequence exists
            jpg_files = []
            png_files = []

            for f in dir.iterdir():
                if not f.is_file():
                    continue

                if f.suffix == ".jpg":
                    jpg_files.append(f)

                elif f.suffix == ".png":
                    png_files.append(f)

            preview_files = sorted([jpg_files, png_files], key=lambda l: len(l))[-1]
            preview_files = sorted(preview_files, key=lambda f: f.name)

            logger.info("%s found %i frames", dir.name, len(preview_files))

            if preview_files:
                # load image seqeunce if found
                """
                op_file_list = [{"name": f.name} for f in preview_files]
                bpy.ops.sequencer.image_strip_add(
                    directory=dir.as_posix() + "/",
                    files=op_file_list,
                    frame_start=int(preview_files[0].stem),
                    frame_end=context.scene.frame_start + len(preview_files) - 1,
                    relative_path=False,
                    channel=idx,
                )
                """
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

        # set scene resolution to resolution of laoded image
        context.scene.render.resolution_x = vars.RESOLUTION[0]
        context.scene.render.resolution_y = vars.RESOLUTION[1]

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
        for window in bpy.context.window_manager.windows:
            screen = window.screen

            for area in screen.areas:
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
        return bool(active_strip.type == "IMAGE" and active_strip.rr.is_render)

    def execute(self, context: bpy.types.Context) -> Set[str]:

        if not self.confirm:
            self.report({"WARNING"}, "Approvin render aborted")
            return {"CANCELLED"}

        active_strip = context.scene.sequence_editor.active_strip
        symlink_path = self._gen_symlink_path(active_strip)
        target_path = Path(bpy.path.abspath(active_strip.directory))

        return {"FINISHED"}

    def invoke(self, context, event):
        active_strip = context.scene.sequence_editor.active_strip
        self.confirm = False
        symlink_path = self._gen_symlink_path(active_strip)

        if not symlink_path.exists():
            self.report({"ERROR"}, f"Symlink not found: {symlink_path.as_posix()}")
            return {"CANCELLED"}

        return context.window_manager.invoke_props_dialog(self, width=700)

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        active_strip = context.scene.sequence_editor.active_strip
        strip_dir = Path(bpy.path.abspath(active_strip.directory))
        symlink_path = self._gen_symlink_path(active_strip)

        layout.row(align=True).label(text=f"Symlink at   : {symlink_path.as_posix()}")
        layout.row(align=True).label(
            text=f"Points to      : {symlink_path.readlink().as_posix()}"
        )
        layout.row(align=True).label(text=f"New Target: {strip_dir.as_posix()}")

        col = layout.column()
        col.prop(self, "confirm", text=f"Approve {active_strip.name} ?")

    def _gen_symlink_path(self, strip: bpy.types.ImageSequence) -> Path:
        output_dir = Path(strip.directory)
        symlink_dir_name = "tmp." + output_dir.parent.name + ".lighting"
        symlink_path = output_dir.parent / symlink_dir_name
        return symlink_path


# ----------------REGISTER--------------


classes = [
    RR_OT_sqe_create_review_session,
    RR_OT_setup_review_workspace,
    RR_OT_sqe_inspect_exr_sequence,
    RR_OT_sqe_clear_exr_inspect,
    RR_OT_sqe_approve_render,
]


def register():

    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
