from __future__ import annotations
from typing import Set, Union, Optional, List, Dict, Any, Tuple
from enum import Enum


class Align(Enum):
    CENTER = (1,)
    TOP = 2
    BOTTOM = 3


class Point:
    def __init__(self, x: int, y: int):
        self._x = int(x)
        self._y = int(y)

    @property
    def x(self) -> int:
        return self._x

    @property
    def y(self) -> int:
        return self._y

    def __add__(self, other: Point):
        return Point(self.x + other.x, self.y + other.y)

    def __iadd__(self, other: Point):
        self.x + other.x
        self.y + other.y
        return self

    def __sub__(self, other: Point):
        return Point(self.x - other.x, self.y - other.y)

    def __isub__(self, other: Point):
        self.x - other.x
        self.y - other.y
        return self

    def __repr__(self) -> str:
        return f"Point(x: {self.x}, y: {self.y})"


class RectCoords:
    def __init__(self, x1: Point, x2: Point, y1: Point, y2: Point):
        self._x1 = x1
        self._x2 = x2
        self._y1 = y1
        self._y2 = y2

    @property
    def x1(self) -> Point:
        return self._x1

    @property
    def x2(self) -> Point:
        return self._x2

    @property
    def y1(self) -> Point:
        return self._y1

    @property
    def y2(self) -> Point:
        return self._y2

    @property
    def top_left(self) -> Point:
        return self._x1

    @property
    def top_right(self) -> Point:
        return self._x2

    @property
    def bot_left(self) -> Point:
        return self._y1

    @property
    def bot_right(self) -> Point:
        return self._y2


class Rectangle:
    def __init__(self, x: int, y: int, width: int, height: int):
        self._width = int(width)
        self._height = int(height)
        self._x = int(x)
        self._y = int(y)
        self._orig_width = self._width
        self._orig_height = self._height
        self._orig_x = self._x
        self._orig_y = self._y

    @property
    def x(self) -> int:
        return self._x

    @x.setter
    def x(self, value: int) -> None:
        self._x = int(value)

    @property
    def y(self) -> int:
        return self._y

    @y.setter
    def y(self, value: int) -> None:
        self._y = int(value)

    @property
    def width(self) -> int:
        return self._width

    @width.setter
    def width(self, value: int) -> None:
        self._width = int(value)

    @property
    def height(self) -> int:
        return self._height

    @height.setter
    def height(self, value: int) -> None:
        self._height = int(value)

    @property
    def area(self) -> int:
        return self.width * self.height

    @property
    def center(self) -> Point:
        center_x = int(self.x + (0.5 * self.width))
        center_y = int(self.y + (0.5 * self.height))
        return Point(center_x, center_y)

    @property
    def position(self) -> Point:
        return Point(self.x, self.y)

    @position.setter
    def position(self, pos: Point) -> None:
        self.x = pos.x
        self.y = pos.y

    @property
    def coords(self) -> RectCoords:
        top_left = self.position
        top_right = Point(self.x + self.width, self.y)
        bot_left = Point(self.x, self.y + self.height)
        bot_right = Point(self.x + self.width, self.y + self.height)
        return RectCoords(top_left, top_right, bot_left, bot_right)

    def resize_to_rect(
        self,
        rect: Rectangle,
        keep_aspect: bool = True,
        align: Align = Align.CENTER,
    ):
        if keep_aspect:
            # fit width
            # width height
            scale_fac = rect.width / self.width
            self.width = rect.width
            self.height = int(self.height * scale_fac)

            # pos
            self.position = rect.position

            if align == Align.CENTER:
                # y offset to center it
                height_diff = rect.height - self.height
                self.y += int(height_diff / 2)

            elif align == Align.TOP:
                self.y == rect.y

            elif align == Align.BOTTOM:
                height_diff = rect.height - self.height
                self.y = rect.y + height_diff

        else:
            # copy all transforms
            self.width = rect.width
            self.height = rect.height
            self.position = rect.position

    def reset_transform(self):
        self.x = self._orig_x
        self.y = self._orig_y
        self.width = self._orig_width
        self.height = self._orig_height

    def copy(self) -> Rectangle:
        return Rectangle(self.x, self.y, self.width, self.height)

    def __repr__(self) -> str:
        return f"Rectangle(x: {self.x}, y: {self.y}, width: {self.width}, height: {self.height})"


