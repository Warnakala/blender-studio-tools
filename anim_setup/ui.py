import bpy

from .ops import (
    AS_OT_create_action,
)


class AS_PT_vi3d_main(bpy.types.Panel):
    """
    Panel in 3dview that displays main functions for anim-setup.
    """

    bl_category = "Anim Setup"
    bl_label = "Main"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_order = 10

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout

        row = layout.row(align=True)
        row.operator(AS_OT_create_action.bl_idname)


# ---------REGISTER ----------

classes = [AS_PT_vi3d_main]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
