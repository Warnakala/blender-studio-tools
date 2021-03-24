import bpy 

def zsession_get(context):
    bz_prefs = context.preferences.addons['blezou'].preferences
    return bz_prefs.session

def zprefs_get(context):
    return context.preferences.addons['blezou'].preferences

def zsession_auth(context):
    return zsession_get(context).is_auth()