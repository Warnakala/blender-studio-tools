from pathlib import Path
from typing import List, Tuple

import bpy
from .ops import (
    CM_OT_cache_export,
    CM_OT_cache_import,
    CM_OT_process_cacheconfig,
    CM_OT_cache_list_actions,
    CM_OT_assign_cachefile,
    CM_OT_cache_show,
    CM_OT_cache_hide,
    CM_OT_cache_remove,
)
from . import blend, prefs, props


def get_cachedir_path(context: bpy.types.Context) -> str:
    addon_prefs = prefs.addon_prefs_get(context)
    if addon_prefs.is_cachedir_valid:
        return Path(addon_prefs.cachedir_path).as_posix()
    return "Invalid"


class CM_PT_vi3d_cache_export(bpy.types.Panel):
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
        row.label(text=f"Cache Directory: {get_cachedir_path(context)}")

        # uilist
        row = layout.row()
        row.template_list(
            "CM_UL_collection_cache_list_export",
            "collection_cache_list_export",
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
            CM_OT_cache_export.bl_idname,
            text=f"Cache {len(collections)} Collections",
            icon="EXPORT",
        ).do_all = True


class CM_UL_collection_cache_list_export(bpy.types.UIList):
    def draw_item(
        self, context, layout, data, item, icon, active_data, active_propname, index
    ):
        if self.layout_type in {"DEFAULT", "COMPACT"}:
            split = layout.split(factor=0.6, align=True)
            split.prop(
                item.coll_ptr,
                "name",
                text="",
                emboss=False,
                icon="OUTLINER_COLLECTION",
            )
            split = split.split(factor=0.75, align=True)
            split.label(text=f"/{blend.gen_filename_collection(item.coll_ptr)}")
            split.operator(
                CM_OT_cache_export.bl_idname,
                text="",
                icon="EXPORT",
            ).index = index

        elif self.layout_type in {"GRID"}:
            layout.alignment = "CENTER"
            layout.label(text="", icon_value=layout.icon(item.coll_ptr))


class CM_UL_collection_cache_list_import(bpy.types.UIList):
    def draw_item(
        self, context, layout, data, item, icon, active_data, active_propname, index
    ):
        if self.layout_type in {"DEFAULT", "COMPACT"}:
            split = layout.split(factor=0.4, align=True)
            split.prop(
                item.coll_ptr,
                "name",
                text="",
                emboss=False,
                icon="OUTLINER_COLLECTION",
            )
            split = split.split(factor=0.7, align=True)

            cachefile = item.coll_ptr.cm.cachefile
            op_text = "Select Cachefile"
            if cachefile:
                op_text = Path(cachefile).name

            split.operator(
                CM_OT_assign_cachefile.bl_idname, text=op_text, icon="DOWNARROW_HLT"
            ).index = index

            split.operator(
                CM_OT_cache_import.bl_idname,
                text="",
                icon="IMPORT",
            ).index = index

            split.operator(
                CM_OT_cache_show.bl_idname, text="", icon="HIDE_OFF"
            ).index = index

            split.operator(
                CM_OT_cache_hide.bl_idname, text="", icon="HIDE_ON"
            ).index = index

            split.operator(
                CM_OT_cache_remove.bl_idname, text="", icon="REMOVE"
            ).index = index

        elif self.layout_type in {"GRID"}:
            layout.alignment = "CENTER"
            layout.label(text="", icon_value=layout.icon(item.coll_ptr))


class CM_PT_vi3d_cache_import(bpy.types.Panel):
    """
    Panel in sequence editor that displays email, password and login operator.
    """

    bl_category = "CacheManager"
    bl_label = "Import"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_order = 20

    def draw(self, context: bpy.types.Context) -> None:
        addon_prefs = prefs.addon_prefs_get(context)
        layout = self.layout
        collections = list(props.get_cache_collections(context))

        # cachedir
        row = layout.row()
        row.label(text=f"Cache Directory: {get_cachedir_path(context)}")

        # cacheconfig
        row = layout.row()
        row.prop(addon_prefs, "cacheconfig", text="Cacheconfig")
        row.operator(CM_OT_process_cacheconfig.bl_idname, icon="PLAY", text="")

        # uilist
        row = layout.row()
        row.template_list(
            "CM_UL_collection_cache_list_import",
            "collection_cache_list_import",
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
            CM_OT_cache_import.bl_idname,
            text=f"Import Cache for {len(collections)} Collections",
            icon="IMPORT",
        ).do_all = True
        row.operator(CM_OT_cache_show.bl_idname, text="", icon="HIDE_OFF").do_all = True

        row.operator(CM_OT_cache_hide.bl_idname, text="", icon="HIDE_ON").do_all = True

        row.operator(CM_OT_cache_remove.bl_idname, text="", icon="REMOVE").do_all = True


# ---------REGISTER ----------

classes = [
    CM_UL_collection_cache_list_export,
    CM_UL_collection_cache_list_import,
    CM_PT_vi3d_cache_export,
    CM_PT_vi3d_cache_import,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
