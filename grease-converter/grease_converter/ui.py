import bpy
from typing import Any, Union, Set, List
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


def menu_draw_convert_to_annotation(self: Any, context: bpy.types.Context) -> None:
    if not GC_OT_convert_to_annotation.poll(context):
        return None
    layout = self.layout
    layout.operator(GC_OT_convert_to_annotation.bl_idname, icon="STROKE")


def menu_draw_convert_to_grease_pencil(self: Any, context: bpy.types.Context) -> None:
    if not GC_OT_convert_to_grease_pencil.poll(context):
        return None
    layout = self.layout
    layout.operator(
        GC_OT_convert_to_grease_pencil.bl_idname, icon="OUTLINER_OB_GREASEPENCIL"
    )


# ---------REGISTER ----------.

classes: List[Any] = []


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.VIEW3D_MT_object_convert.append(menu_draw_convert_to_annotation)
    bpy.types.VIEW3D_PT_grease_pencil.append(menu_draw_convert_to_grease_pencil)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    bpy.types.VIEW3D_MT_object_convert.remove(menu_draw_convert_to_annotation)
    bpy.types.VIEW3D_PT_grease_pencil.remove(menu_draw_convert_to_grease_pencil)
