from pathlib import Path
from typing import Dict, List, Set

import bpy

from .log import LoggerFactory


logger = LoggerFactory.getLogger()


def ui_redraw() -> None:
    """
    Forces blender to redraw the UI.
    """
    for screen in bpy.data.screens:
        for area in screen.areas:
            area.tag_redraw()


class AS_OT_do_it(bpy.types.Operator):
    """ """

    bl_idname = "as.do_it"
    bl_label = "Do something"
    bl_options = {"INTERNAL"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return True

    def execute(self, context: bpy.types.Context) -> Set[str]:
        return {"FINISHED"}


# ---------REGISTER ----------

classes = [AS_OT_do_it]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
