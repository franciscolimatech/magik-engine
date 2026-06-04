"""Primitive drawing helpers for the no-assets prototype."""

from __future__ import annotations

from src.game import colors
from src.game.settings import TILE_SIZE


def draw_tile(pygame, surface, tile: str, x: int, y: int) -> None:
    rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
    base_color = colors.FLOOR_ALT if (x // TILE_SIZE + y // TILE_SIZE) % 2 else colors.FLOOR
    pygame.draw.rect(surface, base_color, rect)
    if tile == "#":
        pygame.draw.rect(surface, colors.WALL, rect)
        inset = rect.inflate(-8, -8)
        pygame.draw.rect(surface, colors.WALL_DARK, inset)
