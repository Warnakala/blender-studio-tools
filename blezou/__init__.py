import bpy

from . import props
from . import prefs
from . import ops
from . import ui

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

_need_reload = "operators" in locals()
if _need_reload:
    # TODO: never gets executed, _need_reload seems to be false always
    import importlib

    print("RELAODING BELZOU")
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