from pathlib import Path
from typing import List, Tuple

import bpy
from .ops import (
    CM_OT_cache_export,
    CM_OT_import_cache,
    CM_OT_import_collections,
    CM_OT_cache_list_actions,
    CM_OT_assign_cachefile,
    CM_OT_cache_show,
    CM_OT_cache_hide,
    CM_OT_cache_remove,
    CM_OT_set_cache_version,
    CM_OT_add_cache_version,
)
from . import propsdata, prefs, props


class CM_PT_vi3d_cache(bpy.types.Panel):
    """
    Panel in sequence editor that displays email, password and login operator.
    """

    bl_category = "CacheManager"
    bl_label = "Cache"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_order = 10

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout

        # category to choose between export / import
        row = layout.row(align=True)
        row.prop(context.scene.cm, "category", expand=True)

        # cache version
        version_text = self._get_version_text(context)

        # show version dropdown
        row = layout.row(align=True)
        row.operator(
            CM_OT_set_cache_version.bl_idname,
            icon="DOWNARROW_HLT",
            text=version_text,
        )
        if context.scene.cm.category == "EXPORT":

            row.operator(
                CM_OT_add_cache_version.bl_idname,
                icon="ADD",
                text="",
            )

        # cachedir
        row = layout.row()
        if not context.scene.cm.is_cachedir_valid:
            row.label(text=f"Cache Directory: Invalid")
        else:
            row.prop(context.scene.cm, "cachedir", text="CachCache Directory")

        if context.scene.cm.category == "EXPORT":

            # get collections
            collections = list(props.get_cache_collections_export(context))

            # uilist
            row = layout.row()
            row.template_list(
                "CM_UL_collection_cache_list_export",
                "collection_cache_list_export",
                context.scene.cm,
                "colls_export",
                context.scene.cm,
                "colls_export_index",
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

        else:
            # get collections
            collections = list(props.get_cache_collections_import(context))

            # cacheconfig
            row = layout.row()
            if not context.scene.cm.is_cacheconfig_valid:
                row.label(text=f"Cacheconfig: Invalid")
            else:
                # split = layout.split(factor=0.9, align=True)
                row.prop(context.scene.cm, "cacheconfig", text="Cacheconfig")
                row.operator(CM_OT_import_collections.bl_idname, icon="PLAY", text="")

            # uilist
            row = layout.row()
            row.template_list(
                "CM_UL_collection_cache_list_import",
                "collection_cache_list_import",
                context.scene.cm,
                "colls_import",
                context.scene.cm,
                "colls_import_index",
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
                CM_OT_import_cache.bl_idname,
                text=f"Import Cache for {len(collections)} Collections",
                icon="IMPORT",
            ).do_all = True
            row.operator(
                CM_OT_cache_show.bl_idname, text="", icon="HIDE_OFF"
            ).do_all = True

            row.operator(
                CM_OT_cache_hide.bl_idname, text="", icon="HIDE_ON"
            ).do_all = True

            row.operator(
                CM_OT_cache_remove.bl_idname, text="", icon="REMOVE"
            ).do_all = True

    def _get_version_text(self, context: bpy.types.Context) -> str:
        version_text = "Select Version"

        if context.scene.cm.cache_version:
            version_text = context.scene.cm.cache_version

        return version_text


class CM_UL_collection_cache_list_export(bpy.types.UIList):
    def draw_item(
        self, context, layout, data, item, icon, active_data, active_propname, index
    ):
        if self.layout_type in {"DEFAULT", "COMPACT"}:
            split = layout.split(factor=0.5, align=True)
            split.prop(
                item.coll_ptr,
                "name",
                text="",
                emboss=False,
                icon="OUTLINER_COLLECTION",
            )
            split = split.split(factor=0.75, align=True)
            split.label(text=f"/{propsdata.gen_cache_coll_filename(item.coll_ptr)}")
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
        coll = item.coll_ptr

        if self.layout_type in {"DEFAULT", "COMPACT"}:
            split = layout.split(factor=0.4, align=True)
            split.prop(
                coll,
                "name",
                text="",
                emboss=False,
                icon="OUTLINER_COLLECTION",
            )
            split = split.split(factor=0.7, align=True)

            cachefile = coll.cm.cachefile
            op_text = "Select Cachefile"
            if cachefile:
                op_text = Path(cachefile).name

            split.operator(
                CM_OT_assign_cachefile.bl_idname, text=op_text, icon="DOWNARROW_HLT"
            ).index = index

            if not coll.cm.is_cache_loaded:
                split.operator(
                    CM_OT_import_cache.bl_idname,
                    text="",
                    icon="IMPORT",
                ).index = index
            else:
                split.operator(
                    CM_OT_cache_remove.bl_idname, text="", icon="REMOVE"
                ).index = index

            if coll.cm.is_cache_hidden:
                split.operator(
                    CM_OT_cache_show.bl_idname, text="", icon="HIDE_ON"
                ).index = index
            else:
                split.operator(
                    CM_OT_cache_hide.bl_idname, text="", icon="HIDE_OFF"
                ).index = index

        elif self.layout_type in {"GRID"}:
            layout.alignment = "CENTER"
            layout.label(text="", icon_value=layout.icon(item.coll_ptr))


# ---------REGISTER ----------

classes = [
    CM_UL_collection_cache_list_export,
    CM_UL_collection_cache_list_import,
    CM_PT_vi3d_cache,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
