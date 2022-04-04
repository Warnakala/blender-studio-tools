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
# (c) 2022, Blender Foundation - Demeter Dzadik

import logging
from typing import Optional, Any, Set, Tuple, List
from pathlib import Path

import bpy
from bpy.props import StringProperty, IntProperty, BoolProperty

from .util import make_getter_func, make_setter_func_readonly

logger = logging.getLogger(name="SVN")


def get_visible_indicies(context) -> List[int]:
    svn_prop = context.scene.svn
    flt_flags, _flt_neworder = bpy.types.SVN_UL_file_list.cls_filter_items(context, svn_prop, 'external_files')

    visible_indicies = [i for i, flag in enumerate(flt_flags) if flag != 0]
    return visible_indicies


def force_good_active_index(context) -> bool:
    """If the active element is being filtered out, set the active element to 
    something that is visible.
    Return False if no elements are visible.
    """
    svn_prop = context.scene.svn
    visible_indicies = get_visible_indicies(context)
    if len(visible_indicies) == 0:
        svn_prop.external_files_active_index = 0
        return False
    if svn_prop.external_files_active_index not in visible_indicies:
        svn_prop.external_files_active_index = visible_indicies[0]

    return True

class SVN_addon_preferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    enable_ui: BoolProperty(
        name="Enable UI",
        default=True,
        description="Enable UI in sidebar for debugging/testing",
    )
    is_in_repo: BoolProperty(
        name="is_in_repo",
        default=False,
        description="To store whether the current file was deemed to be in an SVN repository on file save/load. For internal use only"
    )

    def update_filters(dummy, context):
        """Should run when any of the SVN file list search filters are changed."""
        force_good_active_index(context)

    ### SVN Search filter properties.
    # These are normally stored on the UIList, but then they cannot be accessed
    # from anywhere else, since template_list() does not return the UIList instance.
    # We need to be able to access them to be able to tell which entries are 
    # visible, outside of the drawing code, for ensuring that a filtered out 
    # entry can never be the active one.
    # This is important in this case to avoid user confusion.
    include_normal: BoolProperty(
        name = "Show Normal Files",
        description = "Include files whose SVN status is Normal",
        default = False,
        update = update_filters
    )
    only_referenced_files: BoolProperty(
        name = "Only Referenced Files",
        description = "Only show modified files referenced by this .blend file, rather than the entire repository",
        default = False,
        update = update_filters
    )
    search_filter: StringProperty(
        name = "Search Filter",
        description = "Only show entries that contain this string",
        update = update_filters
    )

    # Following properties are not user-editable. They are filled in on file-load,
    # when the loaded file is in an SVN repository. They are used to display
    # info in the sidebar UI.
    svn_directory: StringProperty(
        name="Root Directory",
        default="",
        subtype="DIR_PATH",
        description="Absolute directory path of the SVN repository's root in the file system",
        get = make_getter_func("svn_directory", ""),
        set = make_setter_func_readonly("svn_directory")
    )
    svn_url: StringProperty(
        name="Remote URL",
        default="",
        description="URL of the remote SVN repository",
        get = make_getter_func("svn_url", ""),
        set = make_setter_func_readonly("svn_url")
    )
    relative_filepath: StringProperty(
        name="Relative Filepath",
        default="",
        description="Path of the currently open .blend file, relative to the SVN root directory",
        get = make_getter_func("relative_filepath", ""),
        set = make_setter_func_readonly("relative_filepath")
    )
    revision_number: IntProperty(
        name="Revision Number",
        description="Revision number of the current .blend file",
        get = make_getter_func("revision_number", 0),
        set = make_setter_func_readonly("revision_number")
    )
    revision_date: StringProperty(
        name="Revision Date",
        description="Date when the current revision was committed",
        get = make_getter_func("revision_date", ""),
        set = make_setter_func_readonly("revision_date")
    )
    revision_author: StringProperty(
        name="Revision Author",
        description="SVN username of the revision author",
        get = make_getter_func("revision_author", ""),
        set = make_setter_func_readonly("revision_author")
    )

    def reset(self):
        """We must use dictionary syntax to avoid the setter callback."""
        self['svn_directory'] = ""
        self['svn_url'] = ""
        self['relative_filepath'] = ""
        self['revision_number'] = -1
        self['revision_date'] = ""
        self['revision_author'] = ""
        self['is_in_repo'] = False

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
