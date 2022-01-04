from __future__ import annotations
from typing import (
    List,
    Dict,
    Tuple,
    Union,
    Any,
    Optional,
    Set,
    Callable,
    Generator,
    Iterable,
)
from enum import Enum
from copy import copy

import bpy
import gpu
import bgl
import blf
from gpu_extras.batch import batch_for_shader
from bpy.app.handlers import persistent

from . import ops, opsdata

Float2 = Tuple[float, float]
Float3 = Tuple[float, float, float]
Float4 = Tuple[float, float, float, float]
Int2 = Tuple[int, int]
Int3 = Tuple[int, int, int]
Int4 = Tuple[int, int, int, int]
# To understand here is an image of how the SQE calculates
# its screen coordinates with the example resolution
# of (2048, 858)

"""
(-1024,429,0)----------(1024,429,0)
|                      |
|        C(0,0,0)      |
|                      |
(-1024,-429,0)---------(1024,-429,0)
"""

# Here is a graphic of how the ImageEditor calculates
# its screen coordinates with the example resolution
# of (2048, 858)

"""
(0,1,0)----------------(1,1,0)
|                      |
|        C(0.5,0.5,0)  |
|                      |
(0,0,0)----------------(1,0,0)
"""

## Thats how region coordinates work for openGL:
"""
(0,region.height,0)----(region.width,region.height,0)
|                      |
|                      |
|                      |
(0,0,0)----------------(region.width,0,0)
"""


def get_region_by_name(area: bpy.types.Area, name: str) -> Optional[bpy.types.Region]:
    for region in area.regions:
        if region.type == name:
            return region
    return None


REGION_NAME = "PREVIEW"
REGION_NAME_IMG = "WINDOW"


def draw_toggle(region_name: str):
    area = bpy.context.area

    region = get_region_by_name(area, region_name)
    if not region:
        return

    offset_y = -5
    offset_x = 10
    width = 30
    height = 30
    # print(f"X: {region.x} Y: {region.y} WIDTH: {region.width} HEIGHT: {region.height}")

    top_left = (0 + offset_x, region.height + offset_y)

    top_right = (top_left[0] + width, top_left[1])
    bot_left = (top_left[0], top_left[1] - height)
    bot_right = (top_left[0] + width, top_left[1] - height)

    coordinates = [top_left, top_right, bot_left, bot_right]
    shader = gpu.shader.from_builtin("2D_UNIFORM_COLOR")
    batch = batch_for_shader(
        shader,
        "TRIS",
        {"pos": coordinates},
        indices=((0, 1, 2), (2, 1, 3)),  # (2, 1, 3)
    )
    batch.draw(shader)


def draw_text(region_name: str):
    area = bpy.context.area
    region = get_region_by_name(area, region_name)

    offset_y = -20
    offset_x = 5
    # print(f"X: {region.x} Y: {region.y} WIDTH: {region.width} HEIGHT: {region.height}")
    y = region.height + offset_y
    x = 0 + offset_x
    font_id = 0
    bgl.glEnable(bgl.GL_BLEND)
    blf.position(font_id, x, y, 0)
    blf.size(font_id, 12, 72)
    blf.color(font_id, 1, 1, 1, 0.9)
    blf.draw(font_id, "Test")


# This function is copied from: "https://github.com/ubisoft/videotracks"
def get_region_at_xy(
    context: bpy.types.Context, x: int, y: int
) -> Optional[Tuple[bpy.types.Region, bpy.types.Area]]:
    """
    :param context:
    :param x:
    :param y:
    :return: the region and the area containing this region
    """
    for area in context.screen.areas:
        for region in area.regions:
            if is_mouse_in_region(region, x, y):
                return region, area

    return None, None


def is_mouse_in_region(region: bpy.types.Region, x: int, y: int) -> bool:
    if (
        region.x <= x < region.width + region.x
        and region.y <= y < region.height + region.y
    ):
        return True
    return False


def get_region_of_area(
    area: bpy.types.Area, region_type: str
) -> Optional[bpy.types.Region]:
    for region in area.regions:
        if region.type == region_type:
            return region
    return None


def points_to_int2(points: Iterable[Point]) -> Tuple[Int2]:
    l = [p.as_tuple() for p in points]
    return tuple(l)

