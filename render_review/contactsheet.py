from __future__ import annotations
from typing import Set, Union, Optional, List, Dict, Any, Tuple

import bpy

from render_review.geo import Point, Rectangle, Cell, Grid


class SequenceRect(Rectangle):
    def __init__(self, sequence: bpy.types.Sequence):
        self.sequence = sequence

    @property
    def orig_width(self) -> int:
        return self.sequence.elements[0].orig_width

    @property
    def orig_height(self) -> int:
        return self.sequence.elements[0].orig_height

    @property
    def width(self) -> int:
        return self.orig_width * self.scale_x

    @width.setter
    def width(self, value: int) -> None:
        scale_fac = value / self.orig_width
        self.scale_x = scale_fac

    @property
    def height(self) -> int:
        return self.orig_height * self.scale_y

    @width.setter
    def height(self, value: int) -> None:
        scale_fac = value / self.orig_height
        self.scale_y = scale_fac

    @property
    def x(self) -> int:
        return self.sequence.transform.offset_x

    @x.setter
    def x(self, value: int) -> None:
        self.sequence.transform.offset_x = int(value)

    @property
    def y(self) -> int:
        return self.sequence.transform.offset_y

    @x.setter
    def y(self, value: int) -> None:
        self.sequence.transform.offset_y = int(value)

    @property
    def scale_x(self):
        return self.sequence.transform.scale_x

    @scale_x.setter
    def scale_x(self, value: float):
        self.sequence.transform.scale_x = float(value)

    @property
    def scale_y(self):
        return self.sequence.transform.scale_y

    @scale_y.setter
    def scale_y(self, value: float):
        self.sequence.transform.scale_y = float(value)


class SequenceCell(Rectangle):
    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        sequence_rect: SequenceRect = None,
        keep_aspect: bool = True,
    ):
        Rectangle.__init__(self, x, y, width, height)
        self._sequence_rect: Optional[SequenceRect] = None

        # if sequence rect was supplied laod it
        if sequence_rect:
            self.load_sequence(sequence_rect, keep_ascpect=keep_aspect)

    def get_rect(self) -> Rectangle:
        return Rectangle(self.x, self.y, self.width, self.height)

    @property
    def sequence_rect(self) -> Optional[SequenceRect]:
        return self._sequence_rect

    def load_sequence(self, sequence_rect: SequenceRect, keep_ascpect: bool = True):
        self._sequence_rect = sequence_rect
        self._sequence_rect.fit_to_rect(self.get_rect(), keep_aspect=keep_ascpect)


class SequenceGrid(Grid):
    def __init__(
        self, x: int, y: int, width: int, height: int, row_count: int, coll_count: int
    ):
        Rectangle.__init__(self, x, y, width, height)
        self.rows: List[Rectangle] = []
        self.colls: List[Rectangle] = []
        self.cells: List[List[SequenceCell]] = []

        self._init_grid(row_count, coll_count)

    def _init_cells(self):
        self.cells.clear()

        for row_index, row in enumerate(self.rows):
            cell_y = row.y
            self.cells.append([])

            for coll in self.colls:
                cell_x = coll.x
                self.cells[row_index].append(
                    SequenceCell(cell_x, cell_y, coll.width, row.height)
                )

    def get_cells_for_row(self, row_index: int) -> List[SequenceCell]:
        return self.cells[row_index]

    def get_cell(self, row_index: int, coll_index: int) -> SequenceCell:
        return self.cells[row_index][coll_index]

    def load_sequences(self, sequences: List[bpy.types.Sequence]):
        counter: int = 0
        for row_idx in range(self.row_count()):
            for cell in self.get_cells_for_row(row_idx):
                try:
                    sequence = sequences[counter]
                except IndexError:
                    break
                # sequence.channel = counter
                sequence.blend_type = "ALPHA_OVER"
                # sequence.frame_final_start = 1001
                cell.load_sequence(SequenceRect(sequence))
                counter += 1
