from __future__ import annotations
from typing import Set, Union, Optional, List, Dict, Any, Tuple
from pathlib import Path

import bpy

from contactsheet.geo import Point, Rectangle, Cell, Grid


class SequenceRect(Rectangle):
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

    # X
    def _get_x(self) -> int:
        return (
            self._canvas_x / 2 - (self.width / 2) + (self.sequence.transform.offset_x)
        )

    def _set_x(self, value: int) -> None:
        # to origin
        self.sequence.transform.offset_x = -(self._canvas_x / 2) + (self.width / 2)
        # plus value
        self.sequence.transform.offset_x += value

    # Y
    def _get_y(self) -> int:
        return (
            self._canvas_y / 2 - (self.height / 2) - (self.sequence.transform.offset_y)
        )

    def _set_y(self, value: int) -> None:
        # y in blender sqe goes up ^ + and down minus (confusing)
        # to origin
        self.sequence.transform.offset_y = (self._canvas_y / 2) - (self.height / 2)
        # minus value
        self.sequence.transform.offset_y -= value

    # WIDTH
    def _get_width(self) -> int:
        return self.orig_width * self.scale_x

    def _set_width(self, value: int) -> None:
        scale_fac = value / self.orig_width
        self.scale_x = scale_fac

    # HEIGHT
    def _get_height(self) -> int:
        return self.orig_height * self.scale_y

    def _set_height(self, value: int) -> None:
        scale_fac = value / self.orig_height
        self.scale_y = scale_fac

    # SCALE

    def _get_scale_x(self):
        return self.sequence.transform.scale_x

    def _get_scale_y(self):
        return self.sequence.transform.scale_y

    def _set_scale_x(self, factor: float) -> None:
        self.sequence.transform.scale_x = float(factor)

    def _set_scale_y(self, factor: float) -> None:
        self.sequence.transform.scale_y = float(factor)

    # FUNCTIONS
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
