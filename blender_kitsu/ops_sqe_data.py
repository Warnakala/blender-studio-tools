import re
from typing import Any, Dict, List, Tuple, Union

import bpy

from .logger import ZLoggerFactory
from .types import Sequence

logger = ZLoggerFactory.getLogger(name=__name__)

_sqe_shot_enum_list: List[Tuple[str, str, str]] = []
_sqe_not_linked: List[Tuple[str, str, str]] = []
_sqe_duplicates: List[Tuple[str, str, str]] = []
_sqe_multi_project: List[Tuple[str, str, str]] = []


def sqe_get_not_linked(self, context):
    return _sqe_not_linked


def sqe_get_duplicates(self, context):
    return _sqe_duplicates


def sqe_get_multi_project(self, context):
    return _sqe_multi_project


def sqe_update_not_linked(context: bpy.types.Context) -> List[Tuple[str, str, str]]:
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


def sqe_update_duplicates(context: bpy.types.Context) -> List[Tuple[str, str, str]]:
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


def sqe_update_multi_project(context: bpy.types.Context) -> List[Tuple[str, str, str]]:
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


def resolve_pattern(pattern: str, var_lookup_table: Dict[str, str]) -> str:

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


def get_shots_enum_for_link_shot_op(
    self: bpy.types.Operator, context: bpy.types.Context
) -> List[Tuple[str, str, str]]:
    global _sqe_shot_enum_list

    if not self.sequence_enum:
        return []

    zseq_active = Sequence.by_id(self.sequence_enum)

    _sqe_shot_enum_list.clear()
    _sqe_shot_enum_list.extend(
        [(s.id, s.name, s.description or "") for s in zseq_active.get_all_shots()]
    )
    return _sqe_shot_enum_list
