from typing import Any, Dict, List, Tuple, Union

import bpy

from blender_kitsu import cache, prefs
from blender_kitsu.logger import LoggerFactory
from blender_kitsu.types import ProjectList, TaskStatus, TaskType

logger = LoggerFactory.getLogger(name=__name__)


_sequence_enum_list: List[Tuple[str, str, str]] = []
_shot_enum_list: List[Tuple[str, str, str]] = []
_asset_types_enum_list: List[Tuple[str, str, str]] = []
_asset_enum_list: List[Tuple[str, str, str]] = []
_projects_list: List[Tuple[str, str, str]] = []
_task_types_enum_list: List[Tuple[str, str, str]] = []

_task_types_shots_enum_list: List[Tuple[str, str, str]] = []
_task_statuses_enum_list: List[Tuple[str, str, str]] = []


def get_projects_enum_list(
    self: bpy.types.Operator, context: bpy.types.Context
) -> List[Tuple[str, str, str]]:
    global _projects_list

    if not prefs.session_auth(context):
        return []

    projectlist = ProjectList()
    _projects_list.clear()
    _projects_list.extend(
        [(p.id, p.name, p.description or "") for p in projectlist.projects]
    )
    return _projects_list


def get_sequences_enum_list(
    self: bpy.types.Operator, context: bpy.types.Context
) -> List[Tuple[str, str, str]]:
    global _sequence_enum_list

    project_active = cache.project_active_get()
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

    zseq_active = cache.sequence_active_get()

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

    project_active = cache.project_active_get()
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

    project_active = cache.project_active_get()
    asset_type_active = cache.asset_type_active_get()

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
        shot_active = cache.shot_active_get()
        if not shot_active:
            return []
        items = [(t.id, t.name, "") for t in TaskType.all_shot_task_types()]

    if context.scene.kitsu.category == "ASSETS":
        asset_active = cache.asset_active_get()
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
