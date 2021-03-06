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

from media_viewer import (
    vars,
    props,
    opsdata,
    ops,
    log,
    shortcuts,
    ui,
    gpu_opsdata,
    gpu_ops,
    draw,
)

from media_viewer.log import LoggerFactory

logger = LoggerFactory.getLogger(__name__)

bl_info = {
    "name": "Media Viewer",
    "author": "Paul Golter",
    "description": (
        "Blender addon that provides additional tools "
        "to make the blender_media_viewer application template more powerful"
    ),
    "blender": (3, 0, 0),
    "version": (0, 1, 0),
    "location": "Sequence Editor",
    "category": "Sequencer",
}

_need_reload = "ops" in locals()

if _need_reload:
    import importlib

    vars = importlib.reload(vars)
    props = importlib.reload(props)
    opsdata = importlib.reload(opsdata)
    log = importlib.reload(log)
    ops = importlib.reload(ops)
    shortcuts = importlib.reload(shortcuts)
    ui = importlib.reload(ui)
    gpu_opsdata = importlib.reload(gpu_opsdata)
    gpu_ops = importlib.reload(gpu_ops)
    draw = importlib.reload(draw)


def register():
    props.register()
    ops.register()
    shortcuts.register()
    # gpu_opsdata.register()
    gpu_ops.register()
    ui.register()
    draw.register()


def unregister():
    draw.unregister()
    ui.unregister()
    ops.unregister()
    gpu_ops.unregister()
    # gpu_opsdata.unregister()
    shortcuts.unregister()
    props.unregister()


if __name__ == "__main__":
    register()
