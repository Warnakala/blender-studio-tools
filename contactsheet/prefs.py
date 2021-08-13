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

import os
import bpy
from pathlib import Path
from typing import Optional, Dict, List, Set, Any

import bpy


def addon_prefs_get(context: bpy.types.Context) -> bpy.types.AddonPreferences:
    """
    Shortcut to get addon preferences.
    """
    return context.preferences.addons["contactsheet"].preferences


class CS_AddonPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    contactsheet_dir: bpy.props.StringProperty(  # type: ignore
        name="Contactsheet Output Directory",
        description="The contactsheet scene will use this directory to compose the output filepath",
        default="",
        subtype="DIR_PATH",
    )

    contactsheet_scale_factor: bpy.props.FloatProperty(
        name="Contactsheet Scale Factor",
        description="This value controls how much space there is between the individual cells of the contactsheet",
        min=0.1,
        max=1.0,
        step=5,
        default=0.9,
    )

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        box = layout.box()
        box.label(text="Filepaths", icon="FILEBROWSER")

        # contactsheet settings
        box.row().prop(self, "contactsheet_dir")
        box.row().prop(self, "contactsheet_scale_factor")

    @property
    def contactsheet_dir_path(self) -> Optional[Path]:
        if not self.is_contactsheet_dir_valid:
            return None
        return Path(os.path.abspath(bpy.path.abspath(self.contactsheet_dir)))

    @property
    def is_contactsheet_dir_valid(self) -> bool:

        # check if file is saved
        if not self.contactsheet_dir:
            return False

        if not bpy.data.filepath and self.contactsheet_dir.startswith("//"):
            return False

        return True


# ---------REGISTER ----------

classes = [CS_AddonPreferences]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
