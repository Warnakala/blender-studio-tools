from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple, Any

import bpy


from blender_kitsu.logger import ZLoggerFactory
from blender_kitsu import prefs
from blender_kitsu import ops_generic_data
from blender_kitsu.rdpreset import opsdata

logger = ZLoggerFactory.getLogger(name=__name__)


class KITSU_OT_rdpreset_set_file(bpy.types.Operator):
    """"""

    bl_idname = "kitsu.rdpreset_set_file"
    bl_label = "Render Preset"
    bl_property = "files"

    files: bpy.props.EnumProperty(items=opsdata.get_rd_settings_enum_list, name="Files")

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        addon_prefs = prefs.addon_prefs_get(context)
        return addon_prefs.is_rd_settings_dir_valid

    def execute(self, context: bpy.types.Context) -> Set[str]:
        file = self.files

        if not file:
            return {"CANCELLED"}

        if context.scene.kitsu.rd_settings_file == file:
            return {"CANCELLED"}

        # update global scene cache version prop
        context.scene.kitsu.rd_settings_file = file
        logger.info("Set render settings file to %s", file)

        # redraw ui
        ops_generic_data.ui_redraw()

        return {"FINISHED"}

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> Set[str]:
        context.window_manager.invoke_search_popup(self)  # type: ignore
        return {"FINISHED"}


# ---------REGISTER ----------

classes = [
    KITSU_OT_rdpreset_set_file,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
