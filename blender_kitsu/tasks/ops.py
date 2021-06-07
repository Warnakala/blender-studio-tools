from typing import Dict, List, Set, Optional, Tuple, Any
from blender_kitsu import tasks

import bpy

from blender_kitsu import cache, prefs, gazu, util

from blender_kitsu.tasks import opsdata
from blender_kitsu.logger import LoggerFactory

logger = LoggerFactory.getLogger(name=__name__)


class KITSU_OT_tasks_user_laod(bpy.types.Operator):
    """
    Gets all tasks that the current logged in user is assgined to
    """

    bl_idname = "kitsu.tasks_user_laod"
    bl_label = "Tasks Load"
    bl_property = "enum_prop"

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return prefs.session_auth(context)

    def execute(self, context: bpy.types.Context) -> Set[str]:
        addon_prefs = prefs.addon_prefs_get(context)
        tasks_coll_prop = addon_prefs.tasks
        active_user = cache.user_active_get()

        # load tasks this also updates the collection property
        cache.load_user_all_tasks(context)

        util.ui_redraw()

        self.report(
            {"INFO"},
            f"Fetched {len(tasks_coll_prop.items())} tasks for {active_user.full_name}",
        )
        return {"FINISHED"}


# ---------REGISTER ----------

classes = [KITSU_OT_tasks_user_laod]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
