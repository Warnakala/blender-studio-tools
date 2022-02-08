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

from . import asset_pipeline, util, prefs

bl_info = {
    "name": "Blender Studio Pipeline",
    "author": "Paul Golter",
    "description": "Blender Studio Pipeline Add-on",
    "blender": (3, 1, 0),
    "version": (0, 1, 0),
    "location": "View3D",
    "warning": "",
    "doc_url": "",
    "tracker_url": "",
    "category": "Generic",
}

logger = logging.getLogger(__name__)

_need_reload = "asset_pipeline" in locals()

if _need_reload:
    import importlib

    prefs = importlib.reload(prefs)
    util = importlib.reload(util)
    asset_pipeline.reload()


# ----------------REGISTER--------------.


def register() -> None:
    prefs.register()
    asset_pipeline.register()


def unregister() -> None:
    prefs.unregister()
    asset_pipeline.unregister()
