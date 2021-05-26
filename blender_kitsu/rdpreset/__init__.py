import importlib
from blender_kitsu.rdpreset import ops
from blender_kitsu.rdpreset import ui
from blender_kitsu.rdpreset import opsdata


# ---------REGISTER ----------


def reload():
    global opsdata
    global ops
    global ui

    opsdata = importlib.reload(opsdata)
    ops = importlib.reload(ops)
    ui = importlib.reload(ui)


def register():
    ops.register()
    ui.register()


def unregister():
    ops.unregister()
    ui.unregister()
