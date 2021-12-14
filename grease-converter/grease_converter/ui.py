import bpy
from .ops import GC_OT_convert_to_grease_pencil, GC_OT_convert_to_annotation

class GC_PT_3dview(bpy.types.Panel):
    bl_category = "Grease Converter"
    bl_label = "Convert"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout

        box = layout.box()
        box.label(text="Active Annotation", icon="OUTLINER_DATA_GREASEPENCIL")
        row = box.row(align=True)
        row.operator(GC_OT_convert_to_grease_pencil.bl_idname)

        if issubclass(bpy.types.GreasePencil, type(context.active_object.data)):
            box = layout.box()
            box.label(text="Grease Pencil", icon="OUTLINER_OB_GREASEPENCIL")
            row = box.row(align=True)
            row.operator(GC_OT_convert_to_annotation.bl_idname)

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

