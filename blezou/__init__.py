import bpy

from .logger import ZLoggerFactory
from . import props
from . import prefs
from . import ops
from . import ui

logger = ZLoggerFactory.getLogger(__name__)

bl_info = {
    "name": "Blezou",
    "author": "Paul Golter",
    "description": "Blender addon to interact with gazou data base",
    "blender": (2, 93, 0),
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

    logger.info("RELAODING BELZOU")
    props = importlib.reload(props)
    prefs = importlib.reload(prefs)
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