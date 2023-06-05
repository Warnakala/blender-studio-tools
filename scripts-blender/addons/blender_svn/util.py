# SPDX-License-Identifier: GPL-2.0-or-later
# (c) 2021, Blender Foundation - Paul Golter
# (c) 2022, Blender Foundation - Demeter Dzadik

from time import time

import bpy

package_name = __package__

def get_addon_prefs(context):
    return context.preferences.addons[__package__].preferences

def dots():
    return "." * int((time() % 10) + 3)

def redraw_viewport(context=None) -> None:
    """This causes the sidebar UI to refresh without having to mouse-hover it."""
    context = bpy.context
    if not context:
        return
    for area in context.screen.areas:
        if area.type in {'VIEW_3D', 'FILE_BROWSER'}:
            area.tag_redraw()
