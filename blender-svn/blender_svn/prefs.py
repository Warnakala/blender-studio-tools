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
from bpy.props import StringProperty, IntProperty, BoolProperty, CollectionProperty

from .util import make_getter_func, make_setter_func_readonly, get_addon_prefs
from . import svn_status
from .execute_subprocess import execute_command

logger = logging.getLogger(name="SVN")


class SVN_credential(bpy.types.PropertyGroup):
    """Authentication information of a single SVN repository."""
    url: StringProperty(
        name = "SVN URL",
        description = "URL of the remote repository"
    )

    def update_cred(self, context):
        if not (self.username and self.password):
            # Only try to authenticate if BOTH username AND pw are entered.
            return
        self.svn_error = ""
        prefs = get_addon_prefs(context)
        output = execute_command(prefs.svn_directory, f'svn status --show-updates --username "{self.username}" --password "{self.password}"')
        if type(output) == str:
            svn_status.init_svn(context, None)
            self.authenticated = True
            self.auth_failed = False

            # For some ungodly reason, ONLY with this addon, 
            # CollectionProperties stored in the AddonPrefs do not get
            # auto-saved, only manually saved! So... we get it done.
            if context.preferences.use_preferences_save:
                bpy.ops.wm.save_userpref()

            return

        error = output.stderr.decode()
        if "Authentication failed" in error:
            self.authenticated = False
            self.auth_failed = True
        else:
            self.authenticated = False
            self.auth_failed = False
            self.svn_error = output

    username: StringProperty(
        name = "SVN Username",
        description = "User name used for authentication with this SVN repository",
        update = update_cred
    )
    password: StringProperty(
        name = "SVN Password",
        description = "Password used for authentication with this SVN repository. This password is stored in your Blender user preferences as plain text. Somebody with access to your user preferences will be able to read your password",
        subtype='PASSWORD',
        update = update_cred
    )

    authenticated: BoolProperty(
        name = "Authenticated",
        description = "Internal flag to mark whether the last entered credentials were confirmed by the repo as correct credentials",
        default = False
    )
    auth_failed: BoolProperty(
        name = "Authentication Failed",
        description = "Internal flag to mark whether the last entered credentials were denied by the repo",
        default = False
    )
    svn_error: StringProperty(
        name = "SVN Error",
        description = "If SVN throws an error other than authentication error, store it here.",
        default = ""
    )


class SVN_UL_credentials(bpy.types.UIList):
    
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        thing = item
        row = layout.row()
        row.prop(thing, 'name', text="", icon='FILE_TEXT')
        row.prop(thing, 'url', text="", icon='URL')
        row.prop(thing, 'username', text="", icon='USER')
        row.prop(thing, 'password', text="", icon='LOCKED')


class SVN_addon_preferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    svn_credentials: CollectionProperty(type=SVN_credential)
    svn_cred_active_idx: IntProperty()

    def get_credentials(self, get_entry=False) -> Optional[Tuple[str, str]]:
        svn_url = self.svn_url
        for cred in self.svn_credentials:
            if cred.url == svn_url:
                if get_entry:
                    return cred
                return cred.username, cred.password

        if get_entry:
            return None
        return None, None

    log_update_in_background: BoolProperty(
        name="Auto-Update SVN Log",
        default=True, 
        description="Allow keeping the SVN log up to date automatically. Disable if suspected of causing problems"
    )

    def update_status_update_in_background(self, context):
        if self.status_update_in_background:
            svn_status.svn_status_background_fetch_start(None, None)
        else:
            svn_status.svn_status_background_fetch_stop()
        
    status_update_in_background: BoolProperty(
        name="Auto-Update File Status",
        default=True,
        description="Allow keeping file statuses up to date automatically. Disable if suspected of causing problems",
        update=update_status_update_in_background
    )

    enable_ui: BoolProperty(
        name="Enable UI",
        default=True,
        description="Enable UI in sidebar for debugging/testing",
    )

    # TODO: Everything below this should be moved to SVN_scene_properties...
    is_in_repo: BoolProperty(
        name="is_in_repo",
        default=False,
        description="To store whether the current file was deemed to be in an SVN repository on file save/load. For internal use only"
    )

    def update_filters(dummy, context):
        """Should run when any of the SVN file list search filters are changed."""
        context.scene.svn.force_good_active_index(context)

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
        # layout.prop(self, 'enable_ui')
        layout.label(text="Debug stuff:")
        layout.prop(self, 'log_update_in_background')
        layout.prop(self, 'status_update_in_background')

        layout.label(text="Saved credentials:")
        col = layout.column()
        col.enabled=False
        col.template_list(
            "SVN_UL_credentials",
            "svn_cred_list",
            self,
            "svn_credentials",
            self,
            "svn_cred_active_idx",
        )


# ----------------REGISTER--------------.

registry = [
    SVN_UL_credentials,
    SVN_credential,
    SVN_addon_preferences
]
