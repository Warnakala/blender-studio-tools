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

from render_review import (
    util,
    props,
    kitsu,
    opsdata,
    checksqe,
    ops,
    ui,
    prefs,
    draw,
)
from render_review.log import LoggerFactory

logger = LoggerFactory.getLogger(__name__)

bl_info = {
    "name": "Render Review",
    "author": "Paul Golter",
    "description": "Addon to review renders from Flamenco with the Sequence Editor",
    "blender": (3, 0, 0),
    "version": (0, 1, 0),
    "location": "Sequence Editor",
    "warning": "",
    "doc_url": "",
    "tracker_url": "",
    "category": "Generic",
}

_need_reload = "ops" in locals()


if _need_reload:
    import importlib

    util = importlib.reload(util)
    props = importlib.reload(props)
    prefs = importlib.reload(prefs)
    kitsu = importlib.reload(kitsu)
    opsdata = importlib.reload(opsdata)
    checksqe = importlib.reload(checksqe)
    ops = importlib.reload(ops)
    ui = importlib.reload(ui)
    draw = importlib.reload(draw)

def register():
    props.register()
    prefs.register()
    ops.register()
    ui.register()
    draw.register()
    logger.info("Registered render-review")


def unregister():
    draw.unregister()
    ui.unregister()
    ops.unregister()
    prefs.unregister()
    props.unregister()


if __name__ == "__main__":
    register()
