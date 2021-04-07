import sys
from pathlib import Path
import bpy
from .auth import ZSession
from typing import Dict, Any, Optional
from .types import ZProject, ZSequence, ZShot, ZAsset, ZAssetType
from . import props


def zsession_get(context: bpy.types.Context) -> ZSession:
    """
    shortcut to get zsession from blezou addon preferences
    """
    prefs = context.preferences.addons["blezou"].preferences
    return prefs.session  # type: ignore


def prefs_get(context: bpy.types.Context) -> bpy.types.AddonPreferences:
    """
    shortcut to get blezou addon preferences
    """
    return context.preferences.addons["blezou"].preferences


def zsession_auth(context: bpy.types.Context) -> bool:
    """
    shortcut to check if zession is authorized
    """
    return zsession_get(context).is_auth()


def zproject_active_get() -> ZProject:
    return props._ZPROJECT_ACTIVE


def zproject_active_set_by_id(context: bpy.types.Context, entity_id: str) -> None:
    props._ZPROJECT_ACTIVE = ZProject.by_id(entity_id)
    context.scene.blezou.project_active_id = entity_id


def zproject_active_reset(context: bpy.types.Context) -> None:
    props._ZPROJECT_ACTIVE = ZProject()
    context.scene.blezou.project_active_id = ""


def zsequence_active_get() -> ZSequence:
    return props._ZSEQUENCE_ACTIVE


def zsequence_active_set_by_id(context: bpy.types.Context, entity_id: str) -> None:
    props._ZSEQUENCE_ACTIVE = ZSequence.by_id(entity_id)
    context.scene.blezou.sequence_active_id = entity_id


def zsequence_active_reset(context: bpy.types.Context) -> None:
    props._ZSEQUENCE_ACTIVE = ZSequence()
    context.scene.blezou.sequence_active_id = ""


def zshot_active_get() -> ZShot:
    return props._ZSHOT_ACTIVE


def zshot_active_set_by_id(context: bpy.types.Context, entity_id: str) -> None:
    props._ZSHOT_ACTIVE = ZShot.by_id(entity_id)
    context.scene.blezou.shot_active_id = entity_id


def zshot_active_reset(context: bpy.types.Context) -> None:
    props._ZSHOT_ACTIVE = ZShot()
    context.scene.blezou.shot_active_id = ""


def zasset_active_get() -> ZAsset:
    return props._ZASSET_ACTIVE


def zasset_active_set_by_id(context: bpy.types.Context, entity_id: str) -> None:
    props._ZASSET_ACTIVE = ZAsset.by_id(entity_id)
    context.scene.blezou.asset_active_id = entity_id


def zasset_active_reset(context: bpy.types.Context) -> None:
    props._ZASSET_ACTIVE = ZAsset()
    context.scene.blezou.asset_active_id = ""


def zasset_type_active_get() -> ZAssetType:
    return props._ZASSET_TYPE_ACTIVE


def zasset_type_active_set_by_id(context: bpy.types.Context, entity_id: str) -> None:
    props._ZASSET_TYPE_ACTIVE = ZAssetType.by_id(entity_id)
    context.scene.blezou.asset_type_active_id = entity_id


def zasset_type_active_reset(context: bpy.types.Context) -> None:
    props._ZASSET_TYPE_ACTIVE = ZAssetType()
    context.scene.blezou.asset_type_active_id = ""


def get_datadir() -> Path:
    """Returns a Path where persistent application data can be stored.

    # linux: ~/.local/share
    # macOS: ~/Library/Application Support
    # windows: C:/Users/<USER>/AppData/Roaming
    """

    home = Path.home()

    if sys.platform == "win32":
        return home / "AppData/Roaming"
    elif sys.platform == "linux":
        return home / ".local/share"
    elif sys.platform == "darwin":
        return home / "Library/Application Support"
