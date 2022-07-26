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

from typing import Optional, Any, Set, Tuple, List

import subprocess
import bpy
from bpy.props import StringProperty, IntProperty, BoolProperty, CollectionProperty

from . import svn_status
from .background_process import BackgroundProcess, process_in_background
from .execute_subprocess import execute_svn_command
from .util import redraw_viewport

class BGP_SVN_Authenticate(BackgroundProcess):
    name = "Authenticate"
    needs_authentication = False
    timeout = 10
    repeat_delay = 0

    def tick(self, context, prefs):
        redraw_viewport()

    def acquire_output(self, context, prefs):
        cred = prefs.get_credentials()
        if not cred:
            return

        try:
            self.output = execute_svn_command(
                context, 
                f'svn status --show-updates --username "{cred.username}" --password "{cred.password}"'
            )
            self.debug_print("Output: \n" + self.output)
        except subprocess.CalledProcessError as error:
            self.error = error.stderr.decode()

    def process_output(self, context, prefs):
        self.debug_print("process_output()")
        cred = prefs.get_credentials()
        if not cred:
            return

        if self.output:
            cred.authenticated = True
            cred.auth_failed = False
            self.debug_print("Run init_svn()")
            svn_status.init_svn(context, None)
            return
        elif self.error:
            if "Authentication failed" in self.error:
                cred.authenticated = False
                cred.auth_failed = True
            else:
                cred.authenticated = False
                cred.auth_failed = False
            return


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

        process_in_background(BGP_SVN_Authenticate)
        svn_status.init_svn(context, None)

        # For some ungodly reason, ONLY with this addon, 
        # CollectionProperties stored in the AddonPrefs do not get
        # auto-saved, only manually saved! So... we get it done.
        if context.preferences.use_preferences_save:
            bpy.ops.wm.save_userpref()


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

    def get_credentials(self) -> Optional[SVN_credential]:
        svn_url = bpy.context.scene.svn.svn_url
        for cred in self.svn_credentials:
            if cred.url == svn_url:
                return cred

        return None

    def draw(self, context) -> None:
        layout = self.layout

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
