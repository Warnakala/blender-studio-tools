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

import math
from typing import List, Dict, Tuple, Union, Any, Optional, Set

import bpy
import gpu
import bgl
from gpu_extras.batch import batch_for_shader

from . import ops

from media_viewer.log import LoggerFactory

logger = LoggerFactory.getLogger(name=__name__)

Float2 = Tuple[float, float]
Float3 = Tuple[float, float, float]
Float4 = Tuple[float, float, float, float]

# Glsl.
gpu_vertex_shader = """
uniform mat4 ModelViewProjectionMatrix;

layout (location = 0) in vec2 pos;
layout (location = 1) in vec4 color;

out vec4 lineColor; // output to the fragment shader

void main()
{
    gl_Position = ModelViewProjectionMatrix * vec4(pos.x, pos.y, 0.0, 1.0);
    lineColor = color;
}
"""

gpu_fragment_shader = """
out vec4 fragColor;
in vec4 lineColor;

void main()
{
    fragColor = lineColor;
}
"""


def get_gpframe_coords(
    gpframe: bpy.types.GPencilFrame, do_3_dimensions=False
) -> List[Float2]:

    coords: List[Float2] = []

    for stroke in gpframe.strokes:

        stroke_coords: List[Float2] = []

        # 0-1 1-2 2-3 3-4 4-5 5-6
        # For each strokes we can duplicate the points and pop the last
        # and first index.
        for point in stroke.points:
            if do_3_dimensions:
                # Some shaders require a z coordinate, in this case just set it 0.
                stroke_coords.append((point.co[0], point.co[1], 0))
                stroke_coords.append((point.co[0], point.co[1], 0))

            else:
                # Only take x, y  coordinate, z is 0 for 2d view
                stroke_coords.append((point.co[0], point.co[1]))
                stroke_coords.append((point.co[0], point.co[1]))

        stroke_coords.pop(-1)
        stroke_coords.pop(0)

        coords.extend(stroke_coords)

    return coords


def get_active_gp_layer() -> bpy.types.GPencilLayer:

    active_media_area = ops.active_media_area

    # In startup.blend we made sure that the gp objects are named after
    # the area type.
    gp_obj = bpy.data.grease_pencils[active_media_area]

    # Get active layer and remove active frame.
    active_layer = gp_obj.layers.active
    return active_layer


def srgb2lin(s: float) -> float:
    if s <= 0.0404482362771082:
        lin = s / 12.92
    else:
        lin = pow(((s + 0.055) / 1.055), 2.4)
    return lin


def lin2srgb(lin: float) -> float:
    if lin > 0.0031308:
        s = 1.055 * (pow(lin, (1.0 / 2.4))) - 0.055
    else:
        s = 12.92 * lin
    return s


class GPDrawerCustomShader:
    def __init__(self):
        self._format = gpu.types.GPUVertFormat()

        # To find out what attributes are available look here:
        # ./source/blender/gpu/GPU_shader.h
        self._pos_id = self._format.attr_add(
            id="pos", comp_type="F32", len=2, fetch_mode="FLOAT"
        )
        self._color_id = self._format.attr_add(
            id="color", comp_type="F32", len=4, fetch_mode="FLOAT"
        )

        self.shader = gpu.types.GPUShader(gpu_vertex_shader, gpu_fragment_shader)

    def draw(self, gpframe: bpy.types.GPencilFrame, line_widht: int, color: Float4):

        coords = get_gpframe_coords(gpframe)

        if not coords:
            return

        # TODO: replace with gpu.state.line_width_set(width)
        bgl.glEnable(bgl.GL_BLEND)
        bgl.glLineWidth(line_widht)

        colors = [color for c in coords]

        vbo = gpu.types.GPUVertBuf(len=len(coords), format=self._format)
        vbo.attr_fill(id=self._pos_id, data=coords)
        vbo.attr_fill(id=self._color_id, data=colors)

        batch = gpu.types.GPUBatch(type="LINES", buf=vbo)
        batch.program_set(self.shader)
        batch.draw()


