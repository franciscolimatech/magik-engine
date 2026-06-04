"""NPC entity for simple interaction."""

from __future__ import annotations

from dataclasses import dataclass

from src.game import colors
from src.game.entities.player import Player
from src.game.settings import TILE_SIZE


@dataclass(frozen=True)
class NPC:
    x: int
    y: int
    name: str
    dialogue: str

    @property
    def position(self) -> tuple[int, int]:
        return self.x, self.y

    def is_adjacent_to(self, player: Player) -> bool:
        return abs(self.x - player.x) + abs(self.y - player.y) == 1

    def is_in_front_of(self, player: Player) -> bool:
        return self.position == player.facing_position()

    def can_interact(self, player: Player) -> bool:
        return self.is_in_front_of(player)

    def draw(self, pygame, surface, camera=None) -> None:
        world_x = self.x * TILE_SIZE
        world_y = self.y * TILE_SIZE
        pixel_x, pixel_y = camera.world_to_screen(world_x, world_y) if camera else (world_x, world_y)
        shadow = pygame.Rect(pixel_x + 7, pixel_y + 22, 18, 6)
        body = pygame.Rect(pixel_x + 9, pixel_y + 9, 14, 17)
        pygame.draw.rect(surface, colors.NPC_SHADOW, shadow)
        pygame.draw.rect(surface, colors.NPC, body)
