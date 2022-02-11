import bpy


def redraw_ui() -> None:
    """
    Forces blender to redraw the UI.
    """
    for screen in bpy.data.screens:
        for area in screen.areas:
            area.tag_redraw()


def get_addon_prefs() -> bpy.types.AddonPreferences:
    return bpy.context.preferences.addons[__package__].preferences


def is_file_saved() -> bool:
    return bool(bpy.data.filepath)