class Cell(Rectangle):
    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        rect: Rectangle = None,
        keep_aspect: bool = True,
        align: Align = Align.CENTER,
    ):
        Rectangle.__init__(self, x, y, width, height)
        self._keep_aspect = keep_aspect
        self._align = align

        if rect:
            self.place_rect(rect, keep_ascpect=keep_aspect, align=align)
        else:
            self._rect = Rectangle(x, y, width, height)

    def get_cell_rect(self) -> Rectangle:
        return Rectangle(self.x, self.y, self.width, self.height)

    @property
    def rect(self) -> Rectangle:
        return self._rect

    def place_rect(
        self, rect: Rectangle, keep_ascpect: bool = True, align: Align = Align.CENTER
    ):
        self._rect = rect
        self._rect.resize_to_rect(
            self.get_cell_rect(), keep_aspect=keep_ascpect, align=align
        )
        self._keep_aspect = keep_ascpect
        self._align = align

    def copy(self) -> Cell:
        return Cell(
            self.x,
            self.y,
            self.width,
            self.height,
            self.rect,
            keep_aspect=self._keep_aspect,
            align=self._align,
        )


class Grid(Rectangle):
    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        row_count: int,
        coll_count: int,
        cell_rect: Rectangle = Rectangle(0, 0, 0, 0),
        align: Align = Align.CENTER,
    ) -> None:

        Rectangle.__init__(self, x, y, width, height)
        self.rows: List[Rectangle] = []
        self.colls: List[Rectangle] = []
        self.cells: List[List[Cell]] = []

        self._init_grid(
            row_count,
            coll_count,
            cell_rect,
            align,
        )

    def _init_grid(
        self,
        row_count: int,
        coll_count: int,
        cell_rect: Rectangle,
        align: Align,
    ) -> None:

        row_height: int = int(self.height / row_count)
        coll_width: int = int(self.width / coll_count)

        self._init_rows(row_height, row_count)
        self._init_colls(coll_width, coll_count)
        self._init_cells(cell_rect, align)

    def _init_rows(self, row_height: int, row_count: int) -> None:
        self.rows = [
            Rectangle(self.x, self.y + (row_height * row_idx), self.width, row_height)
            for row_idx in range(row_count)
        ]

    def _init_colls(self, coll_width: int, coll_count: int) -> None:
        self.colls = [
            Rectangle(self.x + (coll_width * coll_idx), self.y, coll_width, self.height)
            for coll_idx in range(coll_count)
        ]

    def _init_cells(self, cell_rect: Rectangle, align: Align) -> None:
        self.cells.clear()
        for row_index, row in enumerate(self.rows):
            cell_y = row.y
            self.cells.append([])

            for coll in self.colls:
                cell_x = coll.x

                # if cell_rect was not specified use dimensions of cell
                if cell_rect.width == 0 and cell_rect.height == 0:
                    cell_rect.width = coll.width
                    cell_rect.height = row.height

                # make copy to have each cell individual instance
                cell_rect_instance = cell_rect.copy()

                self.cells[row_index].append(
                    Cell(
                        cell_x,
                        cell_y,
                        coll.width,
                        row.height,
                        cell_rect_instance,
                        align=align,
                    )
                )

    def get_cells_for_row(self, row_index: int) -> List[Cell]:
        return self.cells[row_index]

    def get_cell(self, row_index: int, coll_index: int) -> Cell:
        return self.cells[row_index][coll_index]

    @property
    def row_height(self) -> float:
        return self.height / self.row_count()

    @property
    def coll_width(self) -> float:
        return self.width / self.coll_count()

    def row_count(self) -> int:
        return len(self.rows)

    def coll_count(self) -> int:
        return len(self.colls)

    def place_rects(
        self,
        rects: List[Rectangle],
        keep_aspect: bool = True,
        align: Align = Align.CENTER,
    ):
        counter: int = 0
        for row_idx in range(self.row_count()):
            for cell in self.get_cells_for_row(row_idx):
                try:
                    rect = [counter]
                except IndexError:
                    break
                cell.place_rect()
                counter += 1
