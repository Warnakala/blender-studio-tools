import sys
import random
import pygame
import colorsys
from typing import Tuple

RES_X = int(1920 / 2)
RES_Y = int(1920 / 2)


def get_random_pastel_color_rgb() -> Tuple[float, float, float]:
    """Returns a randomly generated color with high brightness and low saturation."""

    hue = random.random()
    saturation = random.uniform(0.25, 0.33)
    brightness = random.uniform(0.75, 0.83)

    color = colorsys.hsv_to_rgb(hue, saturation, brightness)
    return (int(color[0] * 255), int(color[1] * 255), int(255 * color[2]))


def draw_cells(grid):
    for row_idx in range(grid.row_count()):
        for cell in grid.get_cells_for_row(row_idx):
            color = get_random_pastel_color_rgb()
            pygame.draw.rect(
                surface, color, pygame.Rect(cell.x, cell.y, cell.width, cell.height)
            )
            # color = get_random_pastel_color_rgb()
            fac = 0.5
            color = (int(color[0] * fac), int(color[1] * fac), int(color[2] * fac))
            pygame.draw.rect(
                surface,
                color,
                pygame.Rect(
                    cell.rect.x, cell.rect.y, cell.rect.width, cell.rect.height
                ),
            )


def draw_rows(grid):
    for idx, cell in enumerate(grid.rows):
        color = get_random_pastel_color_rgb()
        print(cell)
        pygame.draw.rect(
            surface, color, pygame.Rect(cell.x, cell.y, cell.width, cell.height)
        )


def draw_colls(grid):
    for idx, cell in enumerate(grid.colls):
        color = get_random_pastel_color_rgb()
        print(cell)
        pygame.draw.rect(
            surface, color, pygame.Rect(cell.x, cell.y, cell.width, cell.height)
        )


# appen sys path
sys.path.append("/home/guest/dev/projects/render-review/render_review")
from geo import Grid, Rectangle, Align


# Initializing Pygame
pygame.init()
surface = pygame.display.set_mode((RES_X, RES_Y))

# draw grid
grid = Grid(0, 0, RES_X, RES_Y, 4, 6, Rectangle(0, 0, 1920, 1080), align=Align.CENTER)
# draw_rows(grid)
# draw_colls(grid)
draw_cells(grid)

# run
run = True
while run:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
    pygame.display.update()

pygame.quit()
