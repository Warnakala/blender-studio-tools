from typing import List, Dict, Tuple, Union, Any, Optional, Set

import bpy
import gpu
import bgl
import blf
from gpu_extras.batch import batch_for_shader

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


# ----------------REGISTER--------------.

classes = ()


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.SpaceSequenceEditor.draw_handler_add(
        draw_text, (REGION_NAME,), REGION_NAME, "POST_PIXEL"
    )
    bpy.types.SpaceImageEditor.draw_handler_add(
        draw_text, (REGION_NAME_IMG,), REGION_NAME_IMG, "POST_PIXEL"
    )

    bpy.types.SpaceSequenceEditor.draw_handler_add(
        draw_toggle, (REGION_NAME,), REGION_NAME, "POST_PIXEL"
    )
    bpy.types.SpaceImageEditor.draw_handler_add(
        draw_toggle, (REGION_NAME_IMG,), REGION_NAME_IMG, "POST_PIXEL"
    )


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    bpy.types.SpaceSequenceEditor.draw_handler_remove(draw_text, "PREVIEW")
    bpy.types.SpaceImageEditor.draw_handler_remove(draw_text, REGION_NAME_IMG)

    bpy.types.SpaceSequenceEditor.draw_handler_remove(draw_toggle, "PREVIEW")
    bpy.types.SpaceImageEditor.draw_handler_remove(draw_toggle, REGION_NAME_IMG)
