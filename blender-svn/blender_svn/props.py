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
from bpy.props import StringProperty, EnumProperty, IntProperty, BoolProperty

from .util import get_addon_prefs, make_getter_func, make_setter_func_readonly

class SVN_file(bpy.types.PropertyGroup):
    """Property Group that can represent a version of a File in an SVN repository."""

    lock: BoolProperty(
        name = "Lock Editing",
        description = "Flag used to keep the properties read-only without graying them out in the UI. Purely for aesthetic purpose",
        default = False
    )
    name: StringProperty(
        name = "File Name",
        get = make_getter_func('name', ""),
        set = make_setter_func_readonly('name')
    )
    path_str: StringProperty(
        name="File Path",
        description="Absolute file path",
        subtype='FILE_PATH',
        get = make_getter_func('path_str', ""),
        set = make_setter_func_readonly('path_str')
    )
    status: EnumProperty(
        name="Status",
        items = [   # Based on PySVN/svn/constants.py/STATUS_TYPE_LOOKUP.
            ('added', 'New', 'This file was added to the local repository, and will be added to the remote repository when committing'),
            ('conflicted', 'Conflict', 'This file was modified locally, and a newer version has appeared on the remote repository at the same time. One of the changes will be lost'),
            ('deleted', 'Deleted', 'This file was deleted locally, but still exists on the remote repository'),
            ('external', 'External', 'TODO'),
            ('ignored', 'Ignored', 'TODO'),
            ('incomplete', 'Incomplete', 'TODO'),
            ('merged', 'Merged', 'TODO'),
            ('missing', 'Missing', 'TODO'),
            ('modified', 'Modified', 'This file was modified locally, and can be pushed to the remote repository without a conflict'),
            ('none', 'None', 'TODO'),
            ('normal', 'Normal', 'TODO'),
            ('obstructed', 'Obstructed', 'TODO'),
            ('replaced', 'Replaced', 'TODO'),
            ('unversioned', 'Unversioned', 'This file is new in file system, but not yet added to the local repository. It needs to be added before it can be pushed to the remote repository'),
        ]
        ,default='normal',
        get = make_getter_func('status', 10),
        set = make_setter_func_readonly('status')
    )
    revision: IntProperty(
        name="Revision",
        description="Revision number",
        get = make_getter_func('revision', 0),
        set = make_setter_func_readonly('revision')
    )

    @property
    def path(self) -> Optional[Path]:
        if not self.path_str:
            return None
        return Path(self.path_str)
    
    @property
    def svn_relative_path(self) -> str:
        prefs = get_addon_prefs(bpy.context)
        return self.path_str.replace(prefs.svn_directory, "")[1:]


class SVN_scene_properties(bpy.types.PropertyGroup):
    """
    Scene Properties for SVN
    """

    external_files: bpy.props.CollectionProperty(type=SVN_file)  # type: ignore
    external_files_active_index: bpy.props.IntProperty()

# ----------------REGISTER--------------.

registry = [
    SVN_file,
    SVN_scene_properties
]

def register() -> None:
    # Scene Properties.
    bpy.types.Scene.svn = bpy.props.PointerProperty(type=SVN_scene_properties)


def unregister() -> None:
    del bpy.types.Scene.svn
