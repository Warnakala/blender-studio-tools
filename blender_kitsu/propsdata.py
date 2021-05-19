import re

from typing import Any, Dict, List, Tuple
from pathlib import Path

import bpy

from . import cache, prefs
from .logger import ZLoggerFactory

logger = ZLoggerFactory.getLogger(name=__name__)

# get functions for window manager properties
def _get_project_active(self):
    return cache.project_active_get().name


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


def _get_sequences(self: Any, context: bpy.types.Context) -> List[Tuple[str, str, str]]:
    addon_prefs = bpy.context.preferences.addons["blender_kitsu"].preferences
    project_active = cache.project_active_get()

    if not project_active or not addon_prefs.session.is_auth:
        return [("None", "None", "")]

    enum_list = [(s.name, s.name, "") for s in project_active.get_sequences_all()]
    return enum_list


def _gen_shot_preview(self: Any) -> str:
    addon_prefs = bpy.context.preferences.addons["blender_kitsu"].preferences
    shot_counter_increment = addon_prefs.shot_counter_increment
    shot_counter_digits = addon_prefs.shot_counter_digits
    shot_counter_start = self.shot_counter_start
    shot_pattern = addon_prefs.shot_pattern
    examples: List[str] = []
    sequence = self.sequence_enum
    var_project = (
        self.var_project_custom
        if self.var_use_custom_project
        else self.var_project_active
    )
    var_sequence = self.var_sequence_custom if self.var_use_custom_seq else sequence
    var_lookup_table = {"Sequence": var_sequence, "Project": var_project}

    for count in range(3):
        counter_number = shot_counter_start + (shot_counter_increment * count)
        counter = str(counter_number).rjust(shot_counter_digits, "0")
        var_lookup_table["Counter"] = counter
        examples.append(_resolve_pattern(shot_pattern, var_lookup_table))

    return " | ".join(examples) + "..."


def get_playblast_dir(self: Any) -> str:
    # .../110_rextoria/110_0030_A/110_0030_A.anim

    addon_prefs = prefs.addon_prefs_get(bpy.context)
    if not addon_prefs.is_playblast_root_valid:
        return ""

    seq = cache.sequence_active_get()
    shot = cache.shot_active_get()

    if not seq or not shot:
        return ""

    playblast_dir = (
        addon_prefs.playblast_root_path / seq.name / shot.name / f"{shot.name}.anim"
    )
    return playblast_dir.as_posix()


def get_playblast_file(self: Any) -> str:
    if not self.playblast_dir:
        return ""

    version = self.playblast_version
    shot_ative = cache.shot_active_get()
    # 070_0010_A.anim.v001.mp4
    file_name = f"{shot_ative.name}.anim.{version}.mp4"

    return Path(self.playblast_dir).joinpath(file_name).as_posix()


_active_category_cache = str


def reset_task_type(self: Any, context: bpy.types.Context) -> None:
    global _active_category_cache

    if self.category == _active_category_cache:
        return None

    cache.task_type_active_reset(context)
    _active_category_cache = self.category
    return None
