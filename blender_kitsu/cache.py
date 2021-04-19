import bpy

from bpy.app.handlers import persistent
from .types import ZProject, ZSequence, ZShot, ZAsset, ZAssetType
from .logger import ZLoggerFactory

logger = ZLoggerFactory.getLogger(name=__name__)

# CACHE VARIABLES
# used to cache active entitys to prevent a new api request when read only
_zproject_active: ZProject = ZProject()
_zsequence_active: ZSequence = ZSequence()
_zshot_active: ZShot = ZShot()
_zasset_active: ZAsset = ZAsset()
_zasset_type_active: ZAssetType = ZAssetType()

_cache_initialized: bool = False


def _addon_prefs_get(context: bpy.types.Context) -> bpy.types.AddonPreferences:
    """
    shortcut to get blender_kitsu addon preferences
    """
    return context.preferences.addons["blender_kitsu"].preferences


def zproject_active_get() -> ZProject:
    global _zproject_active

    return _zproject_active


def zproject_active_set_by_id(context: bpy.types.Context, entity_id: str) -> None:
    global _zproject_active

    _zproject_active = ZProject.by_id(entity_id)
    _addon_prefs_get(context).project_active_id = entity_id


def zproject_active_reset(context: bpy.types.Context) -> None:
    global _zproject_active
    _zproject_active = ZProject()
    _addon_prefs_get(context).project_active_id = ""


def zsequence_active_get() -> ZSequence:
    return _zsequence_active


def zsequence_active_set_by_id(context: bpy.types.Context, entity_id: str) -> None:
    global _zsequence_active

    _zsequence_active = ZSequence.by_id(entity_id)
    context.scene.kitsu.sequence_active_id = entity_id


def zsequence_active_reset(context: bpy.types.Context) -> None:
    global _zsequence_active

    _zsequence_active = ZSequence()
    context.scene.kitsu.sequence_active_id = ""


def zshot_active_get() -> ZShot:
    global _zshot_active

    return _zshot_active


def zshot_active_set_by_id(context: bpy.types.Context, entity_id: str) -> None:
    global _zshot_active

    _zshot_active = ZShot.by_id(entity_id)
    context.scene.kitsu.shot_active_id = entity_id


def zshot_active_reset(context: bpy.types.Context) -> None:
    global _zshot_active

    _zshot_active = ZShot()
    context.scene.kitsu.shot_active_id = ""


def zasset_active_get() -> ZAsset:
    global _zasset_active

    return _zasset_active


def zasset_active_set_by_id(context: bpy.types.Context, entity_id: str) -> None:
    global _zasset_active

    _zasset_active = ZAsset.by_id(entity_id)
    context.scene.kitsu.asset_active_id = entity_id


def zasset_active_reset(context: bpy.types.Context) -> None:
    global _zasset_active

    _zasset_active = ZAsset()
    context.scene.kitsu.asset_active_id = ""


def zasset_type_active_get() -> ZAssetType:
    global _zasset_type_active

    return _zasset_type_active


def zasset_type_active_set_by_id(context: bpy.types.Context, entity_id: str) -> None:
    global _zasset_type_active

    _zasset_type_active = ZAssetType.by_id(entity_id)
    context.scene.kitsu.asset_type_active_id = entity_id


def zasset_type_active_reset(context: bpy.types.Context) -> None:
    global _zasset_type_active

    _zasset_type_active = ZAssetType()
    context.scene.kitsu.asset_type_active_id = ""


def init_cache_variables() -> None:
    global _zproject_active
    global _zsequence_active
    global _zshot_active
    global _zasset_active
    global _zasset_type_active
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
        _zproject_active = ZProject.by_id(project_active_id)
        logger.info("Initiated Active Project Cache to: %s", _zproject_active.name)

    if sequence_active_id:
        _zsequence_active = ZSequence.by_id(sequence_active_id)
        logger.info("Initiated active sequence cache to: %s", _zsequence_active.name)

    if shot_active_id:
        _zshot_active = ZShot.by_id(shot_active_id)
        logger.info("Initiated active shot cache to: %s ", _zshot_active.name)

    if asset_active_id:
        _zasset_active = ZAsset.by_id(asset_active_id)
        logger.info("Initiated active asset cache to: %s", _zasset_active.name)

    if asset_type_active_id:
        _zasset_type_active = ZAssetType.by_id(asset_type_active_id)
        logger.info(
            "Initiated active asset type cache to: %s ", _zasset_type_active.name
        )

    _cache_initialized = True


def clear_cache_variables():
    global _zproject_active
    global _zsequence_active
    global _zshot_active
    global _zasset_active
    global _zasset_type_active
    global _cache_initialized

    _zshot_active = ZShot()
    logger.info("Cleared active shot cache")

    _zasset_active = ZAsset()
    logger.info("Cleared active asset cache")

    _zsequence_active = ZSequence()
    logger.info("Cleared active aequence cache")

    _zasset_type_active = ZAssetType()
    logger.info("Cleared active asset type cache")

    _zproject_active = ZProject()
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