class GPDrawerBuiltInShader:
    def __init__(self):
        # 2D_UNIFORM_COLOR is not implemented, documentation is deprecated
        # use 3D_UNIFORM_COLOR instead.
        self.shader = gpu.shader.from_builtin("3D_UNIFORM_COLOR")

    def draw(self, gpframe: bpy.types.GPencilLayer, line_width: int, color: Float4):

        # TODO: not optimal to set here
        self.shader.uniform_float("color", color)

        coords = get_gpframe_coords(gpframe, do_3_dimensions=True)

        if not coords:
            return

        # Question: Can I change the line width using attributes?
        # Or do I have to do it this way?
        # TODO: replace with gpu.state.line_width_set(width)
        bgl.glEnable(bgl.GL_BLEND)
        bgl.glLineWidth(line_width)

        # print(f"Drawing coords: {coords}")
        batch = batch_for_shader(self.shader, "LINES", {"pos": coords})

        self.shader.bind()
        batch.draw(self.shader)


def get_active_gpframe(
    gplayer: bpy.types.GPencilLayer, frame: int
) -> Optional[bpy.types.GPencilFrame]:

    if not gplayer.frames:
        return None

    frames = [(f.frame_number, f) for f in gplayer.frames]
    frames.sort(key=lambda x: x[0])

    # Catch case frame is before first, return None.
    if frame < frames[0][0]:
        return None

    # Catch case frame is after last, return last.
    if frame >= frames[-1][0]:
        return frames[-1][1]

    # If we reach this point, return the next gpframe to the left.
    for idx, tup in enumerate(frames):
        frame_number, gp_frame = tup
        range_active = range(frame_number, frames[idx + 1][0])

        if frame in range_active:
            return gp_frame


def draw_callback(
    gp_drawer: Union[GPDrawerBuiltInShader, GPDrawerCustomShader],
    frame: int,
) -> None:

    # Runs every time redraw is triggered.

    gplayer = get_active_gp_layer()
    if not gplayer:
        return
    # Seem like this gp_layer.active_frame does not update when looping over all frames
    # get the active gp frame manually.
    active_frame = get_active_gpframe(gplayer, frame)

    if not active_frame:
        return

    # Get color, append 1 for alpha.
    # Convert color to lin, otherwise it looks wrong when rendering
    # it out with openGL.
    color = [srgb2lin(c) for c in gplayer.color]
    color = tuple(color) + (1.0,)

    gp_drawer.draw(active_frame, gplayer.thickness, color)


def tag_redraw_all_image_editors():
    context = bpy.context

    # Py cant access notifiers.
    for window in context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == "IMAGE_EDITOR":
                for region in area.regions:
                    if region.type == "WINDOW":
                        region.tag_redraw()


active_draw_handlers = []


def add_draw_handler():
    global active_draw_handlers

    if active_draw_handlers:
        return

    # Doing GPU stuff in the background crashes Blender, so let's not.
    if bpy.app.background:
        return

    # Question: Why does GPDrawerBuiltInShader not work
    gp_drawer = GPDrawerCustomShader()
    active_draw_handlers[:] = (
        bpy.types.SpaceImageEditor.draw_handler_add(
            draw_callback, (gp_drawer,), "WINDOW", "POST_VIEW"
        ),
    )

    tag_redraw_all_image_editors()


def rm_draw_handler():
    global active_draw_handlers

    if not active_draw_handlers:
        return

    try:
        bpy.types.SpaceImageEditor.draw_handler_remove(
            active_draw_handlers[0], "WINDOW"
        )
    except ValueError:
        # Thrown when already removed.
        pass
    active_draw_handlers.clear()

    tag_redraw_all_image_editors()


# ---------REGISTER ----------.

classes = []


def register():
    # For Debugging:
    add_draw_handler()

    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    # For Debugging:
    rm_draw_handler()

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
