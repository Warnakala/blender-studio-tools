import bpy

from render_review import (
    util,
    props,
    kitsu,
    opsdata,
    checksqe,
    ops,
    ui,
    prefs,
    draw,
)
from render_review.log import LoggerFactory

logger = LoggerFactory.getLogger(__name__)

bl_info = {
    "name": "Render Review",
    "author": "Paul Golter",
    "description": "Addon to review renders from Flamenco with the Sequence Editor",
    "blender": (3, 0, 0),
    "version": (0, 1, 0),
    "location": "Sequence Editor",
    "warning": "",
    "doc_url": "",
    "tracker_url": "",
    "category": "Generic",
}

_need_reload = "ops" in locals()


if _need_reload:
    import importlib

    util = importlib.reload(util)
    props = importlib.reload(props)
    prefs = importlib.reload(prefs)
    kitsu = importlib.reload(kitsu)
    opsdata = importlib.reload(opsdata)
    checksqe = importlib.reload(checksqe)
    ops = importlib.reload(ops)
    ui = importlib.reload(ui)
    draw = importlib.reload(draw)
    logger.info("Reloaded render-review")


def register():
    props.register()
    prefs.register()
    ops.register()
    ui.register()
    draw.register()


def unregister():
    draw.unregister()
    ui.unregister()
    ops.unregister()
    prefs.unregister()
    props.unregister()


if __name__ == "__main__":
    register()
