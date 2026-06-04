"""NPC entity for simple interaction."""

from __future__ import annotations

from dataclasses import dataclass

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

    def draw(self, pygame, surface, camera=None, assets=None, highlighted: bool = False) -> None:
        world_x = self.x * TILE_SIZE
        world_y = self.y * TILE_SIZE
        pixel_x, pixel_y = camera.world_to_screen(world_x, world_y) if camera else (world_x, world_y)
        if assets:
            if highlighted:
                surface.blit(assets.interaction_marker, (pixel_x + 10, pixel_y - 10))
            surface.blit(assets.npc, (pixel_x, pixel_y))
            return
        pygame.draw.rect(surface, (81, 167, 255), pygame.Rect(pixel_x + 9, pixel_y + 9, 14, 17))
