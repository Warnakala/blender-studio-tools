from typing import Any, Dict, Optional

import bpy

from . import prefs, props
from .auth import ZSession
from .types import ZAsset, ZAssetType, ZProject, ZSequence, ZShot

VALID_STRIP_TYPES = {"MOVIE", "COLOR"}


def zsession_get(context: bpy.types.Context) -> ZSession:
    """
    shortcut to get zsession from blezou addon preferences
    """
    prefs = context.preferences.addons["blezou"].preferences
    return prefs.session  # type: ignore


def addon_prefs_get(context: bpy.types.Context) -> bpy.types.AddonPreferences:
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
    return prefs._zproject_active


def zproject_active_set_by_id(context: bpy.types.Context, entity_id: str) -> None:
    prefs._zproject_active = ZProject.by_id(entity_id)
    addon_prefs_get(context).project_active_id = entity_id


def zproject_active_reset(context: bpy.types.Context) -> None:
    prefs._zproject_active = ZProject()
    addon_prefs_get(context).project_active_id = ""


def zsequence_active_get() -> ZSequence:
    return props._zsequence_active


def zsequence_active_set_by_id(context: bpy.types.Context, entity_id: str) -> None:
    props._zsequence_active = ZSequence.by_id(entity_id)
    context.scene.blezou.sequence_active_id = entity_id


def zsequence_active_reset(context: bpy.types.Context) -> None:
    props._zsequence_active = ZSequence()
    context.scene.blezou.sequence_active_id = ""


def zshot_active_get() -> ZShot:
    return props._zshot_active


def zshot_active_set_by_id(context: bpy.types.Context, entity_id: str) -> None:
    props._zshot_active = ZShot.by_id(entity_id)
    context.scene.blezou.shot_active_id = entity_id


def zshot_active_reset(context: bpy.types.Context) -> None:
    props._zshot_active = ZShot()
    context.scene.blezou.shot_active_id = ""


def zasset_active_get() -> ZAsset:
    return props._zasset_active


def zasset_active_set_by_id(context: bpy.types.Context, entity_id: str) -> None:
    props._zasset_active = ZAsset.by_id(entity_id)
    context.scene.blezou.asset_active_id = entity_id


def zasset_active_reset(context: bpy.types.Context) -> None:
    props._zasset_active = ZAsset()
    context.scene.blezou.asset_active_id = ""


def zasset_type_active_get() -> ZAssetType:
    return props._zasset_type_active


def zasset_type_active_set_by_id(context: bpy.types.Context, entity_id: str) -> None:
    props._zasset_type_active = ZAssetType.by_id(entity_id)
    context.scene.blezou.asset_type_active_id = entity_id


def zasset_type_active_reset(context: bpy.types.Context) -> None:
    props._zasset_type_active = ZAssetType()
    context.scene.blezou.asset_type_active_id = ""


def ui_redraw() -> None:
    """
    Forces blender to redraw the UI.
    """
    for screen in bpy.data.screens:
        for area in screen.areas:
            area.tag_redraw()
