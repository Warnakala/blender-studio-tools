from pathlib import Path
from typing import List, Tuple

import bpy
from .ops import (
    CM_OT_cache_export,
    CM_OT_cacheconfig_export,
    CM_OT_import_cache,
    CM_OT_import_colls_from_config,
    CM_OT_update_cache_colls_list,
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
        split_factor = 0.225
        split_factor_small = 0.95
        # category to choose between export / import
        row = layout.row(align=True)
        row.prop(context.scene.cm, "category", expand=True)

        # add some space
        row = layout.row(align=True)
        row.separator()

        # box for cache version and cacheconfig
        box = layout.box()

        # VERSION
        version_text = self._get_version_text(context)

        split = box.split(factor=split_factor, align=True)

        # version label
        split.label(text="Version:")

        if context.scene.cm.category == "EXPORT":
            sub_split = split.split(factor=split_factor_small, align=True)
            sub_split.operator(
                CM_OT_set_cache_version.bl_idname,
                icon="DOWNARROW_HLT",
                text=version_text,
            )
            sub_split.operator(
                CM_OT_add_cache_version.bl_idname,
                icon="ADD",
                text="",
            )

        else:
            split.operator(
                CM_OT_set_cache_version.bl_idname,
                icon="DOWNARROW_HLT",
                text=version_text,
            )

        # CACHEDIR
        split = box.split(factor=split_factor, align=True)

        # cachedir label
        split.label(text="Cache Directory:")

        if not context.scene.cm.is_cachedir_valid:
            split.label(text=f"Invalid. Check Addon Preferences.")

        else:
            if context.scene.cm.category == "EXPORT":
                if context.scene.cm.cachedir_path.exists():
                    sub_split = split.split(factor=1 - split_factor_small)
                    sub_split.label(icon="ERROR")
                    sub_split.prop(context.scene.cm, "cachedir", text="")

                else:
                    split.prop(context.scene.cm, "cachedir", text="")

            else:
                if not context.scene.cm.cachedir_path.exists():
                    split.label(text=f"Not found")
                else:
                    split.prop(context.scene.cm, "cachedir", text="")

        # CACHECONFIG
        split = box.split(factor=split_factor, align=True)
        # cachedir label
        split.label(text="Cacheconfig:")

        if not context.scene.cm.is_cacheconfig_valid:
            if (
                context.scene.cm.use_cacheconfig_custom
                and context.scene.cm.category == "IMPORT"
            ):
                sub_split = split.split(factor=0.95, align=True)
                sub_split.prop(context.scene.cm, "cacheconfig_custom", text="")
                sub_split.operator(
                    CM_OT_import_colls_from_config.bl_idname, icon="PLAY", text=""
                )
            else:
                split.label(text=f"Invalid. Check Addon Preferences.")

            row = box.row(align=True)
            row.prop(context.scene.cm, "use_cacheconfig_custom")

        else:
            if context.scene.cm.category == "EXPORT":

                if context.scene.cm.cacheconfig_path.exists():
                    sub_split = split.split(factor=1 - split_factor_small)
                    sub_split.label(icon="ERROR")
                    sub_split.prop(context.scene.cm, "cacheconfig", text="")

                else:
                    split.prop(context.scene.cm, "cacheconfig", text="")
            else:
                if context.scene.cm.use_cacheconfig_custom:
                    sub_split = split.split(factor=0.95, align=True)
                    sub_split.prop(context.scene.cm, "cacheconfig_custom", text="")
                    sub_split.operator(
                        CM_OT_import_colls_from_config.bl_idname, icon="PLAY", text=""
                    )

                else:
                    if not context.scene.cm.cacheconfig_path.exists():
                        split.label(text=f"Not found")

                    else:
                        sub_split = split.split(factor=0.95, align=True)
                        sub_split.prop(context.scene.cm, "cacheconfig", text="")
                        sub_split.operator(
                            CM_OT_import_colls_from_config.bl_idname,
                            icon="PLAY",
                            text="",
                        )
                row = box.row(align=True)
                row.prop(context.scene.cm, "use_cacheconfig_custom")

        # add some space
        row = layout.row(align=True)
        row.separator()

        # COLLECTION OPERATIONS
        box = layout.box()
        row = box.row(align=True)
        row.label(text="Cache Collections", icon="OUTLINER_COLLECTION")
        row.operator(
            CM_OT_update_cache_colls_list.bl_idname, icon="FILE_REFRESH", text=""
        )
        if context.scene.cm.category == "EXPORT":

            # get collections
            collections = list(props.get_cache_collections_export(context))

            # uilist
            row = box.row()
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

            row = box.row(align=True)
            row.operator(
                CM_OT_cache_export.bl_idname,
                text=f"Cache {len(collections)} Collections",
                icon="EXPORT",
            ).do_all = True

            row.operator(
                CM_OT_cacheconfig_export.bl_idname,
                text="",
                icon="ALIGN_LEFT",
            ).do_all = True

        else:
            # get collections
            collections = list(props.get_cache_collections_import(context))

            # uilist
            row = box.row()
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

            row = box.row(align=True)
            row.operator(
                CM_OT_import_cache.bl_idname,
                text="Load",
                icon="IMPORT",
            ).do_all = True
            row.operator(
                CM_OT_cache_show.bl_idname, text="Show", icon="HIDE_OFF"
            ).do_all = True

            row.operator(
                CM_OT_cache_hide.bl_idname, text="Hide", icon="HIDE_ON"
            ).do_all = True

            row.operator(
                CM_OT_cache_remove.bl_idname, text="Remove", icon="REMOVE"
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
