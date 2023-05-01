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

import sys
import random
import pygame
import colorsys
from typing import Tuple
import math

RES_X = int(1920 / 1.4)
RES_Y = int(1080 / 1.4)


def get_random_pastel_color_rgb() -> Tuple[float, float, float]:
    """Returns a randomly generated color with high brightness and low saturation."""

    hue = random.random()
    saturation = random.uniform(0.25, 0.33)
    brightness = random.uniform(0.75, 0.83)

    color = colorsys.hsv_to_rgb(hue, saturation, brightness)
    return (int(color[0] * 255), int(color[1] * 255), int(255 * color[2]))


def draw_nested_rect(rect):
    if not hasattr(rect, "color"):
        color = get_random_pastel_color_rgb()
        rect.color = color

    pygame.draw.rect(
        surface, rect.color, pygame.Rect(rect.x, rect.y, rect.width, rect.height)
    )
    # color = get_random_pastel_color_rgb()
    if not hasattr(rect.child, "color"):
        fac = 0.5
        color = (
            int(rect.color[0] * fac),
            int(rect.color[1] * fac),
            int(rect.color[2] * fac),
        )
        rect.child.color = color
    pygame.draw.rect(
        surface,
        rect.child.color,
        pygame.Rect(rect.child.x, rect.child.y, rect.child.width, rect.child.height),
    )


def draw_single_cell(cell):
    if not hasattr(cell, "color"):
        color = get_random_pastel_color_rgb()
        cell.color = color
    pygame.draw.rect(
        surface, cell.color, pygame.Rect(cell.x, cell.y, cell.width, cell.height)
    )
    draw_nested_rect(cell.child)


def draw_cells(grid):
    for row_idx in range(grid.row_count()):
        for cell in grid.get_cells_for_row(row_idx):
            draw_single_cell(cell)


def draw_rows(grid):
    for idx, cell in enumerate(grid.rows):
        color = get_random_pastel_color_rgb()
        pygame.draw.rect(
            surface, color, pygame.Rect(cell.x, cell.y, cell.width, cell.height)
        )


def draw_colls(grid):
    for cell in grid.colls:
        color = get_random_pastel_color_rgb()
        pygame.draw.rect(
            surface, color, pygame.Rect(cell.x, cell.y, cell.width, cell.height)
        )


# appen sys path
sys.path.append("/home/guest/dev/projects/render-review/render_review")
from geo import Grid, Rectangle, NestedRectangle, Align, Cell


# Initializing Pygame
pygame.init()
surface = pygame.display.set_mode((RES_X, RES_Y))

# Init Rectangles
rect = Rectangle(600, 0, 600 / 2, 400 / 2)
nested_rect = NestedRectangle(
    600, 300, 1920 / 6, 1080 / 6, child=rect, align=Align.CENTER
)
cell = Cell(
    0,
    0,
    500,
    500,
    child=nested_rect,
    align=Align.TOP
    # child=NestedRectangle(100, 100, 400, 400, child=Rectangle(0, 0, 1920, 1080)),
)
grid1 = Grid(0, 0, RES_X, RES_Y, 6, 9, cell_templ=cell, align=Align.CENTER)
grid1.scale_content(1)
grid1.scale_content_x(1)
# grid1.reset_content_transforms()
# grid1.content_scale_x = 1

content = [NestedRectangle(0, 0, 1920, 1080, child=rect.copy()) for r in range(28)]
grid2 = Grid.from_content(0, 0, RES_X, RES_Y, content, 6)
grid2.scale_content(0.8)
# draw_rows(grid)
# draw_colls(grid)

# run
clock = pygame.time.Clock()
run = True

# draw_single_cell(grid.cells[0][1])
count = 1
while run:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
    surface.fill(pygame.Color(0, 0, 0, 1))
    # grid2.scale_content(0.5 * (1 + math.sin(2 * 3.14 * 2 * count)) + 0.1)
    draw_cells(grid1)
    # draw_nested_rect(nested_rect)
    # nested_rect.scale_x = 1.02
    # nested_rect.y += 10
    # draw_single_cell(cell)
    pygame.display.update()
    # cell.x += 10
    # cell.child.x += 1
    # cell.child.child.y += 1
    clock.tick(4)
    count += 1
pygame.quit()
