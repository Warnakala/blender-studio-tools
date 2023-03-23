import bpy

from . import opsdata

from .ops import (
    AS_OT_create_actions,
    AS_OT_setup_workspaces,
    AS_OT_load_latest_edit,
    AS_OT_import_camera,
    AS_OT_import_camera_action,
    AS_OT_shift_anim,
    AS_OT_apply_additional_settings,
    AS_OT_import_asset_actions,
    AS_OT_exclude_colls,
    AS_OT_import_multi_assets
)


class AS_PT_view3d_general(bpy.types.Panel):
    """
    Animation Setup general operators.
    """

    bl_category = "Anim Setup"
    bl_label = "General"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_order = 10

    def draw(self, context: bpy.types.Context) -> None:
        valid_colls = opsdata.get_valid_collections(context)
        layout = self.layout
        col = layout.column(align=True)

        # Workspace.
        col.operator(AS_OT_setup_workspaces.bl_idname)

        # Load edit.
        col.operator(AS_OT_load_latest_edit.bl_idname)



class AS_PT_view3d_animation_and_actions(bpy.types.Panel):
    """
    Animation Setup main operators and properties.
    """

    bl_category = "Anim Setup"
    bl_label = "Animation and Actions"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_order = 12
    
    def draw(self, context: bpy.types.Context) -> None:
        
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        layout.label(text=f"Previs file: {opsdata.get_previs_file(context)}")

        col = layout.column(align=True)

        # Import camera action.
        col.operator(AS_OT_import_camera_action.bl_idname)

        # Import action.
        col.operator(
            AS_OT_import_asset_actions.bl_idname, text=f"Import Char Actions"
        )

        col.operator(
            AS_OT_import_multi_assets.bl_idname, text=f"Import Multi Asset Actions"
        )      

        col.separator()
        col = layout.column()

        # Shift animation.
        col.prop(context.scene.anim_setup, "layout_cut_in")
        col.separator()
        split = col.split(factor=0.5, align=True)
        split.operator(AS_OT_shift_anim.bl_idname, text="Shift Char/Cam")
        split.operator(AS_OT_shift_anim.bl_idname, text="Shift Multi").multi_assets = True

        col.separator()

        # Create actions.
        valid_collections_count = len(opsdata.get_valid_collections(context))
        row = col.row(align=True)
        row.operator(
            AS_OT_create_actions.bl_idname, text=f"Create {valid_collections_count} actions"
        )


class AS_PT_view3d_scene(bpy.types.Panel):
    """
    Animation Setup scene operators.
    """

    bl_category = "Anim Setup"
    bl_label = "Scene"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_order = 13
    
    def draw(self, context: bpy.types.Context) -> None:
        
        layout = self.layout

        # Exclude collections.
        row = layout.row(align=True)
        row.operator(
            AS_OT_exclude_colls.bl_idname, text="Exclude Collections"
        )


# ---------REGISTER ----------.

classes = [
    AS_PT_view3d_general, 
    AS_PT_view3d_animation_and_actions, 
    AS_PT_view3d_scene,
    ]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
