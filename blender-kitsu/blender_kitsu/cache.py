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

from typing import Any, List, Union, Dict, Tuple

import bpy

from bpy.app.handlers import persistent

from blender_kitsu.types import (
    Project,
    Sequence,
    Shot,
    Asset,
    AssetType,
    TaskType,
    Task,
    ProjectList,
    TaskStatus,
    Cache,
    User,
)
from blender_kitsu.logger import LoggerFactory
from blender_kitsu.gazu.exception import RouteNotFoundException

logger = LoggerFactory.getLogger(name=__name__)

# CACHE VARIABLES
# used to cache active entitys to prevent a new api request when read only
_project_active: Project = Project()
_sequence_active: Sequence = Sequence()
_shot_active: Shot = Shot()
_asset_active: Asset = Asset()
_asset_type_active: AssetType = AssetType()
_task_type_active: TaskType = TaskType()
_user_active: User = User()
_user_all_tasks: List[Task] = []

_cache_initialized: bool = False
_cache_startup_initialized: bool = False

_sequence_enum_list: List[Tuple[str, str, str]] = []
_shot_enum_list: List[Tuple[str, str, str]] = []
_asset_types_enum_list: List[Tuple[str, str, str]] = []
_asset_enum_list: List[Tuple[str, str, str]] = []
_projects_enum_list: List[Tuple[str, str, str]] = []
_task_types_enum_list: List[Tuple[str, str, str]] = []
_task_types_shots_enum_list: List[Tuple[str, str, str]] = []
_task_statuses_enum_list: List[Tuple[str, str, str]] = []
_user_all_tasks_enum_list: List[Tuple[str, str, str]] = []


def _addon_prefs_get(context: bpy.types.Context) -> bpy.types.AddonPreferences:
    """
    shortcut to get blender_kitsu addon preferences
    """
    return context.preferences.addons["blender_kitsu"].preferences


def user_active_get() -> User:
    global _user_active

    return _user_active


def project_active_get() -> Project:
    global _project_active

    return _project_active


def project_active_set_by_id(context: bpy.types.Context, entity_id: str) -> None:
    global _project_active

    _project_active = Project.by_id(entity_id)
    _addon_prefs_get(context).project_active_id = entity_id
    logger.info("Set active project to %s", _project_active.name)


def project_active_reset(context: bpy.types.Context) -> None:
    global _project_active
    _project_active = Project()
    _addon_prefs_get(context).project_active_id = ""
    logger.info("Reset active project")


def sequence_active_get() -> Sequence:
    return _sequence_active


def sequence_active_set_by_id(context: bpy.types.Context, entity_id: str) -> None:
    global _sequence_active

    _sequence_active = Sequence.by_id(entity_id)
    context.scene.kitsu.sequence_active_id = entity_id
    logger.info("Set active sequence to %s", _sequence_active.name)


def sequence_active_reset(context: bpy.types.Context) -> None:
    global _sequence_active

    _sequence_active = Sequence()
    context.scene.kitsu.sequence_active_id = ""
    logger.info("Reset active sequence")


def shot_active_get() -> Shot:
    global _shot_active

    return _shot_active


def shot_active_pull_update() -> Shot:
    global _shot_active
    Cache.clear_all()
    shot_active_id = bpy.context.scene.kitsu.shot_active_id
    _init_cache_entity(shot_active_id, Shot, "_shot_active", "shot")
    return _shot_active


def shot_active_set_by_id(context: bpy.types.Context, entity_id: str) -> None:
    global _shot_active

    _shot_active = Shot.by_id(entity_id)
    context.scene.kitsu.shot_active_id = entity_id
    logger.info("Set active shot to %s", _shot_active.name)


def shot_active_reset(context: bpy.types.Context) -> None:
    global _shot_active

    _shot_active = Shot()
    context.scene.kitsu.shot_active_id = ""
    logger.info("Reset active shot")


