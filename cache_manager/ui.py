from pathlib import Path

import bpy
from .ops import CM_OT_cache_export, CM_OT_cache_list_actions
from . import blend, prefs, props


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
        collections = list(props.get_cache_collections(context))

        # filepath
        row = layout.row()
        row.label(text=f"Cache Directory: {self._get_cachedir_path(context)}")

        # uilist
        row = layout.row()
        row.template_list(
            "CM_UL_collection_cache_list",
            "collection_cache_list",
            context.scene,
            "cm_collections",
            context.scene,
            "cm_collections_index",
            rows=5,
            type="DEFAULT",
        )
        col = row.column(align=True)
        col.operator(
            CM_OT_cache_list_actions.bl_idname, icon="ADD", text=""
        ).action = "ADD"
        col.operator(
            CM_OT_cache_list_actions.bl_idname, icon="REMOVE", text=""
        ).action = "REMOVE"

        row = layout.row(align=True)
        row.operator(
            CM_OT_cache_export.bl_idname, text=f"Cache {len(collections)} Collections"
        )

    def _get_cachedir_path(self, context: bpy.types.Context) -> str:
        addon_prefs = prefs.addon_prefs_get(context)
        if prefs.is_cachedir_valid(context):
            return Path(addon_prefs.cachedir_path).as_posix()
        return "Invalid"


class CM_UL_collection_cache_list(bpy.types.UIList):
    def draw_item(
        self, context, layout, data, item, icon, active_data, active_propname, index
    ):
        if self.layout_type in {"DEFAULT", "COMPACT"}:
            split = layout.split(factor=0.6)
            split.prop(
                item.coll_ptr,
                "name",
                text="",
                emboss=False,
                icon="OUTLINER_COLLECTION",
            )
            split.label(text=f"/{blend.gen_filename_collection(item.coll_ptr)}")

        elif self.layout_type in {"GRID"}:
            layout.alignment = "CENTER"
            layout.label(text="", icon_value=layout.icon(item.coll_ptr))


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
