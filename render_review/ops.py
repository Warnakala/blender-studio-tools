from pathlib import Path
from typing import Set, Union, Optional, List, Dict

import bpy


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
        # in this case we make use of ops.sequencer.movie_strip_add because
        # it provides handy auto placing,would be hard to achieve with
        # context.scene.sequence_editor.sequences.new_movie()
        override = context.copy()
        for window in bpy.context.window_manager.windows:
            screen = window.screen

            for area in screen.areas:
                if area.type == "SEQUENCE_EDITOR":
                    override["window"] = window
                    override["screen"] = screen
                    override["area"] = area

        for idx, dir in enumerate(output_dirs):
            # check if previe sequence exists
            print(dir.as_posix())
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
                op_file_list = [{"name": f.name} for f in preview_files]
                bpy.ops.sequencer.image_strip_add(
                    directory=dir.as_posix() + "/",
                    files=op_file_list,
                    frame_start=int(preview_files[0].stem),
                    frame_end=context.scene.frame_start + len(preview_files) - 1,
                    relative_path=False,
                    channel=idx,
                )
            else:
                # add empty movie sequence
                pass

        self.report(
            {"INFO"},
            f"",
        )

        return {"FINISHED"}


# ----------------REGISTER--------------

classes = [
    RR_OT_sqe_create_review_session,
]


def register():

    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
