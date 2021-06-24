from typing import Set, Union, Optional, List, Dict

import bpy

from render_review.ops import (
    RR_OT_sqe_create_review_session,
    RR_OT_setup_review_workspace,
    RR_OT_sqe_inspect_exr_sequence,
    RR_OT_sqe_clear_exr_inspect,
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

        if active_strip:
            # create box
            layout = self.layout
            box = layout.box()
            box.label(text="Render", icon="RESTRICT_RENDER_OFF")

            # inspect exr
            row = box.row(align=True)
            row.operator(RR_OT_sqe_inspect_exr_sequence.bl_idname, icon="VIEWZOOM")
            row.operator(RR_OT_sqe_clear_exr_inspect.bl_idname, text="", icon="X")


# ----------------REGISTER--------------

classes = [
    RR_PT_render_review,
]


def register():

    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
