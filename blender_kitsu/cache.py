import bpy

from bpy.app.handlers import persistent
from .types import Project, Sequence, Shot, Asset, AssetType
from .logger import ZLoggerFactory

logger = ZLoggerFactory.getLogger(name=__name__)

# CACHE VARIABLES
# used to cache active entitys to prevent a new api request when read only
_project_active: Project = Project()
_sequence_active: Sequence = Sequence()
_shot_active: Shot = Shot()
_asset_active: Asset = Asset()
_asset_type_active: AssetType = AssetType()

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


def project_active_reset(context: bpy.types.Context) -> None:
    global _project_active
    _project_active = Project()
    _addon_prefs_get(context).project_active_id = ""


def sequence_active_get() -> Sequence:
    return _sequence_active


def sequence_active_set_by_id(context: bpy.types.Context, entity_id: str) -> None:
    global _sequence_active

    _sequence_active = Sequence.by_id(entity_id)
    context.scene.kitsu.sequence_active_id = entity_id


def sequence_active_reset(context: bpy.types.Context) -> None:
    global _sequence_active

    _sequence_active = Sequence()
    context.scene.kitsu.sequence_active_id = ""


def shot_active_get() -> Shot:
    global _shot_active

    return _shot_active


def shot_active_set_by_id(context: bpy.types.Context, entity_id: str) -> None:
    global _shot_active

    _shot_active = Shot.by_id(entity_id)
    context.scene.kitsu.shot_active_id = entity_id


def shot_active_reset(context: bpy.types.Context) -> None:
    global _shot_active

    _shot_active = Shot()
    context.scene.kitsu.shot_active_id = ""


def asset_active_get() -> Asset:
    global _asset_active

    return _asset_active


def asset_active_set_by_id(context: bpy.types.Context, entity_id: str) -> None:
    global _asset_active

    _asset_active = Asset.by_id(entity_id)
    context.scene.kitsu.asset_active_id = entity_id


def asset_active_reset(context: bpy.types.Context) -> None:
    global _asset_active

    _asset_active = Asset()
    context.scene.kitsu.asset_active_id = ""


def asset_type_active_get() -> AssetType:
    global _asset_type_active

    return _asset_type_active


def asset_type_active_set_by_id(context: bpy.types.Context, entity_id: str) -> None:
    global _asset_type_active

    _asset_type_active = AssetType.by_id(entity_id)
    context.scene.kitsu.asset_type_active_id = entity_id


def asset_type_active_reset(context: bpy.types.Context) -> None:
    global _asset_type_active

    _asset_type_active = AssetType()
    context.scene.kitsu.asset_type_active_id = ""


def init_cache_variables() -> None:
    global _project_active
    global _sequence_active
    global _shot_active
    global _asset_active
    global _asset_type_active
    global _cache_initialized

    addon_prefs = _addon_prefs_get(bpy.context)
    project_active_id = addon_prefs.project_active_id
    sequence_active_id = bpy.context.scene.kitsu.sequence_active_id
    shot_active_id = bpy.context.scene.kitsu.shot_active_id
    asset_active_id = bpy.context.scene.kitsu.asset_active_id
    asset_type_active_id = bpy.context.scene.kitsu.asset_type_active_id

    if not addon_prefs.session.is_auth():
        logger.info("Skip initiating cache. Session not authorized.")
        return

    if _cache_initialized:
        logger.info("Cache already initiated.")
        return

    if project_active_id:
        _project_active = Project.by_id(project_active_id)
        logger.info("Initiated Active Project Cache to: %s", _project_active.name)

    if sequence_active_id:
        _sequence_active = Sequence.by_id(sequence_active_id)
        logger.info("Initiated active sequence cache to: %s", _sequence_active.name)

    if shot_active_id:
        _shot_active = Shot.by_id(shot_active_id)
        logger.info("Initiated active shot cache to: %s ", _shot_active.name)

    if asset_active_id:
        _asset_active = Asset.by_id(asset_active_id)
        logger.info("Initiated active asset cache to: %s", _asset_active.name)

    if asset_type_active_id:
        _asset_type_active = AssetType.by_id(asset_type_active_id)
        logger.info(
            "Initiated active asset type cache to: %s ", _asset_type_active.name
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
def load_post_handler_update_cache(dummy):
    clear_cache_variables()
    init_cache_variables()


# ---------REGISTER ----------


def register():
    # handlers
    bpy.app.handlers.load_post.append(load_post_handler_update_cache)


def unregister():
    # clear handlers
    bpy.app.handlers.load_post.remove(load_post_handler_update_cache)
