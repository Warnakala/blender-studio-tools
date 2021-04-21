import bpy
from . import logger
from . import cache
from . import cmglobals
from . import blend
from . import prefsdata
from . import prefs
from . import props
from . import opsdata
from . import ops
from . import ui

logg = logger.LoggerFactory.getLogger(__name__)

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

    logg.info("-START- Reloading Cache Manager")
    logger = importlib.reload(logger)
    cache = importlib.reload(cache)
    cmglobals = importlib.reload(cmglobals)
    blend = importlib.reload(blend)
    prefsdata = importlib.reload(prefsdata)
    prefs = importlib.reload(prefs)
    props = importlib.reload(props)
    opsdata = importlib.reload(opsdata)
    ops = importlib.reload(ops)
    ui = importlib.reload(ui)
    logg.info("-END- Reloading Cache Manager")


def register():
    logg.info("-START- Registering Cache Manager")
    prefs.register()
    props.register()
    ops.register()
    ui.register()
    logg.info("-END- Registering Cache Manager")


def unregister():
    logg.info("-START- Unregistering Cache Manager")
    ui.unregister()
    ops.unregister()
    props.unregister()
    prefs.unregister()
    logg.info("-END- Unregistering Cache Manager")


if __name__ == "__main__":
    register()
