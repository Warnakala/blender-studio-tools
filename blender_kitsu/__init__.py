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
from . import ops_generic_data
from . import ops_generic
from . import ops_auth
from . import ops_context_data
from . import ops_context
from . import ops_anim_data
from . import ops_anim
from . import ops_sqe_data
from . import ops_sqe
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

_need_reload = "props" in locals()

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
    ops_generic_data = importlib.reload(ops_generic_data)
    ops_generic = importlib.reload(ops_generic)
    ops_auth = importlib.reload(ops_auth)
    ops_context_data = importlib.reload(ops_context_data)
    ops_context = importlib.reload(ops_context)
    ops_anim_data = importlib.reload(ops_anim_data)
    ops_anim = importlib.reload(ops_anim)
    ops_sqe_data = importlib.reload(ops_sqe_data)
    ops_sqe = importlib.reload(ops_sqe)
    ui = importlib.reload(ui)
    ZLoggerLevelManager.configure_levels()
    logger.info("-END- Reloading blender-kitsu")


def register():
    logger.info("-START- Registering blender-kitsu")
    cache.register()
    props.register()
    prefs.register()
    ops_generic.register()
    ops_auth.register()
    ops_context.register()
    ops_anim.register()
    ops_sqe.register()
    ui.register()
    ZLoggerLevelManager.configure_levels()
    logger.info("-END- Registering blender-kitsu")


def unregister():
    logger.info("-START- Unregistering blender-kitsu")
    ui.unregister()
    ops_sqe.unregister()
    ops_anim.unregister()
    ops_context.unregister()
    ops_auth.unregister()
    ops_generic.unregister()
    prefs.unregister()
    props.unregister()
    cache.unregister()
    ZLoggerLevelManager.restore_levels()
    logger.info("-END- Unregistering blender-kitsu")


if __name__ == "__main__":
    register()
