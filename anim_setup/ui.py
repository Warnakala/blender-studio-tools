import bpy

from . import opsdata

from .ops import (
    AS_OT_create_actions,
    AS_OT_setup_workspaces,
    AS_OT_load_latest_edit,
    AS_OT_import_camera,
    AS_OT_import_camera_action,
    AS_OT_shift_anim,
    AS_OT_get_frame_shift,
    AS_OT_apply_additional_settings,
    AS_OT_import_asset_actions,
    AS_OT_exclude_colls
)


class AS_PT_vi3d_main(bpy.types.Panel):
    """
    Panel in 3dview that displays main functions for anim-setup.
    """

    bl_category = "Anim Setup"
    bl_label = "Main"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_order = 10

    def draw(self, context: bpy.types.Context) -> None:
        valid_colls = opsdata.get_valid_collections(context)
        layout = self.layout


        # ------general ops
        box = layout.box()
        box.label(text="General", icon="MODIFIER")

        column = box.column(align=True)

        # workspace
        column.operator(AS_OT_setup_workspaces.bl_idname)

        # load edit
        column.operator(AS_OT_load_latest_edit.bl_idname)

        # apply additional settings
        column.operator(
            AS_OT_apply_additional_settings.bl_idname
        )

        #---------action and anim ops
        box = layout.box()
        box.label(text="Animation and Actions", icon="KEYTYPE_KEYFRAME_VEC")

        box.label(text=f"Previs file: {opsdata.get_previs_file(context)}")


        column = box.column(align=True)

        # import camera action
        column.operator(AS_OT_import_camera_action.bl_idname)

        # import action
        column.operator(
            AS_OT_import_asset_actions.bl_idname, text=f"Import Asset Actions"
        )

        # import camera
        #column = box_cam.column(align=True)
        #column.operator(AS_OT_import_camera.bl_idname)


        # shift animation
        split = column.split(factor=0.3, align=True)
        split.prop(context.scene.anim_setup, "shift_frames", text="")
        split.operator(AS_OT_shift_anim.bl_idname, text="Shift Anim")

        # create actions
        row = box.row(align=True)
        row.operator(
            AS_OT_create_actions.bl_idname, text=f"Create {len(valid_colls)} actions"
        )
        # udpate shift amount
        #column.operator(AS_OT_get_frame_shift.bl_idname)

         #---------scene ops
        box = layout.box()
        box.label(text="Scene", icon="SCENE_DATA")

        # exclude colls
        row = box.row(align=True)
        row.operator(
            AS_OT_exclude_colls.bl_idname, text="Exclude Collections"
        )



# ---------REGISTER ----------

classes = [AS_PT_vi3d_main]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
