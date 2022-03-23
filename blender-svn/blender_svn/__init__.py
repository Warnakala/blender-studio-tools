# ***** BEGIN GPL LICENSE BLOCK *****
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
# ***** END GPL LICENCE BLOCK *****
#
# (c) 2021, Blender Foundation - Paul Golter

import logging

import bpy

import importlib

from . import prefs, props, ops, client, ui

bl_info = {
    "name": "Blender SVN",
    "author": "Paul Golter",
    "description": "Blender Add-on to interact with Subversion. Used by other add-ons in Blender-Studio-Tools.",
    "blender": (3, 1, 0),
    "version": (0, 1, 0),
    "location": "View3D",
    "warning": "",
    "doc_url": "",
    "tracker_url": "",
    "category": "Generic",
}

logger = logging.getLogger("SVN")

modules = [
    prefs,
    props,
    ops,
    client,
    ui,
]

def reload() -> None:
    global modules

    for m in modules:
        importlib.reload(m)


_need_reload = "prefs" in locals()
if _need_reload:
    reload()

# ----------------REGISTER--------------.


def register() -> None:
    for m in modules:
        if hasattr(m, 'registry'):
            for c in m.registry:
                bpy.utils.register_class(c)
        if hasattr(m, 'register'):
            m.register()

def unregister() -> None:
    for m in modules:
        if hasattr(m, 'registry'):
            for c in m.registry:
                bpy.utils.unregister_class(c)
        if hasattr(m, 'unregister'):
            m.unregister()
