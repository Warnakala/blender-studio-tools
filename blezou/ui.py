import bpy
from typing import Optional
from .util import prefs_get, zsession_get, zsession_auth
from .ops import (
    BZ_OT_SQE_PushThumbnail,
    BZ_OT_SQE_InitShot,
    BZ_OT_SQE_DelShotMeta,
    BZ_OT_SQE_LinkShot,
    BZ_OT_SQE_PushNewShot,
    BZ_OT_SQE_PushDeleteShot,
    BZ_OT_SQE_PushShotMeta,
    BZ_OT_SQE_PullShotMeta,
    BZ_OT_SQE_DebugDuplicates,
    BZ_OT_SQE_DebugNotLinked,
)


def get_selshots_noun(context: bpy.types.Context) -> str:
    selshots = context.selected_sequences
    if not selshots:
        noun = "All"
    elif len(selshots) == 1:
        noun = "Active Shot"
    else:
        noun = "%i Shots" % len(selshots)

    return noun


class BZ_PT_vi3d_auth(bpy.types.Panel):
    """
    Panel in 3dview that displays email, password and login operator.
    """

    bl_category = "Blezou"
    bl_label = "Kitsu Login"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_order = 10

    def draw(self, context: bpy.types.Context) -> None:
        prefs = context.preferences.addons["blezou"].preferences
        zsession = prefs.session

        layout = self.layout

        box = layout.box()
        # box.row().prop(prefs, 'host')
        box.row().prop(prefs, "email")
        box.row().prop(prefs, "passwd")

        row = layout.row(align=True)
        if not zsession.is_auth():
            row.operator("blezou.session_start", text="Login")
        else:
            row.operator("blezou.session_end", text="Logout")


class BZ_PT_vi3d_context(bpy.types.Panel):
    """
    Panel in 3dview that enables browsing through backend data structure.
    Thought of as a menu to setup a context by selecting active production
    active sequence, shot etc.
    """

    bl_category = "Blezou"
    bl_label = "Context"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"DEFAULT_CLOSED"}
    bl_order = 20

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return True

    def draw(self, context: bpy.types.Context) -> None:
        prefs = prefs_get(context)
        layout = self.layout
        category = prefs.category  # can be either 'SHOTS' or 'ASSETS'
        item_group_data = {
            "name": "Sequence",
            "pref_name": "sequence_active",
            "operator": "blezou.sequences_load",
        }
        item_data = {
            "name": "Shot",
            "pref_name": "shot_active",
            "operator": "blezou.shots_load",
        }

        # Production
        if not prefs["project_active"].to_dict():
            prod_load_text = "Select Production"
        else:
            prod_load_text = prefs["project_active"]["name"]

        box = layout.box()
        row = box.row(align=True)
        row.operator(
            "blezou.productions_load", text=prod_load_text, icon="DOWNARROW_HLT"
        )

        # Category
        row = box.row(align=True)
        row.prop(prefs, "category", expand=True)
        if not zsession_auth(context) or not prefs["project_active"].to_dict():
            row.enabled = False

        # Sequence / AssetType
        if category == "ASSETS":
            item_group_data["name"] = "AssetType"
            item_group_data["pref_name"] = "asset_type_active"
            item_group_data["operator"] = "blezou.asset_types_load"

        row = box.row(align=True)
        item_group_text = f"Select {item_group_data['name']}"
        if not prefs["project_active"].to_dict():
            row.enabled = False
        elif prefs[item_group_data["pref_name"]]:
            item_group_text = prefs[item_group_data["pref_name"]]["name"]
        row.operator(
            item_group_data["operator"], text=item_group_text, icon="DOWNARROW_HLT"
        )

        # Shot / Asset
        if category == "ASSETS":
            item_data["name"] = "Asset"
            item_data["pref_name"] = "asset_active"
            item_data["operator"] = "blezou.assets_load"

        row = box.row(align=True)
        item_text = f"Select {item_data['name']}"
        if (
            not prefs["project_active"].to_dict()
            and prefs[item_group_data["pref_name"]]
        ):
            row.enabled = False
        elif prefs[item_data["pref_name"]]:
            item_text = prefs[item_data["pref_name"]]["name"]
        row.operator(item_data["operator"], text=item_text, icon="DOWNARROW_HLT")


