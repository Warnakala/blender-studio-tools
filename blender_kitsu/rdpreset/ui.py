from pathlib import Path

import bpy

from blender_kitsu import prefs, rdpreset
from blender_kitsu.rdpreset.ops import KITSU_OT_rdpreset_set_file


class KITSU_PT_vi3d_general_tools(bpy.types.Panel):
    """
    Panel in 3dview that exposes a set of tools that are useful for general tasks
    """

    bl_category = "Kitsu"
    bl_label = "General Tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"DEFAULT_CLOSED"}
    bl_order = 30

    def draw(self, context: bpy.types.Context) -> None:
        addon_prefs = prefs.addon_prefs_get(context)
        layout = self.layout

        box = layout.box()
        box.label(text="Render Settings", icon="RESTRICT_RENDER_OFF")

        # render settings
        row = box.row()
        rdpreset_text = "Select Render Preset"
        if context.scene.kitsu.rd_settings_file:
            rdpreset_text = Path(context.scene.kitsu.rd_settings_file).name
        row.operator(
            KITSU_OT_rdpreset_set_file.bl_idname,
            text=rdpreset_text,
            icon="DOWNARROW_HLT",
        )


# ---------REGISTER ----------

classes = [KITSU_PT_vi3d_general_tools]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
