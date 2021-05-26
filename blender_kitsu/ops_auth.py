from typing import Dict, List, Set, Optional, Tuple, Any

import bpy

from blender_kitsu import cache, prefs
from blender_kitsu.anim import opsdata as ops_anim_data
from blender_kitsu.logger import ZLoggerFactory

logger = ZLoggerFactory.getLogger(name=__name__)


class KITSU_OT_session_start(bpy.types.Operator):
    """
    Starts the Session, which  is stored in blender_kitsu addon preferences.
    Authenticates user with server until session ends.
    Host, email and password are retrieved from blender_kitsu addon preferences.
    """

    bl_idname = "kitsu.session_start"
    bl_label = "Start Kitsu Session"
    bl_options = {"INTERNAL"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return True

    def execute(self, context: bpy.types.Context) -> Set[str]:
        session = prefs.session_get(context)

        session.set_config(self.get_config(context))
        session.start()

        # init cache variables, will skip if cache already initiated
        cache.init_cache_variables()

        # init playblast version dir model
        ops_anim_data.init_playblast_file_model(context)

        return {"FINISHED"}

    def get_config(self, context: bpy.types.Context) -> Dict[str, str]:
        addon_prefs = prefs.addon_prefs_get(context)
        return {
            "email": addon_prefs.email,
            "host": addon_prefs.host,
            "passwd": addon_prefs.passwd,
        }


class KITSU_OT_session_end(bpy.types.Operator):
    """
    Ends the Session which is stored in blender_kitsu addon preferences.
    """

    bl_idname = "kitsu.session_end"
    bl_label = "End Kitsu Session"
    bl_options = {"INTERNAL"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return prefs.session_auth(context)

    def execute(self, context: bpy.types.Context) -> Set[str]:
        session = prefs.session_get(context)
        session.end()
        # clear cache variables
        cache.clear_cache_variables()
        return {"FINISHED"}


# ---------REGISTER ----------

classes = [
    KITSU_OT_session_start,
    KITSU_OT_session_end,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
