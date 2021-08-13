# ***** BEGIN GPL LICENSE BLOCK *****
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
# ***** END GPL LICENCE BLOCK *****
#
# (c) 2021, Blender Foundation - Paul Golter

from typing import Set, Union, Optional, List, Dict, Any

import bpy

from contactsheet.ops import (
    CS_OT_make_contactsheet,
    CS_OT_exit_contactsheet,
)
from contactsheet import opsdata


class CS_PT_contactsheet(bpy.types.Panel):
    """ """

    bl_category = "Contactsheet"
    bl_label = "Contactsheet"
    bl_space_type = "SEQUENCE_EDITOR"
    bl_region_type = "UI"
    bl_order = 10

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        # return opsdata.poll_make_contactsheet(context)
        return True

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout

        # Handle case if scene is contactsheet.
        if context.scene.contactsheet.is_contactsheet:
            # Exit contact sheet.
            row = layout.row(align=True)
            row.operator(CS_OT_exit_contactsheet.bl_idname, icon="X")
            return

        # Make contact sheet.
        row = layout.row(align=True)

        sequences = context.selected_sequences
        if not sequences:
            valid_sequences = opsdata.get_top_level_valid_strips_continuous(context)
        else:
            valid_sequences = opsdata.get_valid_cs_sequences(sequences)

        text = f"Make Contactsheet with {len(valid_sequences)} strips"

        row.operator(CS_OT_make_contactsheet.bl_idname, icon="MESH_GRID", text=text)
        icon = "UNLOCKED" if context.scene.contactsheet.use_custom_rows else "LOCKED"
        row.prop(context.scene.contactsheet, "use_custom_rows", text="", icon=icon)

        if context.scene.contactsheet.use_custom_rows:
            layout.row(align=True).prop(context.scene.contactsheet, "rows")

        # contact sheet resolution
        row = layout.row(align=True)
        row.prop(context.scene.contactsheet, "contactsheet_x", text="X")
        row.prop(context.scene.contactsheet, "contactsheet_y", text="Y")


# ----------------REGISTER--------------

classes = [
    CS_PT_contactsheet,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
