import bpy
from typing import Optional
from .util import prefs_get, zsession_get, zsession_auth


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
        return zsession_auth(context)

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
        if not prefs["project_active"]:
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
        if not prefs["project_active"]:
            row.enabled = False
        row.prop(prefs, "category", expand=True)

        # Sequence / AssetType
        if category == "ASSETS":
            item_group_data["name"] = "AssetType"
            item_group_data["pref_name"] = "asset_type_active"
            item_group_data["operator"] = "blezou.asset_types_load"

        row = box.row(align=True)
        item_group_text = f"Select {item_group_data['name']}"
        if not prefs["project_active"]:
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
        if not prefs["project_active"] and prefs[item_group_data["pref_name"]]:
            row.enabled = False
        elif prefs[item_data["pref_name"]]:
            item_text = prefs[item_data["pref_name"]]["name"]
        row.operator(item_data["operator"], text=item_text, icon="DOWNARROW_HLT")


class BZ_PT_SQE_context(bpy.types.Panel):
    """
    Panel in sequence editor that only shows active production browser operator.
    """

    bl_category = "Blezou"
    bl_label = "Context"
    bl_space_type = "SEQUENCE_EDITOR"
    bl_region_type = "UI"
    bl_order = 10

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return zsession_auth(context)

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


class BZ_PT_SQE_strip_props(bpy.types.Panel):
    """
    Panel in sequence editor that shows .blezou properties of active strip. (shot, sequence)
    """

    bl_category = "Blezou"
    bl_label = "Strip Properties"
    bl_space_type = "SEQUENCE_EDITOR"
    bl_region_type = "UI"
    bl_order = 20

    @classmethod
    def poll(cls, context: bpy.types.Context) -> Optional[bpy.types.Sequence]:
        return context.scene.sequence_editor.active_strip

    def draw(self, context: bpy.types.Context) -> None:
        active_strip_prop = context.scene.sequence_editor.active_strip.blezou

        layout = self.layout
        box = layout.box()
        row = box.row(align=True)
        row.prop(active_strip_prop, "sequence")
        row = box.row(align=True)
        row.prop(active_strip_prop, "shot")


class BZ_PT_SQE_sync(bpy.types.Panel):
    """
    Panel that shows operator to sync sequence editor metadata with backend.
    """

    bl_category = "Blezou"
    bl_label = "Sync"
    bl_space_type = "SEQUENCE_EDITOR"
    bl_region_type = "UI"
    bl_order = 30

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return zsession_auth(context)

    def draw(self, context: bpy.types.Context) -> None:
        prefs = prefs_get(context)

        layout = self.layout
        row = layout.row(align=True)
        row.operator("blezou.sqe_scan_track_properties", text="Scan Sequence Editor")

        """
        box = layout.box()
        row = box.row(align=True)
        row.prop(prefs, 'sqe_track_props') #TODO: Dosn"t work blender complaints it does not exist, manualli in script editr i can retrieve it
        """
        row = layout.row(align=True)
        row.operator(
            "blezou.sqe_create_strip_thumbnail", text=f"Create thumbnails from strips"
        )

        row = layout.row(align=True)
        row.operator("blezou.sqe_sync_track_properties", text=f"Push to: {prefs.host}")


# ---------REGISTER ----------

classes = [
    BZ_PT_vi3d_auth,
    BZ_PT_vi3d_context,
    BZ_PT_SQE_context,
    BZ_PT_SQE_strip_props,
    BZ_PT_SQE_sync,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)