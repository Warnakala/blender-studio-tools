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

from __future__ import annotations
from typing import Set, Union, Optional, List, Dict, Any, Tuple
from pathlib import Path

import bpy

from contactsheet.geo import Point, Rectangle, Cell, Grid


class SequenceRect(Rectangle):
    """
    Class that represents a Blender sequence strip as a rectangle. It
    inherits from Rectangle class and implements the _ methods so the
    Rectangle public interface works as excpected.
    """

    valid_types: List[str] = ["MOVIE", "IMAGE"]

    def __init__(self, sequence: bpy.types.Sequence):

        if sequence.type not in self.valid_types:
            raise ValueError(
                f"SequenceRect can only hold sequences of type {str(self.valid_types)}"
            )

        self._sequence: bpy.types.Sequence = sequence
        self._orig_x: int = sequence.transform.offset_x
        self._orig_y: int = sequence.transform.offset_y

    @property
    def sequence(self) -> bpy.types.Sequence:
        return self._sequence

    def _get_orig_width(self) -> int:
        return self.sequence.elements[0].orig_width

    def _get_orig_height(self) -> int:
        return self.sequence.elements[0].orig_height

    # X.
    def _get_x(self) -> int:
        return (
            self._canvas_x / 2 - (self.width / 2) + (self.sequence.transform.offset_x)
        )

    def _set_x(self, value: int) -> None:
        # To origin.
        self.sequence.transform.offset_x = -(self._canvas_x / 2) + (self.width / 2)
        # Plus value.
        self.sequence.transform.offset_x += value

    # Y.
    def _get_y(self) -> int:
        return (
            self._canvas_y / 2 - (self.height / 2) - (self.sequence.transform.offset_y)
        )

    def _set_y(self, value: int) -> None:
        # Y in blender sqe goes up ^ + and down minus (confusing)
        # to origin.
        self.sequence.transform.offset_y = (self._canvas_y / 2) - (self.height / 2)
        # Minus value.
        self.sequence.transform.offset_y -= value

    # Width.
    def _get_width(self) -> int:
        return self.orig_width * self.scale_x

    def _set_width(self, value: int) -> None:
        scale_fac = value / self.orig_width
        self.scale_x = scale_fac

    # Height.
    def _get_height(self) -> int:
        return self.orig_height * self.scale_y

    def _set_height(self, value: int) -> None:
        scale_fac = value / self.orig_height
        self.scale_y = scale_fac

    # Scale.

    def _get_scale_x(self):
        return self.sequence.transform.scale_x

    def _get_scale_y(self):
        return self.sequence.transform.scale_y

    def _set_scale_x(self, factor: float) -> None:
        self.sequence.transform.scale_x = float(factor)

    def _set_scale_y(self, factor: float) -> None:
        self.sequence.transform.scale_y = float(factor)

    # Functions.
    def copy(self) -> SequenceRect:
        if self.sequence.type == "IMAGE":
            strip = bpy.context.scene.sequence_editor.sequences.new_image(
                self.sequence.name,
                Path(self.sequence.directory)
                .joinpath(self.sequence.elements[0].filename)
                .as_posix(),
                self.sequence.channel + 1,
                self.sequence.frame_final_start,
            )
        elif self.sequence.type == "MOVIE":
            strip = bpy.context.scene.sequence_editor.sequences.new_movie(
                self.sequence.name,
                self.sequence.file,
                self.sequence.channel + 1,
                self.sequence.frame_final_start,
            )

        sequence_rect = SequenceRect(strip)
        sequence_rect.fit_to_rect(self)
        return sequence_rect

    @property
    def _canvas_x(self):
        return bpy.context.scene.render.resolution_x

    @property
    def _canvas_y(self):
        return bpy.context.scene.render.resolution_y
