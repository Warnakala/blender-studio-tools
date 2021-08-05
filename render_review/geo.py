from __future__ import annotations
import math
from typing import Set, Union, Optional, List, Dict, Any, Tuple
from enum import Enum


class Align(Enum):
    NO = 1
    CENTER = 2
    TOP = 3
    BOTTOM = 4


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
        self._width: int = int(width)
        self._height: int = int(height)
        self._x: int = int(x)
        self._y: int = int(y)
        self._orig_width: int = self._width
        self._orig_height: int = self._height
        self._orig_x: int = self._x
        self._orig_y: int = self._y
        self._scale_x: float = 1.0
        self._scale_y: float = 1.0

    # X
    @property
    def x(self) -> int:
        return self._get_x()

    def _get_x(self) -> int:
        return self._x

    @x.setter
    def x(self, value: int) -> None:
        return self._set_x(value)

    def _set_x(self, value: int) -> None:
        self._x = int(value)

    @property
    def orig_x(self) -> int:
        return self._get_orig_x()

    def _get_orig_x(self) -> int:
        return self._orig_x

    # Y
    @property
    def y(self) -> int:
        return self._get_y()

    def _get_y(self) -> int:
        return self._y

    @y.setter
    def y(self, value: int) -> None:
        return self._set_y(value)

    def _set_y(self, value: int) -> None:
        self._y = int(value)

    @property
    def orig_y(self) -> int:
        return self._get_orig_y()

    def _get_orig_y(self) -> int:
        return self._orig_y

    # WIDTH
    @property
    def width(self) -> int:
        return self._get_width()

    def _get_width(self) -> int:
        return self._width

    @width.setter
    def width(self, value: int) -> None:
        return self._set_width(value)

    def _set_width(self, value: int) -> None:
        self._width = int(value)

    @property
    def orig_width(self) -> int:
        return self._get_orig_width()

    def _get_orig_width(self) -> int:
        return self._orig_width

    # HEIGHT
    @property
    def height(self) -> int:
        return self._get_height()

    def _get_height(self) -> int:
        return self._height

    @height.setter
    def height(self, value: int) -> None:
        return self._set_height(value)

    def _set_height(self, value: int) -> None:
        self._height = int(value)

    @property
    def orig_height(self) -> int:
        return self._get_orig_height()

    def _get_orig_height(self) -> int:
        return self._orig_height

    # SCALE

    @property
    def scale_x(self):
        return self._get_scale_x()

    def _get_scale_x(self):
        return self._scale_x

    @scale_x.setter
    def scale_x(self, factor: float) -> None:
        return self._set_scale_x(factor)

    def _set_scale_x(self, factor: float) -> None:
        new_width = self.width * float(factor)
        self.x += self.width / 2 - new_width / 2
        self.width = new_width

    @property
    def scale_y(self):
        return self._get_scale_y()

    def _get_scale_y(self):
        return self._scale_y

    @scale_y.setter
    def scale_y(self, factor: float) -> None:
        return self._set_scale_y(factor)

    def _set_scale_y(self, factor: float) -> None:
        new_height = self.height * float(factor)
        self.y += self.height / 2 - new_height / 2
        self.height = new_height

    def scale(self, factor: float) -> None:
        self.scale_x *= factor
        self.scale_y *= factor

    # ASPECT
    @property
    def aspect_ratio(self) -> float:
        return self.width / self.height

    # AREA
    @property
    def area(self) -> int:
        return self.width * self.height

    # CENTER
    @property
    def center(self) -> Point:
        center_x = int(self.x + (0.5 * self.width))
        center_y = int(self.y + (0.5 * self.height))
        return Point(center_x, center_y)

    # POSITION
    @property
    def position(self) -> Point:
        return Point(self.x, self.y)

    @position.setter
    def position(self, pos: Point) -> None:
        self.x = pos.x
        self.y = pos.y

    # COORDS
    @property
    def coords(self) -> RectCoords:
        top_left = self.position
        top_right = Point(self.x + self.width, self.y)
        bot_left = Point(self.x, self.y + self.height)
        bot_right = Point(self.x + self.width, self.y + self.height)
        return RectCoords(top_left, top_right, bot_left, bot_right)

    # FUNCTIONS
    def fit_to_rect(
        self,
        rect: Rectangle,
        keep_aspect: bool = True,
        align: Align = Align.CENTER,
        keep_offset: bool = False,
    ):
        # if self.aspect_ratio > rect.aspect_ratio:
        # -> fit self by width
        # else fit bei height

        # width height
        if keep_aspect:

            # fit by width
            if self.aspect_ratio > rect.aspect_ratio:
                scale_fac = rect.width / self.width
                self.width = rect.width
                self.height = int(self.height * scale_fac)

            # fit by height
            elif self.aspect_ratio < rect.aspect_ratio:
                scale_fac = rect.height / self.height
                self.height = rect.height
                self.width = int(self.width * scale_fac)

        else:
            # copy width and height
            self.width = rect.width
            self.height = rect.height

        # position
        if keep_offset:
            self.position += self.position - rect.position

        else:
            self.position = rect.position

            # fit by width
            if self.aspect_ratio > rect.aspect_ratio:
                if align == Align.NO:
                    pass

                if align == Align.CENTER:
                    height_diff = rect.height - self.height
                    self.y += int(height_diff / 2)

                elif align == Align.TOP:
                    self.y == rect.y

                elif align == Align.BOTTOM:
                    height_diff = rect.height - self.height
                    self.y = rect.y + height_diff

            # fit by height
            elif self.aspect_ratio < rect.aspect_ratio:
                width_diff = rect.width - self.width

                if align == Align.NO:
                    pass

                if align == Align.CENTER:
                    self.x += int(width_diff / 2)

                elif align == Align.TOP:
                    self.x == rect.x

                elif align == Align.BOTTOM:
                    self.x = rect.x + width_diff

    def reset_transform(self):
        self.scale_x = 1
        self.scale_y = 1
        self.x = self.orig_x
        self.y = self.orig_y
        self.width = self.orig_width
        self.height = self.orig_height

    def copy(self) -> Rectangle:
        return Rectangle(self.x, self.y, self.width, self.height)

    def __repr__(self) -> str:
        return f"Rectangle(x: {self.x}, y: {self.y}, width: {self.width}, height: {self.height})"

    @property
    def valid(self) -> bool:
        return bool(self.width and self.height)


