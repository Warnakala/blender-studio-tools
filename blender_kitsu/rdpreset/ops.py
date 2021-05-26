import importlib.util

from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple, Any

import bpy


from blender_kitsu.logger import LoggerFactory
from blender_kitsu import prefs, util
from blender_kitsu.rdpreset import opsdata

logger = LoggerFactory.getLogger(name=__name__)


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
        logger.info("Set render preset file to %s", file)

        # redraw ui
        util.ui_redraw()

        return {"FINISHED"}

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> Set[str]:
        context.window_manager.invoke_search_popup(self)  # type: ignore
        return {"FINISHED"}


class RDPRESET_OT_rdpreset_apply(bpy.types.Operator):
    """"""

    bl_idname = "rdpreset.apply"
    bl_label = "Apply Preset"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return bool(context.scene.rdpreset.preset_file)

    def execute(self, context: bpy.types.Context) -> Set[str]:
        preset_file = context.scene.rdpreset.preset_file
        preset_path = Path(preset_file).absolute()

        if not preset_file:
            return {"CANCELLED"}

        # load module
        spec = importlib.util.spec_from_file_location(
            preset_path.name, preset_path.as_posix()
        )

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # exec module main function
        if "main" not in dir(module):
            self.report(
                {"ERROR"}, f"{preset_path.name} does not contain a 'main' function"
            )
            return {"CANCELLED"}

        module.main()
        self.report({"INFO"}, f"Applied: {preset_path.name}")

        return {"FINISHED"}


# ---------REGISTER ----------

classes = [RDPRESET_OT_set_preset, RDPRESET_OT_rdpreset_apply]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
