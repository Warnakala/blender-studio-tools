import importlib
from blender_kitsu.sqe import opsdata, checkstrip, pull, push, ops


# ---------REGISTER ----------


def reload():
    global opsdata
    global checkstrip
    global pull
    global push
    global ops

    opsdata = importlib.reload(opsdata)
    checkstrip = importlib.reload(checkstrip)
    pull = importlib.reload(pull)
    push = importlib.reload(push)
    ops = importlib.reload(ops)


def register():
    ops.register()


def unregister():
    ops.unregister()
