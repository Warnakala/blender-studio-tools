import bpy
from blender_kitsu import (
    rdpreset,
    bkglobals,
    types,
    cache,
    models,
    propsdata,
    props,
    prefs,
    sqe,
    util,
    generic,
    auth,
    context,
    anim,
)

from blender_kitsu.logger import LoggerFactory, LoggerLevelManager

logger = LoggerFactory.getLogger(__name__)

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

    rdpreset.reload()
    bkglobals = importlib.reload(bkglobals)
    cache = importlib.reload(cache)
    types = importlib.reload(types)
    models = importlib.reload(models)
    propsdata = importlib.reload(propsdata)
    props = importlib.reload(props)
    prefs = importlib.reload(prefs)
    sqe.reload()
    util = importlib.reload(util)
    generic.reload()
    auth.reload()
    context.reload()
    anim.reload()

    LoggerLevelManager.configure_levels()
    logger.info("-END- Reloading blender-kitsu")


def register():
    logger.info("-START- Registering blender-kitsu")

    rdpreset.register()
    prefs.register()
    cache.register()
    props.register()
    sqe.register()
    generic.register()
    auth.register()
    context.register()
    anim.register()

    LoggerLevelManager.configure_levels()
    logger.info("-END- Registering blender-kitsu")


def unregister():
    logger.info("-START- Unregistering blender-kitsu")

    anim.unregister()
    context.unregister()
    auth.unregister()
    generic.unregister()
    sqe.unregister()
    props.unregister()
    cache.unregister()
    prefs.unregister()
    rdpreset.unregister()

    LoggerLevelManager.restore_levels()
    logger.info("-END- Unregistering blender-kitsu")


if __name__ == "__main__":
    register()
