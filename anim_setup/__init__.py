import bpy

from . import prefs
from . import opsdata
from . import ops
from . import ui
from .log import LoggerFactory

logger = LoggerFactory.getLogger(__name__)

bl_info = {
    "name": "Anim Setup",
    "author": "Paul Golter",
    "description": "Blender addon to quickl setup animation scenes for the spritefright project",
    "blender": (3, 0, 0),
    "version": (0, 1, 0),
    "location": "View3D",
    "warning": "",
    "doc_url": "",
    "tracker_url": "",
    "category": "Generic",
}

_need_reload = "ops" in locals()

if _need_reload:
    import importlib

    logger.info("-START- Reloading anim-setup")
    prefs = importlib.reload(prefs)
    opsdata = importlib.reload(opsdata)
    ops = importlib.reload(ops)
    ui = importlib.reload(ui)
    logger.info("-END- Reloading anim-setup")


def register():
    logger.info("-START- Registering anim-setup")
    prefs.register()
    ops.register()
    ui.register()
    logger.info("-END- Registering anim-setup")


def unregister():
    logger.info("-START- Unregistering anim-setup")
    ui.unregister()
    ops.unregister()
    prefs.unregister()
    logger.info("-END- Unregistering anim-setup")


if __name__ == "__main__":
    register()
