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
        name="Absolute Path",
        description="Absolute file path",
        subtype='FILE_PATH',
        get = make_getter_func('path_str', ""),
        set = make_setter_func_readonly('path_str')
    )
    status: EnumProperty(
        name="Status",
        items = [   # Based on PySVN/svn/constants.py/STATUS_TYPE_LOOKUP.
            ('added', 'Added', 'This file was added to the local repository, and will be added to the remote repository when committing', 'FILE', 0),
            ('conflicted', 'Conflict', 'This file was modified locally, and a newer version has appeared on the remote repository at the same time. To resolve the conflict, one of the changes must be discarded', 'ERROR', 1),
            ('deleted', 'Deleted', 'This file was deleted locally, but still exists on the remote repository', 'TRASH', 2),
            ('external', 'External', 'This file is present because of an externals definition', 'EXTERNAL_DRIVE', 3),
            ('ignored', 'Ignored', 'This file is being ignored (e.g., with the svn:ignore property)', 'RADIOBUT_OFF', 4),
            ('incomplete', 'Incomplete', 'A directory is incomplete (a checkout or update was interrupted)', 'FOLDER_REDIRECT', 5),
            ('merged', 'Merged', 'TODO', 'AUTOMERGE_ON', 6),
            ('missing', 'Missing', 'This file is missing (e.g., you moved or deleted it without using svn)', 'FILE_HIDDEN', 7),
            ('modified', 'Modified', 'This file was modified locally, and can be pushed to the remote repository without a conflict', 'MODIFIER', 8),
            ('none', 'Outdated', 'There is a newer version of this file available on the remote repository. You should update it', 'TIME',  9),
            ('normal', 'Normal', 'This file is in the repository. There are no local modifications to commit', 'CHECKMARK', 10),
            ('obstructed', 'Obstructed', 'Something has gone horribly wrong. Try svn cleanup', 'ERROR', 11),
            ('replaced', 'Replaced', 'This file has been replaced in your local repository. This means the file was scheduled for deletion, and then a new file with the same name was scheduled for addition in its place', 'FILE_REFRESH', 12),
            ('unversioned', 'Unversioned', 'This file is new in file system, but not yet added to the local repository. It needs to be added before it can be committed to the remote repository', 'FILE_NEW', 13),
            # A custom status for files that have a newer version available.
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
    is_referenced: BoolProperty(
        name="Is Referenced",
        description="True when this file is referenced by this .blend file either directly or indirectly. Flag used for list filtering",
        default=False
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