class Point:

    """
    Class that represents a point with 2 coordinates.

    #TODO: support indexing and interating in future.
    """

    def __init__(self, x: int, y: int):
        self._x = int(x)
        self._y = int(y)

    @property
    def x(self) -> int:
        return self._x

    @property
    def y(self) -> int:
        return self._y

    def as_tuple(self) -> Int2:
        return self._coords

    @property
    def _coords(self) -> Int2:
        return (self.x, self.y)

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

    def __iter__(self):
        for i in self._coords:
            yield i

    def __getitem__(self, i):
        return self._coords[i]

    def __len__(self):
        return 2


class RectCoords:
    """
    Class that represents the coordinates of a Rectangle.
    Instances of this class are returned by the Rectangle class.
    The individual coordinate can be retrieved with (top_left, top_right, bot_left, bot_right)..
    RectCoordinates work as region coordinates, that means 0,0 is bottom left.
    """

    def __init__(
        self, top_left: Point, top_right: Point, bot_left: Point, bot_right: Point
    ):
        ## Thats how region coordinates work for openGL:
        """
        (0,region.height,0)----(region.width,region.height,0)
        |                      |
        |                      |
        |                      |
        (0,0,0)----------------(region.width,0,0)
        """
        self._top_left = top_left
        self._top_right = top_right
        self._bot_left = bot_left
        self._bot_right = bot_right
        self._width = top_right.x - top_left.x
        self._height = top_left.y - bot_left.y

    @property
    def top_left(self) -> Point:
        return self._top_left

    @property
    def top_right(self) -> Point:
        return self._top_right

    @property
    def bot_left(self) -> Point:
        return self._bot_left

    @property
    def bot_right(self) -> Point:
        return self._bot_right

    @property
    def position(self) -> Point:
        return self.top_left

    @property
    def center(self) -> Point:
        center_x = int(self.top_left.x + (0.5 * self._width))
        center_y = int(self.top_left.y - (0.5 * self._height))

        return Point(center_x, center_y)

    @property
    def _coords(self) -> Tuple[Point, Point, Point, Point]:
        return (self.top_left, self.top_right, self.bot_left, self.bot_right)

    def apply_padding(self, value: int) -> None:
        self._top_left = self._top_left - Point(value, -value)
        self._top_right = self._top_right + Point(value, value)
        self._bot_left = self._bot_left - Point(value, value)
        self._bot_right = self._bot_right + Point(value, -value)

    def is_over(self, point: Point) -> bool:
        if (
            self.top_left.x <= point.x <= self.top_right.x
            and self.bot_left.y <= point.y <= self.top_left.y
        ):
            return True
        return False

    def __repr__(self) -> str:
        return (
            f"TopLeft({self.top_left.x},{self.top_left.y}), "
            f"TopRight({self.top_right.x},{self.top_right.y}), "
            f"BotLeft({self.bot_left.x},{self.bot_left.y}), "
            f"BotRight({self.bot_right.x},{self.bot_right.y})"
        )

    def __iter__(self):
        for point in self._coords:
            yield point

    def __getitem__(self, i):
        return self._coords[i]

    def __len__(self):
        return 4

    def __copy__(self):
        return RectCoords(self.top_left, self.top_right, self.bot_left, self.bot_right)


class Button:
    def __init__(
        self,
        width: int,
        height: int,
        x: int = 0,
        y: int = 0,
    ):
        self._width = width
        self._height = height
        self._x = x
        self._y = y

    @property
    def width(self) -> int:
        return self._width

    @property
    def height(self) -> int:
        return self._height

    # Local coordinates.
    def get_coords(self) -> RectCoords:
        top_left = Point(self._x, self._y)
        top_right = Point(top_left.x + self.width, top_left.y)
        bot_left = Point(top_left.x, top_left.y - self.height)
        bot_right = Point(top_left.x + self.width, top_left.y - self.height)
        return RectCoords(top_left, top_right, bot_left, bot_right)

    # Region coordinates.
    def get_region_coords(self, region: bpy.types.Region) -> RectCoords:
        top_left = Point(self._x, region.height + self._y)
        top_right = Point(top_left.x + self.width, top_left.y)
        bot_left = Point(top_left.x, top_left.y - self.height)
        bot_right = Point(top_left.x + self.width, top_left.y - self.height)
        return RectCoords(top_left, top_right, bot_left, bot_right)

    # Global coordinates.
    def get_global_coords(self, region: bpy.types.Region) -> RectCoords:
        global_x = region.x + self._x
        global_y = region.y + self._y
        global_top_left = Point(global_x, region.height + global_y)
        global_top_right = Point(global_top_left.x + self.width, global_top_left.y)
        global_bot_left = Point(global_top_left.x, global_top_left.y - self.height)
        global_bot_right = Point(
            global_top_left.x + self.width, global_top_left.y - self.height
        )
        return RectCoords(
            global_top_left, global_top_right, global_bot_left, global_bot_right
        )

    def __repr__(self) -> str:
        coords = self.get_coords()
        return (
            f"Pos({coords.top_left.x},{coords.top_left.y}), "
            f"Width({self.width}), "
            f"Height({self.height}), "
        )


