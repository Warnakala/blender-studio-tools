import bpy
from typing import Optional
from .util import prefs_get, zsession_get, zsession_auth
from .ops import (
    BZ_OT_SQE_PushThumbnail,
    BZ_OT_SQE_InitShot,
    BZ_OT_SQE_DelShot,
    BZ_OT_SQE_LinkShot,
    BZ_OT_SQE_PushNewShot,
    BZ_OT_SQE_PushShotMeta,
    BZ_OT_SQE_PullShotMeta,
)


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


class BZ_PT_SQE_shot_tools(bpy.types.Panel):
    """
    Panel in sequence editor that shows .blezou properties of active strip. (shot, sequence)
    """

    bl_idname = "blezou.pt_sqe_shot_tools"
    bl_category = "Blezou"
    bl_label = "Shot Tools"
    bl_space_type = "SEQUENCE_EDITOR"
    bl_region_type = "UI"
    bl_order = 30

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return True

    def draw(self, context: bpy.types.Context) -> None:

        strip = context.scene.sequence_editor.active_strip
        selshots = context.selected_sequences

        if len(selshots) > 1:
            noun = "%i Shots" % len(selshots)
        else:
            noun = "Active Shot"

        if not strip.blezou.initialized:
            layout = self.layout
            row = layout.row(align=True)
            row.operator(BZ_OT_SQE_InitShot.bl_idname, text=f"Init {noun}", icon="PLUS")
            row.operator(
                BZ_OT_SQE_LinkShot.bl_idname, text="Link Active Shot", icon="LINKED"
            )

        else:
            # strip is initialized
            layout = self.layout
            # delete operator
            row = layout.row(align=True)
            row.operator(BZ_OT_SQE_DelShot.bl_idname, text=f"Del {noun}", icon="CANCEL")
            row.operator(
                BZ_OT_SQE_LinkShot.bl_idname, text="Relink Active Shot", icon="LINKED"
            )


class BZ_PT_SQE_shot_meta(bpy.types.Panel):
    """
    Panel in sequence editor that shows .blezou properties of active strip. (shot, sequence)
    """

    bl_parent_id = "blezou.pt_sqe_shot_tools"
    bl_category = "Blezou"
    bl_label = "Metadata Active Shot"
    bl_space_type = "SEQUENCE_EDITOR"
    bl_region_type = "UI"
    bl_order = 10

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return True

    def draw(self, context: bpy.types.Context) -> None:
        strip = context.scene.sequence_editor.active_strip

        # strip is initialized and props can be displayed
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

        # id
        col = box.column(align=True)
        col.enabled = False
        col.prop(strip.blezou, "id")
        col.prop(strip.blezou, "linked")


class BZ_PT_SQE_push(bpy.types.Panel):
    """
    Panel that shows operator to sync sequence editor metadata with backend.
    """

    bl_parent_id = "blezou.pt_sqe_shot_tools"
    bl_category = "Blezou"
    bl_label = "Push"
    bl_space_type = "SEQUENCE_EDITOR"
    bl_region_type = "UI"
    bl_order = 20

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return True

    def draw(self, context: bpy.types.Context) -> None:
        prefs = prefs_get(context)
        selshots = context.selected_sequences

        if len(selshots) > 1:
            noun = "%i Shots" % len(selshots)
        else:
            noun = "Active Shot"

        layout = self.layout

        # not_linked = [s for s in selshots if not s.blezou.linked] - warn in operator if shot is missing link
        row = layout.row()
        row.operator(
            BZ_OT_SQE_PushNewShot.bl_idname,
            text=f"Push New for {noun}",
            icon="EXPORT",
        )
        row = layout.row()
        row.operator(
            BZ_OT_SQE_PushShotMeta.bl_idname,
            text=f"Push Metadata for {noun}",
            icon="EXPORT",
        )

        row = layout.row()
        row.operator(
            BZ_OT_SQE_PushThumbnail.bl_idname,
            text=f"Push Thumbnail for {noun}",
            icon="EXPORT",
        )


class BZ_PT_SQE_pull(bpy.types.Panel):
    """
    Panel that shows operator to sync sequence editor metadata with backend.
    """

    bl_parent_id = "blezou.pt_sqe_shot_tools"
    bl_category = "Blezou"
    bl_label = "Pull"
    bl_space_type = "SEQUENCE_EDITOR"
    bl_region_type = "UI"
    bl_order = 30

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return True

    def draw(self, context: bpy.types.Context) -> None:
        prefs = prefs_get(context)
        selshots = context.selected_sequences

        if len(selshots) > 1:
            noun = "%i Shots" % len(selshots)
        else:
            noun = "Active Shot"

        layout = self.layout
        row = layout.row()
        row.operator(
            BZ_OT_SQE_PullShotMeta.bl_idname,
            text=f"Pull Metadata for {noun}",
            icon="IMPORT",
        )


# ---------REGISTER ----------

classes = [
    BZ_PT_vi3d_auth,
    BZ_PT_SQE_auth,
    BZ_PT_vi3d_context,
    BZ_PT_SQE_context,
    BZ_PT_SQE_shot_tools,
    BZ_PT_SQE_shot_meta,
    BZ_PT_SQE_push,
    BZ_PT_SQE_pull,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)