# ***** BEGIN GPL LICENSE BLOCK *****
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
# ***** END GPL LICENCE BLOCK *****
#
# (c) 2021, Blender Foundation - Paul Golter

from typing import Dict, List, Set, Optional, Tuple, Any

import bpy


def _do_ranges_collide(range1: range, range2: range) -> bool:
    """Whether the two ranges collide with each other ."""
    # usual strip setup strip1(101, 120)|strip2(120, 130)|strip3(130, 140)
    # first and last frame can be the same for each strip
    range2 = range(range2.start + 1, range2.stop - 1)

    if not range1:
        return True  # empty range is subset of anything

    if not range2:
        return False  # non-empty range can't be subset of empty range

    if len(range1) > 1 and range1.step % range2.step:
        return False  # must have a single value or integer multiple step

    if range(range1.start + 1, range1.stop - 1) == range2:
        return True

    if range2.start in range1 or range2[-1] in range1:
        return True

    return range1.start in range2 or range1[-1] in range2


def get_occupied_ranges(context: bpy.types.Context) -> Dict[str, List[range]]:
    """
    Scans sequence editor and returns a dictionary. It contains a key for each channel
    and a list of ranges with the occupied frame ranges as values.
    """
    # {'1': [(101, 213), (300, 320)]}
    ranges: Dict[str, List[range]] = {}

    # populate ranges
    for strip in context.scene.sequence_editor.sequences_all:
        ranges.setdefault(str(strip.channel), [])
        ranges[str(strip.channel)].append(
            range(strip.frame_final_start, strip.frame_final_end + 1)
        )

    # sort ranges tuple list
    for channel in ranges:
        liste = ranges[channel]
        ranges[channel] = sorted(liste, key=lambda item: item.start)

    return ranges


def get_occupied_ranges_for_strips(sequences: List[bpy.types.Sequence]) -> List[range]:
    """
    Scans input list of sequences and returns a list of ranges that represent the occupied frame ranges.
    """
    ranges: List[range] = []

    # populate ranges
    for strip in sequences:
        ranges.append(range(strip.frame_final_start, strip.frame_final_end + 1))

    # sort ranges tuple list
    ranges.sort(key=lambda item: item.start)
    return ranges


def is_range_occupied(range_to_check: range, occupied_ranges: List[range]) -> bool:
    for r in occupied_ranges:
        # range(101, 150)
        if _do_ranges_collide(range_to_check, r):
            return True
        continue
    return False
