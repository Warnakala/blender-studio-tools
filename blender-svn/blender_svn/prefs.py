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
from bpy.props import StringProperty, IntProperty, BoolProperty

from . import client

logger = logging.getLogger(name="SVN")


class SVN_addon_preferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    enable_ui: BoolProperty(
        name="Enable UI",
        default=True,
        description="Enable UI in sidebar for debugging/testing"
    )
    is_in_repo: BoolProperty(
        name="is_in_repo",
        default=False,
        description="To store whether the current file was deemed to be in an SVN repository on file save/load. For internal use only"
    )

    # Following properties are not user-editable. They are filled in on file-load,
    # when the loaded file is in an SVN repository. They are used to display
    # info in the sidebar UI.
    svn_directory: StringProperty(
        name="Root Directory",
        default="",
        subtype="DIR_PATH",
        description="Absolute directory path of the SVN repository's root in the file system"
    )
    svn_url: StringProperty(
        name="Remote URL",
        default="",
        description="URL of the remote SVN repository"
    )
    relative_filepath: StringProperty(
        name="Relative Filepath",
        default="",
        description="Path of the currently open .blend file, relative to the SVN root directory"
    )
    revision_number: IntProperty(
        name="Revision Number",
        description="Revision number of the current .blend file"
    )
    revision_date: StringProperty(
        name="Revision Date",
        default="",
        description="Date when the current revision was committed"
    )
    revision_author: StringProperty(
        name="Revision Author",
        default="",
        description="SVN username of the revision author"
    )

    def reset(self):
        self.svn_directory = ""
        self.svn_url = ""
        self.relative_filepath = ""
        self.revision_number = -1
        self.revision_date = ""
        self.revision_author = ""
        self.is_in_repo = False

    @property
    def svn_directory_path(self) -> Optional[Path]:
        if not self.svn_directory:
            return None
        return Path(self.svn_directory)

    def draw(self, context: bpy.types.Context) -> None:
        layout: bpy.types.UILayout = self.layout

        # Production Config Dir.
        row = layout.row(align=True)
        row.prop(self, "enable_ui")


# ----------------REGISTER--------------.

registry = [
    SVN_addon_preferences
]
