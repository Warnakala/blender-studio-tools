from typing import Set, Union, Optional, List, Dict, Any, Tuple
from pathlib import Path

import bpy

from contactsheet import checksqe
from contactsheet.log import LoggerFactory

logger = LoggerFactory.getLogger(name=__name__)


def get_valid_cs_sequences(
    context: bpy.types.Context, sequence_list: List[bpy.types.Sequence] = []
) -> List[bpy.types.Sequence]:

    sequences: List[bpy.types.Sequence] = []

    if sequence_list:
        sequences = sequence_list
    else:
        sequences = (
            context.selected_sequences or context.scene.sequence_editor.sequences_all
        )

    valid_sequences = [
        s for s in sequences if s.type in ["MOVIE", "IMAGE"] and not s.mute
    ]

    return valid_sequences


def get_sqe_editor(context: bpy.types.Context) -> Optional[bpy.types.Area]:
    sqe_editor = None

    for area in context.screen.areas:
        if area.type == "SEQUENCE_EDITOR":
            sqe_editor = area

    return sqe_editor


def fit_frame_range_to_strips(
    context: bpy.types.Context, strips: Optional[List[bpy.types.Sequence]] = None
) -> Tuple[int, int]:
    def get_sort_tuple(strip: bpy.types.Sequence) -> Tuple[int, int]:
        return (strip.frame_final_start, strip.frame_final_duration)

    if not strips:
        strips = context.scene.sequence_editor.sequences_all

    if not strips:
        return (0, 0)

    strips = list(strips)
    strips.sort(key=get_sort_tuple)

    context.scene.frame_start = strips[0].frame_final_start
    context.scene.frame_end = strips[-1].frame_final_end

    return (context.scene.frame_start, context.scene.frame_end)


def get_top_level_valid_strips_continious(
    context: bpy.types.Context,
) -> List[bpy.types.Sequence]:

    sequences_tmp = get_valid_cs_sequences(
        context, sequence_list=list(context.scene.sequence_editor.sequences_all)
    )

    sequences_tmp.sort(key=lambda s: (s.channel, s.frame_final_start), reverse=True)
    sequences: List[bpy.types.Sequence] = []

    for strip in sequences_tmp:

        occ_ranges = checksqe.get_occupied_ranges_for_strips(sequences)
        s_range = range(strip.frame_final_start, strip.frame_final_end + 1)

        if not checksqe.is_range_occupied(s_range, occ_ranges):
            sequences.append(strip)

    return sequences
