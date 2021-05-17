import re
from typing import Any, Dict, List, Tuple, Union
from pathlib import Path

import bpy
from bpy.app.handlers import persistent

from . import cache, prefs, bkglobals
from .models import FolderListModel
from .logger import ZLoggerFactory
from .types import Sequence, ProjectList

logger = ZLoggerFactory.getLogger(name=__name__)

_sqe_not_linked: List[Tuple[str, str, str]] = []
_sqe_duplicates: List[Tuple[str, str, str]] = []
_sqe_multi_project: List[Tuple[str, str, str]] = []

_sequence_enum_list: List[Tuple[str, str, str]] = []
_shot_enum_list: List[Tuple[str, str, str]] = []
_asset_types_enum_list: List[Tuple[str, str, str]] = []
_asset_enum_list: List[Tuple[str, str, str]] = []
_projects_list: List[Tuple[str, str, str]] = []


VERSION_DIR_MODEL = FolderListModel()
_versions_enum_list: List[Tuple[str, str, str]] = []
_version_dir_model_init: bool = False


def _sqe_get_not_linked(self, context):
    return _sqe_not_linked


def _sqe_get_duplicates(self, context):
    return _sqe_duplicates


def _sqe_get_multi_project(self, context):
    return _sqe_multi_project


def _sqe_update_not_linked(context: bpy.types.Context) -> List[Tuple[str, str, str]]:
    """get all strips that are initialized but not linked yet"""
    enum_list = []

    if context.selected_sequences:
        strips = context.selected_sequences
    else:
        strips = context.scene.sequence_editor.sequences_all

    for strip in strips:
        if strip.kitsu.initialized and not strip.kitsu.linked:
            enum_list.append((strip.name, strip.name, ""))

    return enum_list


def _sqe_update_duplicates(context: bpy.types.Context) -> List[Tuple[str, str, str]]:
    """get all strips that are initialized but not linked yet"""
    enum_list = []
    data_dict = {}
    if context.selected_sequences:
        strips = context.selected_sequences
    else:
        strips = context.scene.sequence_editor.sequences_all

    # create data dict that holds all shots ids and the corresponding strips that are linked to it
    for i in range(len(strips)):

        if strips[i].kitsu.linked:
            # get shot_id, shot_name, create entry in data_dict if id not existent
            shot_id = strips[i].kitsu.shot_id
            shot_name = strips[i].kitsu.shot_name
            if shot_id not in data_dict:
                data_dict[shot_id] = {"name": shot_name, "strips": []}

            # append i to strips list
            if strips[i] not in set(data_dict[shot_id]["strips"]):
                data_dict[shot_id]["strips"].append(strips[i])

            # comparet to all other strip
            for j in range(i + 1, len(strips)):
                if shot_id == strips[j].kitsu.shot_id:
                    data_dict[shot_id]["strips"].append(strips[j])

    # convert in data strucutre for enum property
    for shot_id, data in data_dict.items():
        if len(data["strips"]) > 1:
            enum_list.append(("", data["name"], shot_id))
            for strip in data["strips"]:
                enum_list.append((strip.name, strip.name, ""))

    return enum_list


def _sqe_update_multi_project(context: bpy.types.Context) -> List[Tuple[str, str, str]]:
    """get all strips that are initialized but not linked yet"""
    enum_list: List[Tuple[str, str, str]] = []
    data_dict: Dict[str, Any] = {}

    if context.selected_sequences:
        strips = context.selected_sequences
    else:
        strips = context.scene.sequence_editor.sequences_all

    # create data dict that holds project names as key and values the corresponding sequence strips
    for strip in strips:
        if strip.kitsu.linked:
            project = strip.kitsu.project_name
            if project not in data_dict:
                data_dict[project] = []

            # append i to strips list
            if strip not in set(data_dict[project]):
                data_dict[project].append(strip)

    # convert in data strucutre for enum property
    for project, strips in data_dict.items():
        enum_list.append(("", project, ""))
        for strip in strips:
            enum_list.append((strip.name, strip.name, ""))

    return enum_list


