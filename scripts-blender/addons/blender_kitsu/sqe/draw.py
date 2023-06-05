# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# <pep8 compliant>.

# Copyright: Blender Foundation

import typing

import bpy
import bgl
import gpu
from gpu_extras.batch import batch_for_shader


# Shaders and batches

rect_coords = ((0, 0), (1, 0), (1, 1), (0, 1))

# Setup shaders only if Blender runs in the foreground.
# If running in the background, no handles are registered, as drawing extra UI
# elements does not make sense.
# See register() and unregister().
if bpy.app.version_string.split('.')[0] == '3':
    color_key = "2D_UNIFORM_COLOR"
else:
    color_key = "UNIFORM_COLOR"
if not bpy.app.background:
    ucolor_2d_shader = gpu.shader.from_builtin(color_key) 
    ucolor_2d_rect_batch = batch_for_shader(
        ucolor_2d_shader, "TRI_FAN", {"pos": rect_coords}
    )


Float2 = typing.Tuple[float, float]
Float3 = typing.Tuple[float, float, float]
Float4 = typing.Tuple[float, float, float, float]


def draw_line(position: Float2, size: Float2, color: Float4):
    with gpu.matrix.push_pop():
        bgl.glEnable(bgl.GL_BLEND)

        gpu.matrix.translate(position)
        gpu.matrix.scale(size)

        # Render a colored rectangle
        ucolor_2d_shader.bind()
        ucolor_2d_shader.uniform_float("color", color)
        ucolor_2d_rect_batch.draw(ucolor_2d_shader)

        bgl.glDisable(bgl.GL_BLEND)


def get_strip_rectf(strip) -> Float4:
    # Get x and y in terms of the grid's frames and channels.
    x1 = strip.frame_final_start
    x2 = strip.frame_final_end
    # Seems to be a 5 % offset from channel top start of strip.
    y1 = strip.channel + 0.05
    y2 = strip.channel - 0.05 + 1

    return x1, y1, x2, y2


def draw_line_in_strip(strip_coords: Float4, height_factor: float, color: Float4):
    # Unpack strip coordinates.
    s_x1, channel, s_x2, _ = strip_coords

    # Get the line's measures, as a percentage of channel height.
    # Note that the strip's height is 10% smaller than the channel (centered 5% top and bottom).
    # Note 2: offset the height slightly (0.005) to make room for the selection outline (channel coords).
    line_height_in_channel = (0.9 - 0.005 * 2) * height_factor + 0.005
    line_thickness = 0.04

    # Offset the width slightly to make room for the selection outline (virtual grid horizontal coords).
    width_offset = 0.2
    width = (s_x2 - s_x1) - width_offset * 2

    pos = (s_x1 + width_offset, channel + line_height_in_channel)
    scale = (width, line_thickness)
    draw_line(pos, scale, color)


def draw_callback_px():
    context = bpy.context
    sqe = context.scene.sequence_editor
    if not sqe:
        return
    strips = sqe.sequences_all

    for strip in strips:
        # Get corners of the strip rectangle in terms of the grid's frames and channels (virtual, not px).
        strip_coords = get_strip_rectf(strip)

        if strip.kitsu.initialized or strip.kitsu.linked:
            try:
                color = tuple(
                    context.scene.kitsu.sequence_colors[strip.kitsu.sequence_id].color
                )
            except KeyError:
                color = (1, 1, 1)

            alpha = 0.75 if strip.kitsu.linked else 0.25

            line_color = color + (alpha,)
            draw_line_in_strip(strip_coords, 0.0, line_color)

        if strip.kitsu.media_outdated:
            line_color = (1.0, 0.05, 0.145, 0.75)
            draw_line_in_strip(strip_coords, 0.9, line_color)


draw_handles = []


def register():
    if bpy.app.background:
        # Do not register anything if Blender runs in the background (no UI needed).
        return
    draw_handles.append(
        bpy.types.SpaceSequenceEditor.draw_handler_add(
            draw_callback_px, (), "WINDOW", "POST_VIEW"
        )
    )


def unregister():
    if bpy.app.background:
        return
    for handle in reversed(draw_handles):
        try:
            bpy.types.SpaceSequenceEditor.draw_handler_remove(handle, "WINDOW")
        except ValueError:
            # Not sure why, but sometimes the handler seems to already be removed...??
            pass
