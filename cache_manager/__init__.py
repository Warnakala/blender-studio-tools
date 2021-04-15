import bpy
from . import cmglobals
from . import blend
from . import prefs
from . import props
from . import opsdata
from . import ops
from . import ui
from .logger import LoggerFactory

logger = LoggerFactory.getLogger(__name__)

bl_info = {
    "name": "Cache Manager",
    "author": "Paul Golter",
    "description": "Blender addon to streamline alembic caches of assets",
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

    logger.info("-START- Reloading Cache Manager")
    cmglobals = importlib.reload(cmglobals)
    blend = importlib.reload(blend)
    prefs = importlib.reload(prefs)
    props = importlib.reload(props)
    opsdata = importlib.reload(opsdata)
    ops = importlib.reload(ops)
    ui = importlib.reload(ui)
    logger.info("-END- Reloading Cache Manager")


def register():
    logger.info("-START- Registering Cache Manager")
    prefs.register()
    props.register()
    ops.register()
    ui.register()
    logger.info("-END- Registering Cache Manager")


def unregister():
    logger.info("-START- Unregistering Cache Manager")
    ui.unregister()
    ops.unregister()
    props.unregister()
    prefs.unregister()
    logger.info("-END- Unregistering Cache Manager")


if __name__ == "__main__":
    register()