def asset_active_get() -> Asset:
    global _asset_active

    return _asset_active


def asset_active_set_by_id(context: bpy.types.Context, entity_id: str) -> None:
    global _asset_active

    _asset_active = Asset.by_id(entity_id)
    context.scene.kitsu.asset_active_id = entity_id
    logger.info("Set active asset to %s", _asset_active.name)


def asset_active_reset(context: bpy.types.Context) -> None:
    global _asset_active

    _asset_active = Asset()
    context.scene.kitsu.asset_active_id = ""
    logger.info("Reset active asset")


def asset_type_active_get() -> AssetType:
    global _asset_type_active

    return _asset_type_active


def asset_type_active_set_by_id(context: bpy.types.Context, entity_id: str) -> None:
    global _asset_type_active

    _asset_type_active = AssetType.by_id(entity_id)
    context.scene.kitsu.asset_type_active_id = entity_id
    logger.info("Set active asset type to %s", _asset_type_active.name)


def asset_type_active_reset(context: bpy.types.Context) -> None:
    global _asset_type_active

    _asset_type_active = AssetType()
    context.scene.kitsu.asset_type_active_id = ""
    logger.info("Reset active asset type")


def task_type_active_get() -> TaskType:
    global _task_type_active

    return _task_type_active


def task_type_active_set_by_id(context: bpy.types.Context, entity_id: str) -> None:
    global _task_type_active

    _task_type_active = TaskType.by_id(entity_id)
    context.scene.kitsu.task_type_active_id = entity_id
    logger.info("Set active task type to %s", _task_type_active.name)


def task_type_active_reset(context: bpy.types.Context) -> None:
    global _task_type_active

    _task_type_active = TaskType()
    context.scene.kitsu.task_type_active_id = ""
    logger.info("Reset active task type")


def get_projects_enum_list(
    self: bpy.types.Operator, context: bpy.types.Context
) -> List[Tuple[str, str, str]]:
    global _projects_enum_list

    if not _addon_prefs_get(context).session.is_auth():
        return []

    projectlist = ProjectList()
    _projects_enum_list.clear()
    _projects_enum_list.extend(
        [(p.id, p.name, p.description or "") for p in projectlist.projects]
    )
    return _projects_enum_list


def get_sequences_enum_list(
    self: bpy.types.Operator, context: bpy.types.Context
) -> List[Tuple[str, str, str]]:
    global _sequence_enum_list

    project_active = project_active_get()
    if not project_active:
        return []

    _sequence_enum_list.clear()
    _sequence_enum_list.extend(
        [
            (s.id, s.name, s.description or "")
            for s in project_active.get_sequences_all()
        ]
    )
    return _sequence_enum_list


def get_shots_enum_for_active_seq(
    self: bpy.types.Operator, context: bpy.types.Context
) -> List[Tuple[str, str, str]]:
    global _shot_enum_list

    zseq_active = sequence_active_get()

    if not zseq_active:
        return []

    _shot_enum_list.clear()
    _shot_enum_list.extend(
        [(s.id, s.name, s.description or "") for s in zseq_active.get_all_shots()]
    )
    return _shot_enum_list


def get_assetypes_enum_list(
    self: bpy.types.Operator, context: bpy.types.Context
) -> List[Tuple[str, str, str]]:
    global _asset_types_enum_list

    project_active = project_active_get()
    if not project_active:
        return []

    _asset_types_enum_list.clear()
    _asset_types_enum_list.extend(
        [(at.id, at.name, "") for at in project_active.get_all_asset_types()]
    )
    return _asset_types_enum_list


def get_assets_enum_for_active_asset_type(
    self: bpy.types.Operator, context: bpy.types.Context
) -> List[Tuple[str, str, str]]:
    global _asset_enum_list

    project_active = project_active_get()
    asset_type_active = asset_type_active_get()

    if not project_active or not asset_type_active:
        return []

    _asset_enum_list.clear()
    _asset_enum_list.extend(
        [
            (a.id, a.name, a.description or "")
            for a in project_active.get_all_assets_for_type(asset_type_active)
        ]
    )
    return _asset_enum_list


