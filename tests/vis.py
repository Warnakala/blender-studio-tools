import sys
import random
import pygame
import colorsys
from typing import Tuple

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
    color = get_random_pastel_color_rgb()
    pygame.draw.rect(
        surface, color, pygame.Rect(rect.x, rect.y, rect.width, rect.height)
    )
    # color = get_random_pastel_color_rgb()
    fac = 0.5
    color = (int(color[0] * fac), int(color[1] * fac), int(color[2] * fac))
    pygame.draw.rect(
        surface,
        color,
        pygame.Rect(rect.child.x, rect.child.y, rect.child.width, rect.child.height),
    )


def draw_single_cell(cell):
    color = get_random_pastel_color_rgb()
    pygame.draw.rect(
        surface, color, pygame.Rect(cell.x, cell.y, cell.width, cell.height)
    )
    draw_nested_rect(cell.child)


def draw_cells(grid):
    for row_idx in range(grid.row_count()):
        for cell in grid.get_cells_for_row(row_idx):
            draw_single_cell(cell)


def draw_rows(grid):
    for idx, cell in enumerate(grid.rows):
        color = get_random_pastel_color_rgb()
        print(cell)
        pygame.draw.rect(
            surface, color, pygame.Rect(cell.x, cell.y, cell.width, cell.height)
        )


def draw_colls(grid):
    for cell in grid.colls:
        color = get_random_pastel_color_rgb()
        print(cell)
        pygame.draw.rect(
            surface, color, pygame.Rect(cell.x, cell.y, cell.width, cell.height)
        )


# appen sys path
sys.path.append("/home/guest/dev/projects/render-review/render_review")
from geo import Grid, Rectangle, NestedRectangle, Align, Cell


# Initializing Pygame
pygame.init()
surface = pygame.display.set_mode((RES_X, RES_Y))

nested_rect = NestedRectangle(600, 300, 1920, 1080, child=Rectangle(0, 0, 600, 120))
cell = Cell(
    0,
    0,
    500,
    500,
    child=nested_rect
    # child=NestedRectangle(100, 100, 400, 400, child=Rectangle(0, 0, 1920, 1080)),
)
grid = Grid(0, 0, RES_X, RES_Y, 4, 6, cell)

# draw_rows(grid)
# draw_colls(grid)

# run
clock = pygame.time.Clock()
run = True
draw_cells(grid)
# draw_single_cell(grid.cells[0][1])
while run:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
    # surface.fill(pygame.Color(0, 0, 0, 1))
    # draw_nested_rect(nested_rect)
    # draw_single_cell(cell)
    pygame.display.update()
    # cell.x += 10
    # cell.child.x += 1
    # cell.child.child.y += 1
    clock.tick(4)

pygame.quit()
