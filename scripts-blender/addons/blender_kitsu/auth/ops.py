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

from typing import Dict, List, Set, Optional, Tuple, Any

import bpy
import threading

from blender_kitsu import cache, prefs, gazu

# TODO: restructure this to not access ops_playblast_data.
from blender_kitsu.playblast import opsdata as ops_playblast_data
from blender_kitsu.playblast import ops as ops_playblast
from blender_kitsu.logger import LoggerFactory

logger = LoggerFactory.getLogger()

active_thread = False

class KITSU_OT_session_start(bpy.types.Operator):
    """
    Starts the Session, which  is stored in blender_kitsu addon preferences.
    Authenticates user with server until session ends.
    Host, email and password are retrieved from blender_kitsu addon preferences.
    """

    bl_idname = "kitsu.session_start"
    bl_label = "Start Kitsu Session"
    bl_options = {"INTERNAL"}
    bl_description = (
        "Logs in to server with the credentials that are defined in the "
        "addon preferences. Session is valid until Blender closes"
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return True

    def execute(self, context: bpy.types.Context) -> Set[str]:
        self.thread_login(context)
        if not prefs.session_get(context).is_auth():
            self.report({"ERROR"}, "Login data not correct")
            logger.error("Login data not correct")
            return {"CANCELLED"}

        # Init cache variables, will skip if cache already initiated.
        cache.init_cache_variables()

        # Init startup variables, will skip if cache already initiated.
        cache.init_startup_variables(context)

        # Init playblast version dir model.
        ops_playblast_data.init_playblast_file_model(context)

        # Check frame range.
        ops_playblast.load_post_handler_check_frame_range(None)
        return {"FINISHED"}

    def get_config(self, context: bpy.types.Context) -> Dict[str, str]:
        addon_prefs = prefs.addon_prefs_get(context)
        return {
            "email": addon_prefs.email,
            "host": addon_prefs.host,
            "passwd": addon_prefs.passwd,
        }

    def kitsu_session_start(self, context):
        session = prefs.session_get(context)
        session.set_config(self.get_config(context))
        try:
            session_data = session.start()
            self.report({"INFO"}, f"Logged in as {session_data.user['full_name']}")
        finally:
            return

    def thread_login(self, context):
        global active_thread
        if active_thread:
            active_thread._stop()
        active_thread = threading.Thread(
            target=self.kitsu_session_start(context), daemon=True
        )
        active_thread.start()


class KITSU_OT_session_end(bpy.types.Operator):
    """
    Ends the Session which is stored in blender_kitsu addon preferences.
    """

    bl_idname = "kitsu.session_end"
    bl_label = "End Kitsu Session"
    bl_options = {"INTERNAL"}
    bl_description = "Logs active user out"

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return prefs.session_auth(context)

    def execute(self, context: bpy.types.Context) -> Set[str]:
        session = prefs.session_get(context)
        session.end()

        # Clear cache variables.
        cache.clear_cache_variables()

        # Clear startup variables.
        cache.clear_startup_variables()

        self.report({"INFO"}, "Logged out")

        return {"FINISHED"}


def auto_login_on_file_open():
    context = bpy.context
    session = prefs.session_get(context)
    if not session.is_auth():
        bpy.ops.kitsu.session_start()

# ---------REGISTER ----------.

classes = [
    KITSU_OT_session_start,
    KITSU_OT_session_end,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    # Note: Since this timer function does not repeat
    # (because it doesn't return a value)
    # it automatically un-registers after it runs.
    # FIXME: XXX This makes Blender hang if there is no Internet connectivity
    # TODO: Rewrite this, so the 'auto' login happens out of the main thread
    bpy.app.timers.register(auto_login_on_file_open, first_interval=0.2)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
