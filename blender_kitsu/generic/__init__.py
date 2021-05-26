import importlib
from blender_kitsu.generic import ops


# ---------REGISTER ----------


def reload():
    global ops

    ops = importlib.reload(ops)


def register():
    ops.register()


def unregister():
    ops.unregister()