def get_task_types_enum_for_current_context(
    self: bpy.types.Operator, context: bpy.types.Context
) -> List[Tuple[str, str, str]]:
    global _task_types_enum_list

    items = []
    if context.scene.kitsu.category == "SHOTS":
        shot_active = shot_active_get()
        if not shot_active:
            return []
        items = [(t.id, t.name, "") for t in TaskType.all_shot_task_types()]

    if context.scene.kitsu.category == "ASSETS":
        asset_active = asset_active_get()
        if not asset_active:
            return []
        items = [(t.id, t.name, "") for t in TaskType.all_asset_task_types()]

    _task_types_enum_list.clear()
    _task_types_enum_list.extend(items)

    return _task_types_enum_list


def get_shot_task_types_enum(
    self: bpy.types.Operator, context: bpy.types.Context
) -> List[Tuple[str, str, str]]:
    global _task_types_shots_enum_list

    items = [(t.id, t.name, "") for t in TaskType.all_shot_task_types()]

    _task_types_shots_enum_list.clear()
    _task_types_shots_enum_list.extend(items)

    return _task_types_shots_enum_list


def get_all_task_statuses_enum(
    self: bpy.types.Operator, context: bpy.types.Context
) -> List[Tuple[str, str, str]]:
    global _task_statuses_enum_list

    items = [(t.id, t.name, "") for t in TaskStatus.all_task_statuses()]

    _task_statuses_enum_list.clear()
    _task_statuses_enum_list.extend(items)

    return _task_statuses_enum_list


def load_user_all_tasks(context: bpy.types.Context) -> List[Task]:
    global _user_all_tasks
    global _user_active

    tasks = _user_active.all_tasks_to_do()
    _user_all_tasks.clear()
    _user_all_tasks.extend(tasks)

    _update_tasks_collection_prop(context)

    logger.info("Loaded assigned tasks for: %s", _user_active.full_name)

    return _user_all_tasks


def _update_tasks_collection_prop(context: bpy.types.Context) -> None:
    global _user_all_tasks
    addon_prefs = _addon_prefs_get(bpy.context)
    tasks_coll_prop = addon_prefs.tasks

    # Get current index.
    idx = context.window_manager.kitsu.tasks_index

    # Clear all old tasks.
    tasks_coll_prop.clear()

    # Populate with new tasks.
    for task in _user_all_tasks:
        item = tasks_coll_prop.add()
        item.id = task.id
        item.entity_id = task.entity_id
        item.entity_name = task.entity_name
        item.task_type_id = task.task_type_id
        item.task_type_name = task.task_type_name

    # Update index.
    idx = len(tasks_coll_prop) - 1


def get_user_all_tasks_enum(
    self: bpy.types.Operator, context: bpy.types.Context
) -> List[Tuple[str, str, str]]:
    global _user_all_tasks_enum_list
    global _user_all_tasks

    enum_items = [(t.id, t.name, "") for t in _user_all_tasks]

    _user_all_tasks_enum_list.clear()
    _user_all_tasks_enum_list.extend(enum_items)

    return _user_all_tasks_enum_list


def get_user_all_tasks() -> List[Task]:
    global _user_all_tasks
    return _user_all_tasks


def _init_cache_entity(
    entity_id: str, entity_type: Any, cache_variable_name: Any, cache_name: str
) -> None:

    if entity_id:
        try:
            globals()[cache_variable_name] = entity_type.by_id(entity_id)
            logger.info(
                "Initiated active %s cache to: %s",
                cache_name,
                globals()[cache_variable_name].name,
            )
        except RouteNotFoundException:
            logger.error(
                "Failed to initialize active %s cache. ID not found on server: %s",
                cache_name,
                entity_id,
            )


