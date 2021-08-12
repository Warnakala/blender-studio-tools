from typing import Set, Union, Optional, List, Dict, Any

import bpy

from contactsheet.ops import (
    RR_OT_make_contactsheet,
    RR_OT_exit_contactsheet,
)
from contactsheet import opsdata, prefs


class RR_PT_contactsheet(bpy.types.Panel):
    """ """

    bl_category = "Contactsheet"
    bl_label = "Contactsheet"
    bl_space_type = "SEQUENCE_EDITOR"
    bl_region_type = "UI"
    bl_order = 10

    def draw(self, context: bpy.types.Context) -> None:

        addon_prefs = prefs.addon_prefs_get(context)

        # Handle special case if scene is contactsheet.
        if context.scene.contactsheet.is_contactsheet:
            layout = self.layout
            box = layout.box()
            box.label(text="Contactsheet", icon="MESH_GRID")

            # Exit contact sheet.
            row = box.row(align=True)
            row.operator(RR_OT_exit_contactsheet.bl_idname, icon="X")
            return

        # Contactsheet tools.
        valid_sequences = opsdata.get_valid_cs_sequences(context)
        if not context.selected_sequences and not valid_sequences:
            return

        # Create box.
        layout = self.layout
        box = layout.box()
        box.label(text="Contactsheet", icon="MESH_GRID")

        # Make contact sheet.
        row = box.row(align=True)

        if not context.selected_sequences:
            valid_sequences = opsdata.get_top_level_valid_strips_continious(context)

        text = f"Make Contactsheet with {len(valid_sequences)} strips"

        row.operator(RR_OT_make_contactsheet.bl_idname, icon="MESH_GRID", text=text)
        icon = "UNLOCKED" if context.scene.contactsheet.use_custom_rows else "LOCKED"
        row.prop(context.scene.contactsheet, "use_custom_rows", text="", icon=icon)

        if context.scene.contactsheet.use_custom_rows:
            box.row(align=True).prop(context.scene.contactsheet, "rows")

        # contact sheet resolution
        row = box.row(align=True)
        row.prop(context.scene.contactsheet, "contactsheet_x", text="X")
        row.prop(context.scene.contactsheet, "contactsheet_y", text="Y")


# ----------------REGISTER--------------

classes = [
    RR_PT_contactsheet,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
