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

import bpy

from contactsheet import (
    prefs,
    props,
    opsdata,
    ops,
    ui,
    geo,
    geo_seq,
)
from contactsheet.log import LoggerFactory

logger = LoggerFactory.getLogger(__name__)

bl_info = {
    "name": "Contactsheet",
    "author": "Paul Golter",
    "description": "Blender addon to create a contactsheet from sequence editor strips",
    "blender": (3, 0, 0),
    "version": (0, 1, 1),
    "location": "Sequence Editor",
    "category": "Sequencer",
}

_need_reload = "ops" in locals()

if _need_reload:
    import importlib

    geo_seq = importlib.reload(geo_seq)
    geo = importlib.reload(geo)
    props = importlib.reload(props)
    prefs = importlib.reload(prefs)
    opsdata = importlib.reload(opsdata)
    ops = importlib.reload(ops)
    ui = importlib.reload(ui)


def register():
    props.register()
    prefs.register()
    ops.register()
    ui.register()


def unregister():
    ui.unregister()
    ops.unregister()
    prefs.unregister()
    props.unregister()


if __name__ == "__main__":
    register()
