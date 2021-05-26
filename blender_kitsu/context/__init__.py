import importlib
from blender_kitsu.context import opsdata, ops, ui


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
    ui.unregister()
    ops.unregister()
