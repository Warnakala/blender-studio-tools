import bpy
from blender_kitsu.anim.ops import KITSU_OT_anim_pull_frame_range


def draw_error_box(layout: bpy.types.UILayout) -> bpy.types.UILayout:
    box = layout.box()
    box.label(text="Error", icon="ERROR")
    return box


def draw_error_active_project_unset(box: bpy.types.UILayout) -> bpy.types.UILayout:
    row = box.row(align=True)
    row.label(text="No Active Project")
    row.operator(
        "preferences.addon_show", text="Open Addon Preferences"
    ).module = "blender_kitsu"


def draw_error_invalid_playblast_root_dir(
    box: bpy.types.UILayout,
) -> bpy.types.UILayout:
    row = box.row(align=True)
    row.label(text="Invalid Playblast Root Directory")
    row.operator(
        "preferences.addon_show", text="Open Addon Preferences"
    ).module = "blender_kitsu"


def draw_error_frame_range_outdated(
    box: bpy.types.UILayout,
) -> bpy.types.UILayout:

    row = box.row(align=True)
    row.label(text="Frame Range Outdated")
    row.operator(KITSU_OT_anim_pull_frame_range.bl_idname, icon="FILE_REFRESH")
