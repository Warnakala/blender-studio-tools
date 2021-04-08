import bpy
import re
from typing import List, Tuple, Optional, Dict, Any
from .logger import ZLoggerFactory

logger = ZLoggerFactory.getLogger(name=__name__)

_SQE_NOT_LINKED: List[Tuple[str, str, str]] = []
_SQE_DUPLCIATES: List[Tuple[str, str, str]] = []
_SQE_MULTI_PROJECT: List[Tuple[str, str, str]] = []


def _sqe_get_not_linked(self, context):
    return _SQE_NOT_LINKED


def _sqe_get_duplicates(self, context):
    return _SQE_DUPLCIATES


def _sqe_get_multi_project(self, context):
    return _SQE_MULTI_PROJECT


def _sqe_update_not_linked(context: bpy.types.Context) -> List[Tuple[str, str, str]]:
    """get all strips that are initialized but not linked yet"""
    enum_list = []

    if context.selected_sequences:
        strips = context.selected_sequences
    else:
        strips = context.scene.sequence_editor.sequences_all

    for strip in strips:
        if strip.blezou.initialized and not strip.blezou.linked:
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

        if strips[i].blezou.linked:
            # get shot_id, shot_name, create entry in data_dict if id not existent
            shot_id = strips[i].blezou.shot_id
            shot_name = strips[i].blezou.shot_name
            if shot_id not in data_dict:
                data_dict[shot_id] = {"name": shot_name, "strips": []}

            # append i to strips list
            if strips[i] not in set(data_dict[shot_id]["strips"]):
                data_dict[shot_id]["strips"].append(strips[i])

            # comparet to all other strip
            for j in range(i + 1, len(strips)):
                if shot_id == strips[j].blezou.shot_id:
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
        if strip.blezou.linked:
            project = strip.blezou.project_name
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
                logger.warning(f"Failed to resolve variable: {to_replace} not defined!")
                return ""
        return result
