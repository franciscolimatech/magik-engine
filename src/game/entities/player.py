"""Player entity for tile-by-tile movement."""

from __future__ import annotations

from dataclasses import dataclass

from src.game import colors
from src.game.maps.test_map import is_walkable
from src.game.settings import TILE_SIZE


@dataclass
class Player:
    x: int
    y: int
    name: str = "Aventureiro"
    facing: tuple[int, int] = (0, 1)

    @property
    def position(self) -> tuple[int, int]:
        return self.x, self.y

    def move(self, dx: int, dy: int, map_data: list[str]) -> bool:
        if dx == 0 and dy == 0:
            return False
        self.facing = (dx, dy)
        target_x = self.x + dx
        target_y = self.y + dy
        if not is_walkable(map_data, target_x, target_y):
            return False
        self.x = target_x
        self.y = target_y
        return True

    def facing_position(self) -> tuple[int, int]:
        return self.x + self.facing[0], self.y + self.facing[1]

    def draw(self, pygame, surface) -> None:
        pixel_x = self.x * TILE_SIZE
        pixel_y = self.y * TILE_SIZE
        shadow = pygame.Rect(pixel_x + 7, pixel_y + 22, 18, 6)
        body = pygame.Rect(pixel_x + 8, pixel_y + 8, 16, 18)
        pygame.draw.rect(surface, colors.PLAYER_SHADOW, shadow)
        pygame.draw.rect(surface, colors.PLAYER, body)