def init_startup_variables(context: bpy.types.Context) -> None:
    addon_prefs = _addon_prefs_get(context)
    global _cache_startup_initialized
    global _user_active
    global _user_all_tasks

    if not addon_prefs.session.is_auth():
        logger.info("Skip initiating startup cache. Session not authorized")
        return

    if _cache_startup_initialized:
        logger.info("Startup Cache already initiated")
        return

    # User.
    _user_active = User()
    logger.info("Initiated active user cache to: %s", _user_active.full_name)

    # User Tasks.
    load_user_all_tasks(context)
    logger.info("Initiated active user tasks")

    _cache_startup_initialized = True


def clear_startup_variables():
    global _user_active
    global _user_all_tasks
    global _cache_startup_initialized

    _user_active = User()
    logger.info("Cleared active user cache")

    _user_all_tasks.clear()
    _update_tasks_collection_prop(bpy.context)
    logger.info("Cleared active user all tasks cache")

    _cache_startup_initialized = False


def init_cache_variables() -> None:
    global _project_active
    global _sequence_active
    global _shot_active
    global _asset_active
    global _asset_type_active
    global _task_type_active
    global _cache_initialized
    addon_prefs = _addon_prefs_get(bpy.context)

    if not addon_prefs.session.is_auth():
        logger.info("Skip initiating cache. Session not authorized")
        return

    if _cache_initialized:
        logger.info("Cache already initiated")
        return

    project_active_id = addon_prefs.project_active_id
    sequence_active_id = bpy.context.scene.kitsu.sequence_active_id
    shot_active_id = bpy.context.scene.kitsu.shot_active_id
    asset_active_id = bpy.context.scene.kitsu.asset_active_id
    asset_type_active_id = bpy.context.scene.kitsu.asset_type_active_id
    task_type_active_id = bpy.context.scene.kitsu.task_type_active_id

    _init_cache_entity(project_active_id, Project, "_project_active", "project")
    _init_cache_entity(sequence_active_id, Sequence, "_sequence_active", "sequence")
    _init_cache_entity(
        asset_type_active_id, AssetType, "_asset_type_active", "asset type"
    )
    _init_cache_entity(shot_active_id, Shot, "_shot_active", "shot")
    _init_cache_entity(asset_active_id, Asset, "_asset_active", "asset")
    _init_cache_entity(task_type_active_id, TaskType, "_task_type_active", "task type")

    _cache_initialized = True


def clear_cache_variables():
    global _project_active
    global _sequence_active
    global _shot_active
    global _asset_active
    global _asset_type_active
    global _task_type_active
    global _cache_initialized

    _user_active = User()
    logger.info("Cleared active user cache")

    _shot_active = Shot()
    logger.info("Cleared active shot cache")

    _asset_active = Asset()
    logger.info("Cleared active asset cache")

    _sequence_active = Sequence()
    logger.info("Cleared active aequence cache")

    _asset_type_active = AssetType()
    logger.info("Cleared active asset type cache")

    _project_active = Project()
    logger.info("Cleared active project cache")

    _task_type_active = TaskType()
    logger.info("Cleared active task type cache")

    _cache_initialized = False


@persistent
def load_post_handler_update_cache(dummy: Any) -> None:
    clear_cache_variables()
    init_cache_variables()


@persistent
def load_post_handler_init_startup_variables(dummy: Any) -> None:
    init_startup_variables(bpy.context)


# ---------REGISTER ----------.


def register():
    # Handlers.
    bpy.app.handlers.load_post.append(load_post_handler_update_cache)
    bpy.app.handlers.load_post.append(load_post_handler_init_startup_variables)


def unregister():
    # Clear handlers.
    bpy.app.handlers.load_post.remove(load_post_handler_init_startup_variables)
    bpy.app.handlers.load_post.remove(load_post_handler_update_cache)
