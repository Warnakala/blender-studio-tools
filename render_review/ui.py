from pathlib import Path

from typing import Set, Union, Optional, List, Dict, Any

import bpy

from render_review.ops import (
    RR_OT_sqe_create_review_session,
    RR_OT_setup_review_workspace,
    RR_OT_sqe_inspect_exr_sequence,
    RR_OT_sqe_clear_exr_inspect,
    RR_OT_sqe_approve_render,
    RR_OT_sqe_update_is_approved,
    RR_OT_open_path,
)


class RR_PT_render_review(bpy.types.Panel):
    """ """

    bl_category = "Render Review"
    bl_label = "Render Review"
    bl_space_type = "SEQUENCE_EDITOR"
    bl_region_type = "UI"
    bl_order = 10

    def draw(self, context: bpy.types.Context) -> None:

        active_strip = context.scene.sequence_editor.active_strip

        # create box
        layout = self.layout
        box = layout.box()

        # label and setup workspace
        row = box.row(align=True)
        row.label(text="Review", icon="CAMERA_DATA")
        row.operator(RR_OT_setup_review_workspace.bl_idname, text="", icon="WINDOW")

        # render dir prop
        row = box.row(align=True)
        row.prop(context.scene.rr, "render_dir")

        # shot_name label
        if context.scene.rr.is_render_dir_valid:
            row = box.row(align=True)
            row.label(text=f"Shot: {context.scene.rr.shot_name}")

        # create session
        row = box.row(align=True)
        row.operator(RR_OT_sqe_create_review_session.bl_idname, icon="PLAY")

        if active_strip and active_strip.rr.is_render:
            # create box
            layout = self.layout
            box = layout.box()
            box.label(text="Render", icon="RESTRICT_RENDER_OFF")

            # render dir name label and open file op
            row = box.row(align=True)

            # gen text for label
            label_text = f"{Path(active_strip.directory).name} | {active_strip.rr.frames_found_text}"
            row.label(text=label_text)

            row.operator(
                RR_OT_open_path.bl_idname, icon="FILEBROWSER", text=""
            ).filepath = bpy.path.abspath(active_strip.directory)

            # inspect exr
            row = box.row(align=True)
            row.operator(RR_OT_sqe_inspect_exr_sequence.bl_idname, icon="VIEWZOOM")
            row.operator(RR_OT_sqe_clear_exr_inspect.bl_idname, text="", icon="X")

            # approve render & udpate approved
            row = box.row(align=True)
            row.operator(RR_OT_sqe_approve_render.bl_idname, icon="CHECKMARK")
            row.operator(
                RR_OT_sqe_update_is_approved.bl_idname, text="", icon="FILE_REFRESH"
            )


def RR_topbar_file_new_draw_handler(self: Any, context: bpy.types.Context) -> None:
    layout = self.layout
    op = layout.operator(RR_OT_setup_review_workspace.bl_idname, text="Render Review")


# ----------------REGISTER--------------

classes = [
    RR_PT_render_review,
]


def register():

    for cls in classes:
        bpy.utils.register_class(cls)

    # append to topbar file new
    bpy.types.TOPBAR_MT_file_new.append(RR_topbar_file_new_draw_handler)


def unregister():

    # remove to topbar file new
    bpy.types.TOPBAR_MT_file_new.remove(RR_topbar_file_new_draw_handler)

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
