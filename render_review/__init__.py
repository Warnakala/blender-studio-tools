import bpy

from render_review import props, ops, ui, prefs, draw
from render_review.log import LoggerFactory

logger = LoggerFactory.getLogger(__name__)

bl_info = {
    "name": "Render Review",
    "author": "Paul Golter",
    "description": "Blender addon to review renderings from flamenco",
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

    logger.info("-START- Reloading render-review")

    props = importlib.reload(props)
    prefs = importlib.reload(prefs)
    ops = importlib.reload(ops)
    ui = importlib.reload(ui)
    draw = importlib.reload(draw)

    logger.info("-END- Reloading render-review")


def register():
    logger.info("-START- Registering render-review")

    props.register()
    prefs.register()
    ops.register()
    ui.register()
    draw.register()

    logger.info("-END- Registering render-review")


def unregister():
    logger.info("-START- Unregistering render-review")

    draw.unregister()
    ui.unregister()
    ops.unregister()
    prefs.unregister()
    props.unregister()

    logger.info("-END- Unregistering render-review")


if __name__ == "__main__":
    register()
