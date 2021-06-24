from typing import Set, Union, Optional, List, Dict

import bpy

from render_review.ops import RR_OT_sqe_create_review_session


class RR_PT_render_review(bpy.types.Panel):
    """ """

    bl_category = "Render Review"
    bl_label = "Render Review"
    bl_space_type = "SEQUENCE_EDITOR"
    bl_region_type = "UI"
    bl_order = 10
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context: bpy.types.Context) -> None:

        # create box
        layout = self.layout
        box = layout.box()
        box.label(text="Review", icon="CAMERA_DATA")

        row = box.row(align=True)
        row.prop(context.scene.rr, "render_dir")

        if context.scene.rr.is_render_dir_valid:
            row = box.row(align=True)
            row.label(text=f"Shot: {context.scene.rr.shot_name}")

        row = box.row(align=True)
        row.operator(RR_OT_sqe_create_review_session.bl_idname, icon="PLAY")


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
