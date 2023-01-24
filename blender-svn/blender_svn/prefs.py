# SPDX-License-Identifier: GPL-2.0-or-later
# (c) 2021, Blender Foundation - Paul Golter
# (c) 2022, Blender Foundation - Demeter Dzadik

from typing import Optional, Any, Set, Tuple, List

import bpy
from bpy.props import StringProperty, IntProperty, BoolProperty, CollectionProperty

from . import svn_status
from .background_process import process_in_background
from .util import redraw_viewport, get_addon_prefs

class BGP_SVN_Authenticate(svn_status.BGP_SVN_Status):
    name = "Authenticate"
    needs_authentication = False
    timeout = 10
    repeat_delay = 0
    debug = False

    def tick(self, context, prefs):
        redraw_viewport()

    def acquire_output(self, context, prefs):
        cred = prefs.get_credentials()
        if not cred:
            return

        super().acquire_output(context, prefs)

    def process_output(self, context, prefs):
        cred = prefs.get_credentials()
        if not cred:
            return

        if self.output:
            cred.authenticated = True
            cred.auth_failed = False
            self.debug_print("Run init_svn()")
            svn_status.init_svn(context, None)

            super().process_output(context, prefs)
            return
        elif self.error:
            if "Authentication failed" in self.error:
                cred.authenticated = False
                cred.auth_failed = True
            else:
                cred.authenticated = False
                cred.auth_failed = False


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

        self.auth_failed = False

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
    svn_cred_active_idx: IntProperty(
        name = "SVN Credentials",
        options = set()
    )

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


@bpy.app.handlers.persistent
def try_authenticating_on_file_load(_dummy1, _dummy2):
    context = bpy.context
    prefs = get_addon_prefs(context)
    cred = prefs.get_credentials()
    if cred:
        print("SVN: Credentials found. Try authenticating on file load...")
        # Don't assume that a previously saved password is still correct.
        cred.authenticated = False
        # Trigger the update callback.
        cred.password = cred.password


# ----------------REGISTER--------------.

registry = [
    SVN_UL_credentials,
    SVN_credential,
    SVN_addon_preferences
]

def register():
    bpy.app.handlers.load_post.append(try_authenticating_on_file_load)

def unregister():
    bpy.app.handlers.load_post.remove(try_authenticating_on_file_load)
