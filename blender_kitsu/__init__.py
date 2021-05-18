import bpy

from . import bkglobals
from . import types
from . import cache
from . import checkstrip
from . import pull
from . import push
from . import models
from . import propsdata
from . import props
from . import prefs
from . import opsdata
from . import ops
from . import ui
from .logger import ZLoggerFactory, ZLoggerLevelManager

logger = ZLoggerFactory.getLogger(__name__)

bl_info = {
    "name": "Blender Kitsu",
    "author": "Paul Golter",
    "description": "Blender addon to interact with Kitsu",
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

    logger.info("-START- Reloading blender-kitsu")
    bkglobals = importlib.reload(bkglobals)
    cache = importlib.reload(cache)
    types = importlib.reload(types)
    checkstrip = importlib.reload(checkstrip)
    pull = importlib.reload(pull)
    push = importlib.reload(push)
    models = importlib.reload(models)
    propsdata = importlib.reload(propsdata)
    props = importlib.reload(props)
    prefs = importlib.reload(prefs)
    opsdata = importlib.reload(opsdata)
    ops = importlib.reload(ops)
    ui = importlib.reload(ui)
    ZLoggerLevelManager.configure_levels()
    logger.info("-END- Reloading blender-kitsu")


def register():
    logger.info("-START- Registering blender-kitsu")
    cache.register()
    props.register()
    prefs.register()
    opsdata.register()
    ops.register()
    ui.register()
    ZLoggerLevelManager.configure_levels()
    logger.info("-END- Registering blender-kitsu")


def unregister():
    logger.info("-START- Unregistering blender-kitsu")
    ui.unregister()
    ops.unregister()
    opsdata.unregister()
    prefs.unregister()
    props.unregister()
    cache.unregister()
    ZLoggerLevelManager.restore_levels()
    logger.info("-END- Unregistering blender-kitsu")


if __name__ == "__main__":
    register()
