from pathlib import Path

import bpy
from .ops import CM_OT_cache_export, CM_OT_cache_list_actions
from . import blend, prefs


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

        row = layout.row()
        row.template_list(
            "CM_UL_collection_cache_list",
            "collection_cache_list",
            context.scene,
            "cm_collections",
            context.scene,
            "cm_collections_index",
            rows=2,
            type="DEFAULT",
        )
        col = row.column(align=True)
        col.operator(
            CM_OT_cache_list_actions.bl_idname, icon="ADD", text=""
        ).action = "ADD"
        col.operator(
            CM_OT_cache_list_actions.bl_idname, icon="REMOVE", text=""
        ).action = "REMOVE"

        collection = context.view_layer.active_layer_collection.collection
        row = layout.row(align=True)
        export_text = "Select Collection"
        if collection:
            export_text = f"Export {collection.name}"

        row.operator(CM_OT_cache_export.bl_idname, text=export_text)
        row = layout.row()
        row.label(text=f"filepath: {self._get_col_filepath(context, collection)}")

    def _get_col_filepath(
        self, context: bpy.types.Context, collection: bpy.types.Collection
    ) -> Path:
        addon_prefs = prefs.addon_prefs_get(context)
        cachedir_path = Path(addon_prefs.cachedir_path)
        if prefs.is_cachedir_valid(context):
            return cachedir_path / blend.gen_filename_collection(collection)
        return Path()


class CM_UL_collection_cache_list(bpy.types.UIList):
    def draw_item(
        self, context, layout, data, item, icon, active_data, active_propname, index
    ):
        if self.layout_type in {"DEFAULT", "COMPACT"}:
            split = layout.split(factor=0.3)
            split.label(text="Index: %d" % (index))
            split.prop(
                item.coll_ptr,
                "name",
                text="",
                emboss=False,
                icon="OUTLINER_COLLECTION",
            )

        elif self.layout_type in {"GRID"}:
            layout.alignment = "CENTER"
            layout.label(text="", icon_value=layout.icon(item.coll_ptr))

    def invoke(self, context, event):
        pass


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
        row.label(text="Future Import Ops will be here")


# ---------REGISTER ----------

classes = [
    CM_PT_vi3d_CacheExport,
    CM_UL_collection_cache_list,
    CM_PT_vi3d_CacheImport,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