class NestedRectangle(Rectangle):
    """
    A Class that inherits from Rectangle and holds a child inside.
    """

    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        child: Optional[Union[Rectangle, NestedRectangle]] = None,
        keep_aspect: bool = True,
        align: Align = Align.CENTER,
        keep_offset: bool = False,
    ):
        super().__init__(x, y, width, height)

        # if child was not supplied on init make child same dimensions as parent
        if child == None:
            child = Rectangle(0, 0, self.width, self.height)

        self._child = child
        self._keep_aspect = keep_aspect
        self._align = align
        self._keep_offset = keep_offset
        self._child.fit_to_rect(
            self.get_rect(),
            keep_aspect=keep_aspect,
            align=align,
            keep_offset=keep_offset,
        )

    def fit_to_rect(
        self,
        rect: Rectangle,
        keep_aspect: bool = True,
        align: Align = Align.CENTER,
        keep_offset: bool = False,
    ):
        super().fit_to_rect(
            rect, keep_aspect=keep_aspect, align=align, keep_offset=keep_offset
        )
        self.child.fit_to_rect(
            self.get_rect(),
            keep_aspect=keep_aspect,
            align=align,
            keep_offset=keep_offset,
        )

    def get_rect(self) -> Rectangle:
        return Rectangle(self.x, self.y, self.width, self.height)

    @property
    def child(self) -> Rectangle:
        return self._child

    def set_child(
        self,
        child: Union[Rectangle, NestedRectangle],
        keep_aspect: bool = True,
        align: Align = Align.CENTER,
        keep_offset: bool = False,
    ) -> None:

        self._child = child
        self._child.fit_to_rect(
            self.get_rect(),
            keep_aspect=keep_aspect,
            align=align,
            keep_offset=keep_offset,
        )
        self._keep_aspect = keep_aspect
        self._align = align
        self._keep_offset = keep_offset

    def copy(self) -> NestedRectangle:
        return NestedRectangle(
            self.x,
            self.y,
            self.width,
            self.height,
            self.child.copy(),
            keep_aspect=self._keep_aspect,
            align=self._align,
        )

    def _set_x(self, value: int) -> None:
        offset = self.child.x - self._x
        self._x = int(value)
        self.child.x = int(value + offset)

    def _set_y(self, value: int) -> None:
        offset = self.child.y - self._y
        self._y = int(value)
        self.child.y = int(value + offset)

    def _set_width(self, value: int) -> None:
        self._width = int(value)
        self.child.fit_to_rect(
            self.get_rect(), self._keep_aspect, self._align, keep_offset=True
        )

    def _set_height(self, value: int) -> None:
        self._height = int(value)
        self.child.fit_to_rect(
            self.get_rect(), self._keep_aspect, self._align, keep_offset=True
        )

    def _set_scale_x(self, factor: float) -> None:
        super()._set_scale_x(factor)
        self.child.fit_to_rect(
            self.get_rect(),
            keep_aspect=self._keep_aspect,
            align=self._align,
            keep_offset=self._keep_offset,
        )

    def _set_scale_y(self, factor: float) -> None:
        super()._set_scale_y(factor)
        self.child.fit_to_rect(
            self.get_rect(),
            keep_aspect=self._keep_aspect,
            align=self._align,
            keep_offset=self._keep_offset,
        )

    @property
    def keep_aspect(self) -> bool:
        return self._keep_aspect

    @keep_aspect.setter
    def keep_aspect(self, value: bool):
        self._keep_aspect = value

    @property
    def align(self) -> Align:
        return self._align

    @align.setter
    def align(self, value: Align) -> None:
        self._align = value

        self.child.fit_to_rect(
            self.get_rect(),
            keep_aspect=self._keep_aspect,
            align=self._align,
            keep_offset=self._keep_offset,
        )

    @property
    def keep_offset(self) -> bool:
        return self._keep_offset

    @keep_offset.setter
    def keep_offset(self, value: bool):
        self._keep_offset = value


