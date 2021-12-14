import bpy
from .ops import GC_OT_convert_to_grease_pencil

class GC_PT_3dview(bpy.types.Panel):
    bl_category = "Grease Converter"
    bl_label = "Convert"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout

        row = layout.row(align=True)
        row.operator(GC_OT_convert_to_grease_pencil.bl_idname)


# ---------REGISTER ----------.

classes = [
    GC_PT_3dview
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

