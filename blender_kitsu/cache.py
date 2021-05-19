from typing import Any

import bpy

from bpy.app.handlers import persistent
from .types import Project, Sequence, Shot, Asset, AssetType, TaskType
from .logger import ZLoggerFactory
from .gazu.exception import RouteNotFoundException

logger = ZLoggerFactory.getLogger(name=__name__)

# CACHE VARIABLES
# used to cache active entitys to prevent a new api request when read only
_project_active: Project = Project()
_sequence_active: Sequence = Sequence()
_shot_active: Shot = Shot()
_asset_active: Asset = Asset()
_asset_type_active: AssetType = AssetType()
_task_type_active: TaskType = TaskType()

_cache_initialized: bool = False


def _addon_prefs_get(context: bpy.types.Context) -> bpy.types.AddonPreferences:
    """
    shortcut to get blender_kitsu addon preferences
    """
    return context.preferences.addons["blender_kitsu"].preferences


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


def init_cache_variables() -> None:
    global _project_active
    global _sequence_active
    global _shot_active
    global _asset_active
    global _asset_type_active
    global _task_type_active
    global _cache_initialized

    addon_prefs = _addon_prefs_get(bpy.context)
    project_active_id = addon_prefs.project_active_id
    sequence_active_id = bpy.context.scene.kitsu.sequence_active_id
    shot_active_id = bpy.context.scene.kitsu.shot_active_id
    asset_active_id = bpy.context.scene.kitsu.asset_active_id
    asset_type_active_id = bpy.context.scene.kitsu.asset_type_active_id
    task_type_active_id = bpy.context.scene.kitsu.task_type_active_id

    if not addon_prefs.session.is_auth():
        logger.info("Skip initiating cache. Session not authorized.")
        return

    if _cache_initialized:
        logger.info("Cache already initiated.")
        return

    # TODO: refactor in one function with parameter for entity

    if project_active_id:
        try:
            _project_active = Project.by_id(project_active_id)
            logger.info("Initiated active project cache to: %s", _project_active.name)
        except RouteNotFoundException:
            logger.error(
                "Failed to initialize active project cache. ID not found on server: %s",
                project_active_id,
            )

    if sequence_active_id:
        try:
            _sequence_active = Sequence.by_id(sequence_active_id)
            logger.info("Initiated active sequence cache to: %s", _sequence_active.name)
        except RouteNotFoundException:
            logger.error(
                "Failed to initialize active sequence cache. ID not found on server: %s",
                sequence_active_id,
            )

    if shot_active_id:
        try:
            _shot_active = Shot.by_id(shot_active_id)
            logger.info("Initiated active shot cache to: %s ", _shot_active.name)
        except RouteNotFoundException:
            logger.error(
                "Failed to initialize active shot cache. ID not found on server: %s",
                shot_active_id,
            )

    if asset_active_id:
        try:
            _asset_active = Asset.by_id(asset_active_id)
            logger.info("Initiated active asset cache to: %s", _asset_active.name)
        except RouteNotFoundException:
            logger.error(
                "Failed to initialize active asset cache. ID not found on server: %s",
                asset_active_id,
            )

    if asset_type_active_id:
        try:
            _asset_type_active = AssetType.by_id(asset_type_active_id)
            logger.info(
                "Initiated active asset type cache to: %s ", _asset_type_active.name
            )
        except RouteNotFoundException:
            logger.error(
                "Failed to initialize active asset type cache. ID not found on server: %s",
                asset_type_active_id,
            )

    if task_type_active_id:
        try:
            _task_type_active = TaskType.by_id(task_type_active_id)
            logger.info(
                "Initiated active task type cache to: %s ", _task_type_active.name
            )
        except RouteNotFoundException:
            logger.error(
                "Failed to initialize active task type cache. ID not found on server: %s",
                task_type_active_id,
            )

    _cache_initialized = True


def clear_cache_variables():
    global _project_active
    global _sequence_active
    global _shot_active
    global _asset_active
    global _asset_type_active
    global _cache_initialized

    _shot_active = Shot()
    logger.info("Cleared active shot cache")

    _asset_active = Asset()
    logger.info("Cleared active asset cache")

    _sequence_active = Sequence()
    logger.info("Cleared active aequence cache")

    _asset_type_active = AssetType()
    logger.info("Cleared active asset type cache")

    _project_active = Project()
    logger.info("Cleared Active Project Cache")

    _cache_initialized = False


@persistent
def load_post_handler_update_cache(dummy: Any) -> None:
    clear_cache_variables()
    init_cache_variables()


@persistent
def load_post_handler_check_frame_range(dummy: Any) -> None:
    """
    Compares current scenes frame range with the active shot one on kitsu.
    If mismatch sets kitsu_error.frame_range -> True. This will enable
    a warning in the Animation Tools Tab UI
    """
    active_shot = shot_active_get()

    if not active_shot:
        return

    frame_in = active_shot.frame_in
    frame_out = active_shot.frame_out

    if (
        frame_in == bpy.context.scene.frame_start
        and frame_out == bpy.context.scene.frame_end
    ):
        bpy.context.scene.kitsu_error.frame_range = False
        return

    bpy.context.scene.kitsu_error.frame_range = True
    logger.warning("Current frame range is outdated!")


# ---------REGISTER ----------


def register():
    # handlers
    bpy.app.handlers.load_post.append(load_post_handler_update_cache)
    bpy.app.handlers.load_post.append(load_post_handler_check_frame_range)


def unregister():
    # clear handlers
    bpy.app.handlers.load_post.remove(load_post_handler_check_frame_range)
    bpy.app.handlers.load_post.remove(load_post_handler_update_cache)