class Cell(NestedRectangle):
    """
    A Class that inherits from NestedRectangle and holds another NestedRectangle inside.
    """

    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        child: Optional[NestedRectangle] = None,
        keep_aspect: bool = True,
        align: Align = Align.CENTER,
    ):
        # if child was not supplied on init make child same dimensions as parent
        if child == None:
            child = NestedRectangle(0, 0, width, height)

        # init self
        super().__init__(
            x, y, width, height, child, keep_aspect=keep_aspect, align=align
        )

    def copy(self) -> Cell:
        return Cell(
            self.x,
            self.y,
            self.width,
            self.height,
            self.child.copy(),
            keep_aspect=self._keep_aspect,
            align=self._align,
        )

    def clear_content(self) -> None:
        self.set_child(NestedRectangle(0, 0, self.width, self.height))


class Grid(Rectangle):
    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        row_count: int,
        coll_count: int,
        cell_templ: Optional[Cell] = None,
        keep_aspect: bool = True,
        align: Align = Align.CENTER,
    ) -> None:

        super().__init__(x, y, width, height)
        self._keep_aspect: bool = keep_aspect
        self._align: Align = align

        # if cell_templ was not supplied on init make cell that has same dimensions as row / coll
        if cell_templ == None:
            cell_templ: Cell = Cell(
                0, 0, int(self.height / row_count), int(self.width / coll_count)
            )

        # init rows, colls, cells
        self.rows: List[Rectangle] = []
        self.colls: List[Rectangle] = []
        self.cells: List[List[Cell]] = []
        self._init_grid(
            row_count,
            coll_count,
            cell_templ,
            keep_aspect,
            align,
        )

    def _init_grid(
        self,
        row_count: int,
        coll_count: int,
        cell_templ: Cell,
        keep_aspect: bool,
        align: Align,
    ) -> None:

        self._init_rows(row_count)
        self._init_colls(coll_count)
        self._init_cells(cell_templ, keep_aspect, align)

    def _init_rows(self, row_count: int) -> None:
        row_height: int = int(self.height / row_count)
        self.rows = [
            Rectangle(self.x, self.y + (row_height * row_idx), self.width, row_height)
            for row_idx in range(row_count)
        ]

    def _init_colls(self, coll_count: int) -> None:
        coll_width: int = int(self.width / coll_count)
        self.colls = [
            Rectangle(self.x + (coll_width * coll_idx), self.y, coll_width, self.height)
            for coll_idx in range(coll_count)
        ]

    def _init_cells(self, cell_templ: Cell, keep_aspect: bool, align: Align) -> None:
        # TODO: cell.child.keep_aspect = keep_aspect

        self.cells.clear()
        # if cell_templ was supplied make sure it has the right dimension to fit in grid
        cell_templ.width = self.coll_width
        cell_templ.height = self.row_height

        for row_index, row in enumerate(self.rows):
            cell_y = row.y
            self.cells.append([])

            for coll in self.colls:
                cell_x = coll.x

                # make copy to have each cell individual instance
                cell_instance = cell_templ.copy()
                cell_instance.position = Point(cell_x, cell_y)
                self.cells[row_index].append(cell_instance)

    @classmethod
    def from_content(
        csl,
        x: int,
        y: int,
        width: int,
        height: int,
        content: List[NestedRectangle],
        row_count: Optional[int] = None,
        keep_aspect: bool = True,
        align: Align = Align.CENTER,
    ) -> Grid:
        """
        Creates a grid based of a content list. Calculates optimal amount of rows and colls.
        """
        if not row_count:

            # Calculate by how much images need to be scaled in order to fit. (won't be perfect)
            available_area = width * height
            content_area_orig = content[0].child.area
            content_area = available_area / len(content)
            scale_factor = math.sqrt(content_area / content_area_orig)

            content_size = (
                content[0].child.width * scale_factor,
                content[0].child.height * scale_factor,
            )

            row_count = math.ceil(width / content_size[0])
            coll_count = math.ceil(len(content) / row_count)

        else:
            # row count should not be bigger as nr of cells
            row_count = min(row_count, len(content))
            coll_count = math.ceil(len(content) / row_count)  # 13 / 3 = 4.3 -> 4

        grid = Grid(
            x,
            y,
            width,
            height,
            row_count,
            coll_count,
            keep_aspect=keep_aspect,
            align=align,
        )
        grid.place_content(content, keep_aspect=keep_aspect, align=align)
        return grid

    def get_cells_for_row(self, row_index: int) -> List[Cell]:
        return self.cells[row_index]

    def get_cell(self, row_index: int, coll_index: int) -> Cell:
        return self.cells[row_index][coll_index]

    def get_cells_all(self) -> List[Cell]:
        cells: List[Cell] = []
        for row_idx in range(self.row_count()):
            cells.extend(self.get_cells_for_row(row_idx))
        return cells

    @property
    def row_height(self) -> int:
        return int(self.height / self.row_count())

    @property
    def coll_width(self) -> int:
        return int(self.width / self.coll_count())

    def row_count(self) -> int:
        return len(self.rows)

    def coll_count(self) -> int:
        return len(self.colls)

    def place_content(
        self,
        content_list: List[NestedRectangle],
        keep_aspect: bool = True,
        align: Align = Align.CENTER,
        keep_offset: bool = False,
        clear_cells: bool = True,
    ):
        """
        Fills up all available cells with the content from given list.
        Will clear remaining empty cells.
        """
        counter: int = 0
        for row_idx in range(self.row_count()):
            for cell in self.get_cells_for_row(row_idx):
                try:
                    content = content_list[counter]
                except IndexError:
                    if clear_cells:
                        cell.clear_content()
                else:
                    # switch child of cell
                    cell.set_child(
                        content,
                        keep_aspect=keep_aspect,
                        align=align,
                        keep_offset=keep_offset,
                    )

                counter += 1

    def place_content_in_cell(
        self,
        row_index: int,
        coll_index: int,
        content: NestedRectangle,
        keep_aspect: bool = True,
        align: Align = Align.CENTER,
        keep_offset: bool = False,
    ):
        cell = self.get_cell(row_index, coll_index)
        # switch child of cell
        cell.set_child(
            content,
            keep_aspect=keep_aspect,
            align=align,
            keep_offset=keep_offset,
        )

    def scale_content(self, factor: float):
        for cell in self.get_cells_all():
            cell.child.scale_x *= factor
            cell.child.scale_y *= factor

    def scale_content_x(self, factor: float):
        for cell in self.get_cells_all():
            cell.child.scale_x *= factor

    def scale_content_y(self, factor: float):
        for cell in self.get_cells_all():
            cell.child.scale_y *= factor

    def reset_content_transforms(self):
        for cell in self.get_cells_all():
            cell.reset_transform()
