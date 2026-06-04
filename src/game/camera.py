"""Simple camera for the 2D prototype."""

from __future__ import annotations

from dataclasses import dataclass

from src.game.settings import SCREEN_HEIGHT, SCREEN_WIDTH, TILE_SIZE


@dataclass
class Camera:
    screen_width: int = SCREEN_WIDTH
    screen_height: int = SCREEN_HEIGHT
    tile_size: int = TILE_SIZE
    offset_x: int = 0
    offset_y: int = 0

    def follow(self, target_tile_x: int, target_tile_y: int, map_width: int, map_height: int) -> None:
        target_pixel_x = target_tile_x * self.tile_size + self.tile_size // 2
        target_pixel_y = target_tile_y * self.tile_size + self.tile_size // 2
        desired_x = target_pixel_x - self.screen_width // 2
        desired_y = target_pixel_y - self.screen_height // 2
        max_x = max(0, map_width * self.tile_size - self.screen_width)
        max_y = max(0, map_height * self.tile_size - self.screen_height)
        self.offset_x = _clamp(desired_x, 0, max_x)
        self.offset_y = _clamp(desired_y, 0, max_y)

    def world_to_screen(self, pixel_x: int, pixel_y: int) -> tuple[int, int]:
        return pixel_x - self.offset_x, pixel_y - self.offset_y

    def tile_to_screen(self, tile_x: int, tile_y: int) -> tuple[int, int]:
        return self.world_to_screen(tile_x * self.tile_size, tile_y * self.tile_size)


def _clamp(value: int, minimum: int, maximum: int) -> int:
    return max(minimum, min(maximum, value))
