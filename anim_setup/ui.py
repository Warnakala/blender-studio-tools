import bpy

from . import opsdata

from .ops import (
    AS_OT_create_actions,
    AS_OT_setup_workspaces,
    AS_OT_load_latest_edit,
    AS_OT_import_camera,
    AS_OT_import_camera_action,
    AS_OT_shift_cam_anim,
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

        # workspace
        row = layout.row(align=True)
        row.operator(AS_OT_setup_workspaces.bl_idname)

        # filepath dependent ops
        box = layout.box()
        box.label(text="", icon="MODIFIER")

        # create actions
        row = box.row(align=True)
        row.operator(
            AS_OT_create_actions.bl_idname, text=f"Create {len(valid_colls)} actions"
        )

        # load edit
        row = box.row(align=True)
        row.operator(AS_OT_load_latest_edit.bl_idname)

        # import camera
        box_cam = layout.box()
        box_cam.label(text="", icon="OUTLINER_OB_CAMERA")
        box_cam.label(text=f"Previs file: {opsdata.get_previs_file(context)}")
        column = box_cam.column(align=True)
        column.operator(AS_OT_import_camera.bl_idname)

        # import camera action
        column.operator(AS_OT_import_camera_action.bl_idname)

        # shift camera animation
        split = column.split(factor=0.3, align=True)
        split.prop(context.scene.anim_setup, "shift_frames", text="")
        split.operator(AS_OT_shift_cam_anim.bl_idname, text="Shift Anim")


# ---------REGISTER ----------

classes = [AS_PT_vi3d_main]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
