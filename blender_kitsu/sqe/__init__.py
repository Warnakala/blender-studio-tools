import importlib
from blender_kitsu.sqe import opsdata, checkstrip, pull, push, ops, ui


# ---------REGISTER ----------


def reload():
    global opsdata
    global checkstrip
    global pull
    global push
    global ops
    global ui

    opsdata = importlib.reload(opsdata)
    checkstrip = importlib.reload(checkstrip)
    pull = importlib.reload(pull)
    push = importlib.reload(push)
    ops = importlib.reload(ops)
    ui = importlib.reload(ui)


def register():
    ops.register()
    ui.register()


def unregister():
    ui.unregister()
    ops.unregister()