class BZ_PT_SQE_auth(bpy.types.Panel):
    """
    Panel in sequence editor that displays email, password and login operator.
    """

    bl_category = "Blezou"
    bl_label = "Kitsu Login"
    bl_space_type = "SEQUENCE_EDITOR"
    bl_region_type = "UI"
    bl_order = 10

    def draw(self, context: bpy.types.Context) -> None:
        prefs = context.preferences.addons["blezou"].preferences
        zsession = prefs.session

        layout = self.layout

        box = layout.box()
        # box.row().prop(prefs, 'host')
        box.row().prop(prefs, "email")
        box.row().prop(prefs, "passwd")

        row = layout.row(align=True)
        if not zsession.is_auth():
            row.operator("blezou.session_start", text="Login")
        else:
            row.operator("blezou.session_end", text="Logout")


class BZ_PT_SQE_context(bpy.types.Panel):
    """
    Panel in sequence editor that only shows active production browser operator.
    """

    bl_category = "Blezou"
    bl_label = "Context"
    bl_space_type = "SEQUENCE_EDITOR"
    bl_region_type = "UI"
    bl_order = 20

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return True

    def draw(self, context: bpy.types.Context) -> None:
        prefs = prefs_get(context)
        layout = self.layout

        # Production
        if not prefs["project_active"]:
            prod_load_text = "Select Production"
        else:
            prod_load_text = prefs["project_active"]["name"]

        box = layout.box()
        row = box.row(align=True)
        row.operator(
            "blezou.productions_load", text=prod_load_text, icon="DOWNARROW_HLT"
        )


class BZ_PT_SQE_tools(bpy.types.Panel):
    """
    Panel in sequence editor that shows .blezou properties of active strip. (shot, sequence)
    """

    bl_idname = "BZ_PT_SQE_tools"
    bl_category = "Blezou"
    bl_label = "SEQ Editor Tools"
    bl_space_type = "SEQUENCE_EDITOR"
    bl_region_type = "UI"
    bl_order = 30

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return True

    def draw(self, context: bpy.types.Context) -> None:

        strip = context.scene.sequence_editor.active_strip
        noun = get_selshots_noun(context)

        layout = self.layout
        row = layout.row(align=True)
        row.operator(BZ_OT_SQE_InitShot.bl_idname, text=f"INIT {noun}", icon="PLUS")

        if not strip:
            # link operator
            row.operator(
                BZ_OT_SQE_LinkShot.bl_idname, text="Link Active Shot", icon="LINKED"
            )
        else:
            if not strip.blezou.initialized:
                # link operator
                row.operator(
                    BZ_OT_SQE_LinkShot.bl_idname, text="Link Active Shot", icon="LINKED"
                )
            else:
                # relink operator
                row.operator(
                    BZ_OT_SQE_LinkShot.bl_idname,
                    text="Relink Active Shot",
                    icon="LINKED",
                )

        # delete operator
        selshots = context.selected_sequences
        if len(selshots) > 1:
            noun = "%i Shots" % len(selshots)
        else:
            noun = "Active Shot"
        row = layout.row(align=True)
        row.operator(
            BZ_OT_SQE_DelShotMeta.bl_idname,
            text=f"Delete Metadata {noun}",
            icon="CANCEL",
        )


class BZ_PT_SQE_shot_meta(bpy.types.Panel):
    """
    Panel in sequence editor that shows .blezou properties of active strip. (shot, sequence)
    """

    bl_parent_id = "BZ_PT_SQE_tools"
    bl_category = "Blezou"
    bl_label = "Metadata Active Shot"
    bl_space_type = "SEQUENCE_EDITOR"
    bl_region_type = "UI"
    bl_order = 10

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return bool(context.scene.sequence_editor.active_strip)

    def draw(self, context: bpy.types.Context) -> None:

        strip = context.scene.sequence_editor.active_strip
        layout = self.layout
        box = layout.box()
        col = box.column(align=True)

        # sequence
        col.prop(strip.blezou, "sequence")

        # shot
        col.prop(strip.blezou, "shot")

        # description
        col.prop(strip.blezou, "description")
        col.enabled = False if not strip.blezou.initialized else True

        # initialized
        col = box.column(align=True)
        col.prop(strip.blezou, "initialized")
        col.enabled = False

        # id
        col = box.column(align=True)
        col.enabled = False
        col.prop(strip.blezou, "id")
        col.prop(strip.blezou, "linked")


