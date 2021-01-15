# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# <pep8 compliant>
import bpy

import pathlib

from shot_builder.project import is_valid_production_root
from shot_builder.connectors.kitsu import KitsuPreferences


class ShotBuilderPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    production_path: bpy.props.StringProperty(  # type: ignore
        name="Production Root",
        description="The location to load configuration files from when "
        "they couldn't be found in any parent folder of the current "
        "file. Folder must contain a sub-folder named `shot-builder` "
        "that holds the configuration files",
        subtype='DIR_PATH',
    )

    kitsu: bpy.props.PointerProperty(  # type: ignore
        name="Kitsu Preferences",
        type=KitsuPreferences
    )

    def draw(self, context: bpy.types.Context):
        layout = self.layout

        is_valid = is_valid_production_root(pathlib.Path(self.production_path))
        layout.prop(self, "production_path",
                    icon='NONE' if is_valid else 'ERROR')
        if not is_valid:
            layout.label(text="Folder must contain a sub-folder named "
                              "`shot-builder` that holds the configuration "
                              "files.",
                         icon="ERROR")
        sublayout = layout.box()
        self.kitsu.draw(sublayout, context)
