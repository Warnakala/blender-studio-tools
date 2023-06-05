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
# (c) 2021, Blender Foundation


import bpy
from cache_manager import (
    cmglobals,
    logger,
    cache,
    models,
    prefs,
    propsdata,
    props,
    opsdata,
    ops,
    ui
)

logg = logger.LoggerFactory.getLogger(__name__)

bl_info = {
    "name": "Cache Manager",
    "author": "Paul Golter",
    "description": "Blender addon to streamline alembic caches of assets",
    "blender": (2, 93, 0),
    "version": (0, 1, 1),
    "location": "View3D",
    "warning": "",
    "doc_url": "",
    "tracker_url": "",
    "category": "Generic",
}

_need_reload = "ops" in locals()

if _need_reload:
    import importlib

    cmglobals = importlib.reload(cmglobals)
    logger = importlib.reload(logger)
    cache = importlib.reload(cache)
    models = importlib.reload(models)
    prefs = importlib.reload(prefs)
    propsdata = importlib.reload(propsdata)
    props = importlib.reload(props)
    opsdata = importlib.reload(opsdata)
    ops = importlib.reload(ops)
    ui = importlib.reload(ui)


def register():
    prefs.register()
    props.register()
    propsdata.register()
    ops.register()
    ui.register()
    logg.info("Registered cache-manager")


def unregister():
    ui.unregister()
    ops.unregister()
    propsdata.unregister()
    props.unregister()
    prefs.unregister()


if __name__ == "__main__":
    register()