def _resolve_pattern(pattern: str, var_lookup_table: Dict[str, str]) -> str:

    matches = re.findall(r"\<(\w+)\>", pattern)
    matches = list(set(matches))
    # if no variable detected just return value
    if len(matches) == 0:
        return pattern
    else:
        result = pattern
        for to_replace in matches:
            if to_replace in var_lookup_table:
                to_insert = var_lookup_table[to_replace]
                result = result.replace("<{}>".format(to_replace), to_insert)
            else:
                logger.warning(
                    "Failed to resolve variable: %s not defined!", to_replace
                )
                return ""
        return result


def _get_projects(
    self: bpy.types.Operator, context: bpy.types.Context
) -> List[Tuple[str, str, str]]:
    global _projects_list

    if not prefs.zsession_auth(context):
        return []

    projectlist = ProjectList()
    _projects_list.clear()
    _projects_list.extend(
        [(p.id, p.name, p.description or "") for p in projectlist.projects]
    )
    return _projects_list


def _get_sequences(
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


def _get_shots_from_op_enum(
    self: bpy.types.Operator, context: bpy.types.Context
) -> List[Tuple[str, str, str]]:
    global _shot_enum_list

    if not self.sequence_enum:
        return []

    zseq_active = Sequence.by_id(self.sequence_enum)

    _shot_enum_list.clear()
    _shot_enum_list.extend(
        [(s.id, s.name, s.description or "") for s in zseq_active.get_all_shots()]
    )
    return _shot_enum_list


def _get_shots_from_active_seq(
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


def _get_assetypes(
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


def _get_assets_from_active_asset_type(
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


def init_version_dir_model(
    context: bpy.types.Context,
) -> None:

    global VERSION_DIR_MODEL
    global _version_dir_model_init
    addon_prefs = prefs.addon_prefs_get(context)

    # is None if invalid
    if not addon_prefs.playblast_version_dir:
        logger.error(
            "Failed to initialize version directory model. Invalid path. Check addon preferences."
        )
        return

    version_dir = Path(addon_prefs.playblast_version_dir)

    VERSION_DIR_MODEL.reset()
    VERSION_DIR_MODEL.root_path = version_dir

    if not VERSION_DIR_MODEL.items:
        VERSION_DIR_MODEL.append_item("v001")
        # update playblast_version prop
        context.scene.kitsu.playblast_version = "v001"

    else:
        # update playblast_version prop
        context.scene.kitsu.playblast_version = VERSION_DIR_MODEL.items[0]

    _version_dir_model_init = True


def get_version(str_value: str, format: type = str) -> Union[str, int, None]:
    match = re.search(bkglobals.VERSION_PATTERN, str_value)
    if match:
        version = match.group()
        if format == str:
            return version
        if format == int:
            return int(version.replace("v", ""))
    return None


def add_version_increment(context: bpy.types.Context) -> str:

    # init model if it did not happen
    if not _version_dir_model_init:
        init_version_dir_model(context)

    items = VERSION_DIR_MODEL.items  # should be already sorted
    versions = [get_version(item) for item in items if get_version(item)]

    if len(versions) > 0:
        latest_version = items[0]
        increment = "v{:03}".format(int(latest_version.replace("v", "")) + 1)
    else:
        increment = "v001"

    VERSION_DIR_MODEL.append_item(increment)
    return increment


def get_versions_enum_list(
    self: Any,
    context: bpy.types.Context,
) -> List[Tuple[str, str, str]]:

    global _versions_enum_list
    global VERSION_DIR_MODEL
    global init_version_dir_model

    # init model if it did not happen
    if not _version_dir_model_init:
        init_version_dir_model(context)

    # clear all versions in enum list
    _versions_enum_list.clear()
    _versions_enum_list.extend(VERSION_DIR_MODEL.items_as_enum_list)

    return _versions_enum_list


def add_version_custom(custom_version: str) -> None:
    global _versions_enum_list
    global VERSION_DIR_MODEL

    VERSION_DIR_MODEL.append_item(custom_version)


@persistent
def load_post_handler_init_version_model(dummy: Any) -> None:
    init_version_dir_model(bpy.context)


# ---------REGISTER ----------


def register():
    # init model
    init_version_dir_model(bpy.context)

    # handlers
    bpy.app.handlers.load_post.append(load_post_handler_init_version_model)


def unregister():
    # clear handlers
    bpy.app.handlers.load_post.remove(load_post_handler_init_version_model)
