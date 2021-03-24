import bpy
from .bz_util import zprefs_get

def bz_prefs_clear_properties(context):
    zprefs = zprefs_get(context)

    #id properties
    zprefs['project_active'] = {}
    zprefs['sequence_active'] = {}

def ui_redraw():
    """
    Forces blender to redraw the UI.
    """
    for screen in bpy.data.screens:
        for area in screen.areas:
            area.tag_redraw()