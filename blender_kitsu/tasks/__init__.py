import importlib
from blender_kitsu.tasks import ops, ui


# ---------REGISTER ----------


def reload():
    global ops
    global ui

    ops = importlib.reload(ops)
    ui = importlib.reload(ui)


def register():
    ops.register()
    ui.register()


def unregister():
    ui.unregister()
    ops.unregister()
