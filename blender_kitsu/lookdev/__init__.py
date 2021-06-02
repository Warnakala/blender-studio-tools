import importlib
from blender_kitsu.lookdev import prefs
from blender_kitsu.lookdev import props
from blender_kitsu.lookdev import opsdata
from blender_kitsu.lookdev import ops
from blender_kitsu.lookdev import ui


# ---------REGISTER ----------


def reload():
    global prefs
    global props
    global opsdata
    global ops
    global ui

    prefs = importlib.reload(prefs)
    props = importlib.reload(props)
    opsdata = importlib.reload(opsdata)
    ops = importlib.reload(ops)
    ui = importlib.reload(ui)


def register():
    prefs.register()
    props.register()
    ops.register()
    ui.register()


def unregister():
    ops.unregister()
    ui.unregister()
    props.unregister()
    prefs.unregister()