class ButtonDrawer:
    def __init__(
        self,
    ):
        self._shader = gpu.shader.from_builtin("2D_UNIFORM_COLOR")
        self.draw_arrow = True
        self.draw_rect = False
        self._arrow_direction = "UP"

    @property
    def arrow_direction(self):
        return self._arrow_direction

    @arrow_direction.setter
    def arrow_direction(self, direction: str):
        if direction not in ["UP", "DOWN"]:
            raise ValueError("Direction must be either 'UP', 'DOWN'")

        self._arrow_direction = direction

    @property
    def shader(self):
        return self._shader

    def draw_button(
        self, button: Button, region: bpy.types.Region, color: Float4
    ) -> None:
        bgl.glEnable(bgl.GL_BLEND)
        bgl.glLineWidth(0)
        coords = button.get_region_coords(region)

        # Draw rectangle.
        # Bind the shader object. Required to be able to change uniforms of this shader.
        if self.draw_rect:
            self.shader.bind()
            color_dimmed = [c * 0.4 for c in color]
            self.shader.uniform_float("color", color_dimmed)
            batch = batch_for_shader(
                self.shader,
                "TRIS",
                {"pos": coords},
                indices=((0, 1, 2), (2, 1, 3)),  # (2, 1, 3)
            )
            batch.draw(self.shader)

        if self.draw_arrow:
            # Draw arrow pointing up.
            if self.arrow_direction == "UP":
                cord_center = Point(coords.center.x, coords.top_left.y)
                line_pos = (
                    coords.bot_left,
                    cord_center,
                    cord_center,
                    coords.bot_right,
                )

            # Draw arrow pointing down.
            elif self.arrow_direction == "DOWN":
                cord_center = Point(coords.center.x, coords.bot_left.y)
                line_pos = (
                    coords.top_left,
                    cord_center,
                    cord_center,
                    coords.top_right,
                )

            else:
                return

            # Create line batch and draw it.
            bgl.glLineWidth(3)
            self._shader.bind()
            self._shader.uniform_float("color", color)
            # print(f"Drawing points: {line_pos}")
            line_batch = batch_for_shader(self._shader, "LINES", {"pos": line_pos})
            line_batch.draw(self._shader)


