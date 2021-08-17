import bpy

from . import asglobals
from . import prefs
from . import kitsu
from . import props
from . import opsdata
from . import ops
from . import ui
from .log import LoggerFactory

logger = LoggerFactory.getLogger(__name__)

bl_info = {
    "name": "Anim Setup",
    "author": "Paul Golter",
    "description": "Blender addon to setup animation scenes for the spritefright project",
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

    asglobals = importlib.reload(asglobals)
    prefs = importlib.reload(prefs)
    kitsu = importlib.reload(kitsu)
    props = importlib.reload(props)
    opsdata = importlib.reload(opsdata)
    ops = importlib.reload(ops)
    ui = importlib.reload(ui)


def register():
    prefs.register()
    props.register()
    ops.register()
    ui.register()
    logger.info("Registered anim-setup")


def unregister():
    ui.unregister()
    ops.unregister()
    props.unregister()
    prefs.unregister()


if __name__ == "__main__":
    register()
