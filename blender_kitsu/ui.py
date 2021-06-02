import bpy


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
