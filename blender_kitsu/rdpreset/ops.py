from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple, Any

import bpy


from blender_kitsu.logger import ZLoggerFactory
from blender_kitsu import prefs
from blender_kitsu import ops_generic_data
from blender_kitsu.rdpreset import opsdata

logger = ZLoggerFactory.getLogger(name=__name__)


class RDPRESET_OT_set_preset(bpy.types.Operator):
    """"""

    bl_idname = "rdpreset.set_preset"
    bl_label = "Render Preset"
    bl_property = "files"

    files: bpy.props.EnumProperty(items=opsdata.get_rd_settings_enum_list, name="Files")

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        addon_prefs = prefs.addon_prefs_get(context)
        return addon_prefs.rdpreset.is_presets_dir_valid

    def execute(self, context: bpy.types.Context) -> Set[str]:
        file = self.files

        if not file:
            return {"CANCELLED"}

        if context.scene.rdpreset.preset_file == file:
            return {"CANCELLED"}

        # update global scene cache version prop
        context.scene.rdpreset.preset_file = file
        logger.info("Set render settings file to %s", file)

        # redraw ui
        ops_generic_data.ui_redraw()

        return {"FINISHED"}

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> Set[str]:
        context.window_manager.invoke_search_popup(self)  # type: ignore
        return {"FINISHED"}


class RDPRESET_OT_rdpreset_apply(bpy.types.Operator):
    """"""

    bl_idname = "rdpreset.apply"
    bl_label = "Apply Preset"

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return True
        # return bool(context.scene.kitsu.)

    def execute(self, context: bpy.types.Context) -> Set[str]:
        file = ""

        if not file:
            return {"CANCELLED"}

        if context.scene.rdpreset.preset_file == file:
            return {"CANCELLED"}

        # update global scene cache version prop
        context.scene.rdpreset.preset_file = file
        logger.info("Set render settings file to %s", file)

        # redraw ui
        ops_generic_data.ui_redraw()

        return {"FINISHED"}

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> Set[str]:
        context.window_manager.invoke_search_popup(self)  # type: ignore
        return {"FINISHED"}


# ---------REGISTER ----------

classes = [
    RDPRESET_OT_set_preset,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
