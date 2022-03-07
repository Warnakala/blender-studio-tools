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
import logging
from typing import Optional, Any, Set, Tuple, List
from pathlib import Path

import bpy


logger = logging.getLogger(name="SVN")


class SVN_addon_preferences(bpy.types.AddonPreferences):

    bl_idname = __package__

    svn_directory: bpy.props.StringProperty(  # type: ignore
        name="SVN Directory",
        default="",
        subtype="DIR_PATH",
    )

    @property
    def svn_directory_path(self) -> Optional[Path]:
        if not self.svn_directory:
            return None
        return Path(self.svn_directory)

    def draw(self, context: bpy.types.Context) -> None:
        layout: bpy.types.UILayout = self.layout

        # Production Config Dir.
        row = layout.row(align=True)
        row.prop(self, "svn_directory")


# ----------------REGISTER--------------.

classes = [SVN_addon_preferences]


def register() -> None:
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
