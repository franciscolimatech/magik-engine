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

    def resize(self, screen_width: int, screen_height: int, tile_size: int | None = None) -> None:
        self.screen_width = max(1, screen_width)
        self.screen_height = max(1, screen_height)
        if tile_size is not None:
            self.tile_size = max(1, tile_size)

    def follow(self, target_tile_x: int, target_tile_y: int, map_width: int, map_height: int) -> None:
        target_pixel_x = target_tile_x * self.tile_size + self.tile_size // 2
        target_pixel_y = target_tile_y * self.tile_size + self.tile_size // 2
        desired_x = target_pixel_x - self.screen_width // 2
        desired_y = target_pixel_y - self.screen_height // 2
        world_width = map_width * self.tile_size
        world_height = map_height * self.tile_size
        self.offset_x = _centered_offset(desired_x, world_width, self.screen_width)
        self.offset_y = _centered_offset(desired_y, world_height, self.screen_height)

    def world_to_screen(self, pixel_x: int, pixel_y: int) -> tuple[int, int]:
        return pixel_x - self.offset_x, pixel_y - self.offset_y

    def tile_to_screen(self, tile_x: int, tile_y: int) -> tuple[int, int]:
        return self.world_to_screen(tile_x * self.tile_size, tile_y * self.tile_size)


def _clamp(value: int, minimum: int, maximum: int) -> int:
    return max(minimum, min(maximum, value))


def _centered_offset(desired: int, world_size: int, screen_size: int) -> int:
    if world_size <= screen_size:
        return -((screen_size - world_size) // 2)
    return _clamp(desired, 0, world_size - screen_size)
