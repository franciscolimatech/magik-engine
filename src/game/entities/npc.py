"""NPC entity for simple interaction."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from src.game.dialogue import DialogueChoice
from src.game.entities.player import Player
from src.game.assets import blit_scaled
from src.game.settings import TILE_SIZE


@dataclass
class NPC:
    x: int
    y: int
    name: str
    dialogues: str | Iterable[str]
    choice: DialogueChoice | None = None
    npc_id: str | None = None
    location_id: str | None = None

    def __post_init__(self) -> None:
        if isinstance(self.dialogues, str):
            self.dialogues = (self.dialogues,)
        else:
            self.dialogues = tuple(self.dialogues)

    @property
    def dialogue(self) -> str:
        return self.dialogues[0] if self.dialogues else ""

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
        tile_size = camera.tile_size if camera else TILE_SIZE
        scale = tile_size / TILE_SIZE
        pixel_x, pixel_y = camera.tile_to_screen(self.x, self.y) if camera else (self.x * TILE_SIZE, self.y * TILE_SIZE)
        if assets:
            if highlighted:
                marker_size = (
                    max(1, int(assets.interaction_marker.get_width() * scale)),
                    max(1, int(assets.interaction_marker.get_height() * scale)),
                )
                blit_scaled(pygame, surface, assets.interaction_marker, (pixel_x + int(10 * scale), pixel_y - int(10 * scale)), marker_size)
            blit_scaled(pygame, surface, assets.npc, (pixel_x, pixel_y), tile_size)
            return
        pygame.draw.rect(surface, (81, 167, 255), pygame.Rect(pixel_x + 9, pixel_y + 9, 14, 17))
