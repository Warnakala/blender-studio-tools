import bpy

class CM_PT_vi3d_CacheExport(bpy.types.Panel):
    """
    Panel in sequence editor that displays email, password and login operator.
    """

    bl_category = "CacheManager"
    bl_label = "Export"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_order = 10

    def draw(self, context: bpy.types.Context) -> None:

        layout = self.layout

        row = layout.row(align=True)
        row.label(text='Future Export Ops will be here')

class CM_PT_vi3d_CacheImport(bpy.types.Panel):
    """
    Panel in sequence editor that displays email, password and login operator.
    """

    bl_category = "CacheManager"
    bl_label = "Import"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_order = 20

    def draw(self, context: bpy.types.Context) -> None:

        layout = self.layout

        row = layout.row(align=True)
        row.label(text='Future Import Ops will be here')

# ---------REGISTER ----------

classes = [
    CM_PT_vi3d_CacheExport,
    CM_PT_vi3d_CacheImport
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