class BZ_PT_SQE_push(bpy.types.Panel):
    """
    Panel that shows operator to sync sequence editor metadata with backend.
    """

    bl_parent_id = "BZ_PT_SQE_tools"
    bl_category = "Blezou"
    bl_label = "PUSH"
    bl_space_type = "SEQUENCE_EDITOR"
    bl_region_type = "UI"
    bl_order = 20

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return True

    def draw(self, context: bpy.types.Context) -> None:
        noun = get_selshots_noun(context)

        layout = self.layout

        row = layout.row()
        col = row.column(align=True)
        col.operator(
            BZ_OT_SQE_PushShotMeta.bl_idname,
            text=f"Push METADATA for {noun}",
            icon="SEQ_STRIP_META",
        )

        col.operator(
            BZ_OT_SQE_PushThumbnail.bl_idname,
            text=f"Push THUMBNAIL for {noun}",
            icon="IMAGE_DATA",
        )

        row = layout.row()
        col = row.column(align=True)
        col.operator(
            BZ_OT_SQE_PushNewShot.bl_idname,
            text=f"Push NEW for {noun}",
            icon="ADD",
        )
        # delete operator
        selshots = context.selected_sequences
        if len(selshots) > 1:
            noun = "%i Shots" % len(selshots)
        else:
            noun = "Active Shot"
        col.operator(
            BZ_OT_SQE_PushDeleteShot.bl_idname,
            text=f"Push DELETE for {noun}",
            icon="KEYTYPE_EXTREME_VEC",
        )


class BZ_PT_SQE_pull(bpy.types.Panel):
    """
    Panel that shows operator to sync sequence editor metadata with backend.
    """

    bl_parent_id = "BZ_PT_SQE_tools"
    bl_category = "Blezou"
    bl_label = "PULL"
    bl_space_type = "SEQUENCE_EDITOR"
    bl_region_type = "UI"
    bl_order = 30

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return True

    def draw(self, context: bpy.types.Context) -> None:
        noun = get_selshots_noun(context)

        layout = self.layout
        row = layout.row()
        row.operator(
            BZ_OT_SQE_PullShotMeta.bl_idname,
            text=f"Pull Metadata for {noun}",
            icon="SEQ_STRIP_META",
        )


class BZ_PT_SQE_debug(bpy.types.Panel):
    """
    Panel that shows operator to open a debug ui
    """

    bl_parent_id = "BZ_PT_SQE_tools"
    bl_category = "Blezou"
    bl_label = "Debug"
    bl_space_type = "SEQUENCE_EDITOR"
    bl_region_type = "UI"
    bl_order = 40

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return True

    def draw(self, context: bpy.types.Context) -> None:
        noun = get_selshots_noun(context)

        layout = self.layout
        row = layout.row()
        row.operator(
            BZ_OT_SQE_DebugDuplicates.bl_idname,
            text=f"Debug Duplicates {noun}",
            icon="MODIFIER_ON",
        )
        row = layout.row()
        row.operator(
            BZ_OT_SQE_DebugNotLinked.bl_idname,
            text=f"Debug not Linked {noun}",
            icon="MODIFIER_ON",
        )


# ---------REGISTER ----------

classes = [
    BZ_PT_vi3d_auth,
    BZ_PT_SQE_auth,
    BZ_PT_vi3d_context,
    BZ_PT_SQE_context,
    BZ_PT_SQE_tools,
    BZ_PT_SQE_shot_meta,
    BZ_PT_SQE_push,
    BZ_PT_SQE_pull,
    BZ_PT_SQE_debug,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)