# The way this operator adds draw handlers and runs in modal mode is
# inspired by: "https://github.com/ubisoft/videotracks"
class MV_OT_toggle_header(bpy.types.Operator):

    bl_idname = "media_viewer.toggle_header"
    bl_label = "Toggle Header"
    # bl_options = {"REGISTER", "INTERNAL"}

    def __init__(self):
        self._area_draw_handle_dict: Dict[str : List[Callable]] = {
            "IMAGE_EDITOR": [],
            "SEQUENCE_EDITOR": [],
        }
        self._areas_to_process: List[str] = ["IMAGE_EDITOR", "SEQUENCE_EDITOR"]
        self._area_region_dict: Dict[str, str] = {
            "IMAGE_EDITOR": "WINDOW",
            "SEQUENCE_EDITOR": "PREVIEW",
        }
        self._area_space_type_dict: Dict[str, bpy.types.Space] = {
            "IMAGE_EDITOR": bpy.types.SpaceImageEditor,
            "SEQUENCE_EDITOR": bpy.types.SpaceSequenceEditor,
        }

        # Define variables to control our rectangle.
        btn_offset_y = -5
        btn_offset_x = 10
        btn_width = 24
        btn_height = 12
        self.button = Button(btn_width, btn_height, btn_offset_x, btn_offset_y)
        self.btn_drawer = ButtonDrawer()
        # self.btn_drawer.draw_rect = True

    def draw(self, context: bpy.types.Context) -> None:

        # Get active media area.
        area = ops.active_media_area_obj
        if not area:
            return

        # We don't need it for the text editor.
        if area.type not in self._areas_to_process:
            return

        # Get region to display header toggle in.
        region_name = self._area_region_dict[area.type]
        region = get_region_by_name(area, region_name)
        if not region:
            return
        # print(f"X: {region.x} Y: {region.y} WIDTH: {region.width} HEIGHT: {region.height}")

        # Set arrow direction depending on region header state.
        if area.spaces.active.show_region_header:
            self.btn_drawer.arrow_direction = "UP"
        else:
            self.btn_drawer.arrow_direction = "DOWN"

        # Draw button.
        self.btn_drawer.draw_button(self.button, region, (0.8, 0.8, 0.8, 0.9))

    def modal(self, context: bpy.types.Context, event: bpy.types.Event) -> Set[str]:

        # If cancel remove draw handler.
        if self.should_cancel():
            for area_type, draw_handler_list in self._area_draw_handle_dict:

                region_type = self._area_region_dict[area_type]
                space_type = self._area_space_type_dict[area_type]

                for draw_handler in draw_handler_list:
                    space_type.draw_handler_remove(draw_handler, region_type)

                draw_handler_list.clear()

            return {"CANCELLED"}

        # Redraw areas, otherwise button flickers.
        for area in context.screen.areas:
            area.tag_redraw()

        area = ops.active_media_area_obj
        if not area:
            return {"PASS_THROUGH"}

        # We don't need it for the text editor.
        if area.type not in self._areas_to_process:
            return {"PASS_THROUGH"}

        region = get_region_of_area(area, self._area_region_dict[area.type])
        if not region:
            return {"PASS_THROUGH"}

        # Check if mouse is in active_media_area.
        if not is_mouse_in_region(region, event.mouse_x, event.mouse_y):
            return {"PASS_THROUGH"}

        # Check if mouse is in collision region.
        # Apply some padding to make it easier clickable.
        collision_rect = self.button.get_global_coords(region)
        collision_rect.apply_padding(10)
        if not collision_rect.is_over(Point(event.mouse_x, event.mouse_y)):
            return {"PASS_THROUGH"}

        # If user clicks on the rectangle with leftmouse button, toggle header.
        if event.type == "LEFTMOUSE":
            if event.value == "PRESS":
                area.spaces.active.show_region_header = (
                    not area.spaces.active.show_region_header
                )
            return {"PASS_THROUGH"}

        # return {"RUNNING_MODAL"}
        return {"PASS_THROUGH"}

    def should_cancel(self) -> bool:
        return not self.context.window_manager.media_viewer.draw_header_toggle

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> Set[str]:
        self.context = context

        # Add draw handler to each space type.
        for area_type in self._areas_to_process:
            region_type = self._area_region_dict[area_type]
            space_type = self._area_space_type_dict[area_type]
            self._area_draw_handle_dict[area_type].append(
                space_type.draw_handler_add(
                    self.draw, (context,), region_type, "POST_PIXEL"
                )
            )

        context.window_manager.modal_handler_add(self)
        return {"RUNNING_MODAL"}


@persistent
def load_post_start_toggle_header(_) -> None:
    bpy.ops.media_viewer.toggle_header("INVOKE_DEFAULT")


# ----------------REGISTER--------------.

load_post_handler: List[Callable] = [load_post_start_toggle_header]
classes = [MV_OT_toggle_header]
draw_handlers_img: List[Callable] = []
draw_handlers_sqe: List[Callable] = []


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    for handler in load_post_handler:
        bpy.app.handlers.load_post.append(load_post_start_toggle_header)

    # draw_handlers_sqe.append(bpy.types.SpaceSequenceEditor.draw_handler_add(
    #     draw_text, (REGION_NAME,), REGION_NAME, "POST_PIXEL"
    # ))

    # draw_handlers_img.append(bpy.types.SpaceImageEditor.draw_handler_add(
    #     draw_text, (REGION_NAME_IMG,), REGION_NAME_IMG, "POST_PIXEL"
    # ))

    # draw_handlers_sqe.append(bpy.types.SpaceSequenceEditor.draw_handler_add(
    #     draw_toggle, (REGION_NAME,), REGION_NAME, "POST_PIXEL"
    # ))
    # draw_handlers_img.append(bpy.types.SpaceImageEditor.draw_handler_add(
    #     draw_toggle, (REGION_NAME_IMG,), REGION_NAME_IMG, "POST_PIXEL"
    # ))


def unregister():

    # Remove handlers.
    for handler in draw_handlers_img:
        bpy.types.SpaceImageEditor.draw_handler_remove(handler, REGION_NAME_IMG)

    for handler in draw_handlers_sqe:
        bpy.types.SpaceSequenceEditor.draw_handler_remove(handler, REGION_NAME)

    for handler in load_post_handler:
        bpy.app.handlers.load_post.remove(handler)

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
