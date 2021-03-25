import bpy


def zsession_get(context: bpy.types.Context):
    """
    shortcut to get zsession from blezou addon preferences
    """
    bz_prefs = context.preferences.addons["blezou"].preferences
    return bz_prefs.session


def zprefs_get(context: bpy.types.Context):
    """
    shortcut to get blezou addon preferences
    """
    return context.preferences.addons["blezou"].preferences


def zsession_auth(context: bpy.types.Context) -> bool:
    """
    shortcut to check if zession is authorized
    """
    return zsession_get(context).is_auth()