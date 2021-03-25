import bpy

from . import bz_props
from . import bz_prefs
from . import bz_ops
from . import bz_ui

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


def register():
    bz_props.register()
    bz_prefs.register()
    bz_ops.register()
    bz_ui.register()


def unregister():
    bz_ui.unregister()
    bz_ops.unregister()
    bz_prefs.unregister()
    bz_props.unregister()


if __name__ == "__main__":
    register()