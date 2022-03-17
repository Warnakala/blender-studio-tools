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
from typing import Optional, Dict, Any, List, Tuple

from pathlib import Path

import bpy


class SVN_file(bpy.types.PropertyGroup):

    """
    Property Group that can represent a minimal version of a File in a SVN repository.
    """

    path_str: bpy.props.StringProperty(  # type: ignore
        name="Path",
    )

    @property
    def path(self) -> Optional[Path]:
        if not self.path_str:
            return None
        return Path(self.path_str)


class SVN_scene_properties(bpy.types.PropertyGroup):
    """
    Scene Properties for SVN
    """

    external_files: bpy.props.CollectionProperty(type=SVN_file)  # type: ignore


# ----------------REGISTER--------------.

classes = [SVN_file, SVN_scene_properties]


def register() -> None:
    for cls in classes:
        bpy.utils.register_class(cls)

    # Scene Properties.
    bpy.types.Scene.svn = bpy.props.PointerProperty(type=SVN_scene_properties)


def unregister() -> None:
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
