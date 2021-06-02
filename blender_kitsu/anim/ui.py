import bpy

from pathlib import Path

from blender_kitsu import prefs, cache, ui
from blender_kitsu.anim.ops import (
    KITSU_OT_anim_create_playblast,
    KITSU_OT_anim_set_playblast_version,
    KITSU_OT_anim_increment_playblast_version,
    KITSU_OT_anim_pull_frame_range,
)
from blender_kitsu.generic.ops import KITSU_OT_open_path


class KITSU_PT_vi3d_anim_tools(bpy.types.Panel):
    """
    Panel in 3dview that exposes a set of tools that are useful for animation
    tasks, e.G playblast
    """

    bl_category = "Kitsu"
    bl_label = "Animation Tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"DEFAULT_CLOSED"}
    bl_order = 30

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return bool(
            prefs.session_auth(context)
            and cache.task_type_active_get().name == "Animation"
        )

    @classmethod
    def poll_error(cls, context: bpy.types.Context) -> bool:
        addon_prefs = prefs.addon_prefs_get(context)

        return bool(
            context.scene.kitsu_error.frame_range
            or not addon_prefs.is_playblast_root_valid
        )

    def draw(self, context: bpy.types.Context) -> None:
        addon_prefs = prefs.addon_prefs_get(context)
        layout = self.layout
        split_factor_small = 0.95

        # ERROR
        if self.poll_error(context):
            box = ui.draw_error_box(layout)
            if context.scene.kitsu_error.frame_range:
                ui.draw_error_frame_range_outdated(box)
            if not addon_prefs.is_playblast_root_valid:
                ui.draw_error_invalid_playblast_root_dir(box)

        # playblast box
        box = layout.box()
        box.label(text="Playblast")

        # if playblast directory is not valid dont show other
        if not addon_prefs.playblast_root_dir:
            split = box.split(factor=1 - split_factor_small, align=True)
            split.label(icon="ERROR")
            split.label(
                text="Invalid Playblast Root Directory. Check Addon Preferences."
            )
            return

        # if playblast directory is not valid dont show other
        if not context.scene.kitsu.playblast_dir:
            split = box.split(factor=1 - split_factor_small, align=True)
            split.label(icon="ERROR")
            split.label(text="Select Sequence and Shot in Context Tab.")
            return

        if not context.scene.camera:
            split = box.split(factor=1 - split_factor_small, align=True)
            split.label(icon="ERROR")
            split.label(text="Scene has no active camera.")
            return

        # playlast version op
        row = box.row(align=True)
        row.operator(
            KITSU_OT_anim_set_playblast_version.bl_idname,
            text=context.scene.kitsu.playblast_version,
            icon="DOWNARROW_HLT",
        )
        # playblast increment version op
        row.operator(
            KITSU_OT_anim_increment_playblast_version.bl_idname,
            text="",
            icon="ADD",
        )

        # playblast op
        row = box.row(align=True)
        row.operator(KITSU_OT_anim_create_playblast.bl_idname, icon="RENDER_ANIMATION")

        # playblast path label
        if Path(context.scene.kitsu.playblast_file).exists():
            split = box.split(factor=1 - split_factor_small, align=True)
            split.label(icon="ERROR")
            sub_split = split.split(factor=split_factor_small)
            sub_split.label(text=context.scene.kitsu.playblast_file)
            sub_split.operator(
                KITSU_OT_open_path.bl_idname, icon="FILE_FOLDER", text=""
            ).filepath = context.scene.kitsu.playblast_file
        else:
            row = box.row(align=True)
            row.label(text=context.scene.kitsu.playblast_file)
            row.operator(
                KITSU_OT_open_path.bl_idname, icon="FILE_FOLDER", text=""
            ).filepath = context.scene.kitsu.playblast_file

        # scene operators
        box = layout.box()
        box.label(text="Scene", icon="SCENE_DATA")

        # pull frame range
        row = box.row(align=True)
        row.operator(
            KITSU_OT_anim_pull_frame_range.bl_idname,
            icon="FILE_REFRESH",
        )


# ---------REGISTER ----------

classes = [
    KITSU_PT_vi3d_anim_tools,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
