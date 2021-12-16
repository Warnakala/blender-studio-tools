from typing import List, Dict, Tuple, Union, Any, Optional, Set, Callable

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


def is_mouse_in_region_rect(
    region: bpy.types.Region, rectangle: Tuple[Int2, Int2, Int2, Int2], x: int, y: int
) -> bool:
    # [top_left, top_right, bot_left, bot_right]
    width = rectangle[1][0] - rectangle[0][0]
    height = rectangle[0][1] - rectangle[2][1]

    # To global screen coordinates.
    top_left = (region.x + rectangle[0][0], region.y + rectangle[0][1])

    top_right = (top_left[0] + width, top_left[1])
    bot_left = (top_left[0], top_left[1] - height)
    bot_right = (top_left[0] + width, top_left[1] - height)

    # print(f"RECT: {top_left[0], top_left[1]} WIDTH: {width} HEIGHT: {height})")
    # print(f"MICE: {x, y}")

    if top_left[0] <= x <= top_right[0] and bot_left[1] <= y <= top_left[1]:
        return True
    return False


def get_region_of_area(
    area: bpy.types.Area, region_type: str
) -> Optional[bpy.types.Region]:
    for region in area.regions:
        if region.type == region_type:
            return region
    return None


def scale_rectangle_center(
    rectangle: Tuple[Int2, Int2, Int2, Int2], factor: float
) -> Tuple[Int2, Int2, Int2, Int2]:
    """
    ! not working yet
    """
    # [top_left, top_right, bot_left, bot_right]
    width = rectangle[1][0] - rectangle[0][0]
    height = rectangle[0][1] - rectangle[2][1]
    center = (int(rectangle[0][0] + width / 2), int(rectangle[0][1] - height / 2))

    rectangle_s: List[Int2, Int2, Int2, Int2] = []
    for point in rectangle:
        new_point = (
            center[0] + (factor * (point[0] - center[0])),
            center[1] + (factor * (point[1] - center[1])),
        )
        rectangle_s.append(new_point)

    return rectangle_s


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
        self.btn_offset_y = -5
        self.btn_offset_x = 10
        self.btn_width = 24
        self.btn_height = 12
        self.btn_coordinates: List[Int2, Int2, Int2, Int2] = []

        # Shader
        self.shader = gpu.shader.from_builtin("2D_UNIFORM_COLOR")

    def get_btn_coordinates(
        self, region: bpy.types.Region
    ) -> Tuple[Int2, Int2, Int2, Int2]:
        # Define top left coordinate which will be our referenc point for other points.
        top_left = (0 + self.btn_offset_x, region.height + self.btn_offset_y)

        top_right = (top_left[0] + self.btn_width, top_left[1])
        bot_left = (top_left[0], top_left[1] - self.btn_height)
        bot_right = (top_left[0] + self.btn_width, top_left[1] - self.btn_height)

        return (top_left, top_right, bot_left, bot_right)

    def _draw_widget(
        self, btn_coordinates: Tuple[Int2, Int2, Int2, Int2], area: bpy.types.Area
    ) -> None:

        if not btn_coordinates:
            return

        bgl.glEnable(bgl.GL_BLEND)
        bgl.glLineWidth(0)

        # Draw rectangle.
        # Bind the shader object. Required to be able to change uniforms of this shader.
        # self.shader.bind()
        # self.shader.uniform_float("color", (0.2, 0.2, 0.2, 1))
        # batch = batch_for_shader(
        #     self.shader,
        #     "TRIS",
        #     {"pos": btn_coordinates},
        #     indices=((0, 1, 2), (2, 1, 3)),  # (2, 1, 3)
        # )
        # batch.draw(self.shader)

        bgl.glLineWidth(3)
        self.shader.bind()
        self.shader.uniform_float("color", (0.8, 0.8, 0.8, 0.8))
        # Draw arrow pointing up.
        if area.spaces.active.show_region_header:
            cord_center = (
                btn_coordinates[0][0] + self.btn_width / 2,
                btn_coordinates[0][1],
            )
            line_pos = (
                btn_coordinates[2],
                cord_center,
                cord_center,
                btn_coordinates[3],
            )
        # Draw arrow pointing down.
        else:
            cord_center = (
                btn_coordinates[0][0] + self.btn_width / 2,
                btn_coordinates[0][1] - self.btn_height,
            )
            line_pos = (
                btn_coordinates[0],
                cord_center,
                cord_center,
                btn_coordinates[1],
            )
        line_batch = batch_for_shader(self.shader, "LINES", {"pos": line_pos})
        line_batch.draw(self.shader)

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

        # Get button coordinates.
        coordinates = self.get_btn_coordinates(region)
        self.btn_coordinates.clear()
        self.btn_coordinates.extend(list(coordinates))

        # btn_coordinates_s = scale_rectangle_center(coordinates, 0.7)
        self._draw_widget(coordinates, area)

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

        # At this point mouse is in right region, now we check if its above our button.
        if not self.btn_coordinates:
            return {"PASS_THROUGH"}

        if not is_mouse_in_region_rect(
            region, self.btn_coordinates, event.mouse_x, event.mouse_y
        ):
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

load_post_handler: List[Callable] = []
classes = [MV_OT_toggle_header]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    load_post_handler.clear()
    load_post_handler.append(
        bpy.app.handlers.load_post.append(load_post_start_toggle_header)
    )

    # bpy.types.SpaceSequenceEditor.draw_handler_add(
    #     draw_text, (REGION_NAME,), REGION_NAME, "POST_PIXEL"
    # )
    # bpy.types.SpaceImageEditor.draw_handler_add(
    #     draw_text, (REGION_NAME_IMG,), REGION_NAME_IMG, "POST_PIXEL"
    # )

    # bpy.types.SpaceSequenceEditor.draw_handler_add(
    #     draw_toggle, (REGION_NAME,), REGION_NAME, "POST_PIXEL"
    # )
    # bpy.types.SpaceImageEditor.draw_handler_add(
    #     draw_toggle, (REGION_NAME_IMG,), REGION_NAME_IMG, "POST_PIXEL"
    # )


def unregister():

    for handler in load_post_handler:
        bpy.app.handlers.load_post.remove(handler)
    load_post_handler.clear()

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    # bpy.types.SpaceSequenceEditor.draw_handler_remove(draw_text, "PREVIEW")
    # bpy.types.SpaceImageEditor.draw_handler_remove(draw_text, REGION_NAME_IMG)

    # bpy.types.SpaceSequenceEditor.draw_handler_remove(draw_toggle, "PREVIEW")
    # bpy.types.SpaceImageEditor.draw_handler_remove(draw_toggle, REGION_NAME_IMG)
