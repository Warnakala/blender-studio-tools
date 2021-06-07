import bpy
from blender_kitsu import (
    lookdev,
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
    tasks,
    ui,
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

    lookdev.reload()
    bkglobals = importlib.reload(bkglobals)
    cache = importlib.reload(cache)
    types = importlib.reload(types)
    models = importlib.reload(models)
    propsdata = importlib.reload(propsdata)
    props = importlib.reload(props)
    prefs = importlib.reload(prefs)
    ui = importlib.reload(ui)
    sqe.reload()
    util = importlib.reload(util)
    generic.reload()
    auth.reload()
    context.reload()
    tasks.reload()
    anim.reload()

    LoggerLevelManager.configure_levels()
    logger.info("-END- Reloading blender-kitsu")


def register():
    logger.info("-START- Registering blender-kitsu")

    lookdev.register()
    prefs.register()
    cache.register()
    props.register()
    sqe.register()
    generic.register()
    auth.register()
    context.register()
    # tasks.register()
    anim.register()

    LoggerLevelManager.configure_levels()
    logger.info("-END- Registering blender-kitsu")


def unregister():
    logger.info("-START- Unregistering blender-kitsu")

    anim.unregister()
    # tasks.unregister()
    context.unregister()
    auth.unregister()
    generic.unregister()
    sqe.unregister()
    props.unregister()
    cache.unregister()
    prefs.unregister()
    lookdev.unregister()

    LoggerLevelManager.restore_levels()
    logger.info("-END- Unregistering blender-kitsu")


if __name__ == "__main__":
    register()
