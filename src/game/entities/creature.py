"""Creature entity for map encounters in the 2D prototype."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from src.core.creatures import Creature as CoreCreature
from src.core.creatures import list_creatures
from src.game.dialogue import DialogueChoice, DialogueOption, normalize_messages
from src.game.entities.player import Player
from src.game.settings import TILE_SIZE
from src.storage.types import JsonStore


DEFAULT_CREATURE_ID = "sombra-rastejante"
DEFAULT_CREATURE_NAME = "Sombra Rastejante"
DEFAULT_CREATURE_DESCRIPTION = "Uma forma baixa e escura se arrasta pelo chao, como sombra que esqueceu o dono."


@dataclass
class Creature:
    id: str
    name: str
    x: int
    y: int
    description: str
    current_health: int
    max_health: int
    armor: int = 0
    hostile: bool = True
    dialogues: str | Iterable[str] = ()

    def __post_init__(self) -> None:
        self.dialogues = normalize_messages(self.dialogues or self.description)

    @property
    def position(self) -> tuple[int, int]:
        return self.x, self.y

    def is_in_front_of(self, player: Player) -> bool:
        return self.position == player.facing_position()

    def can_interact(self, player: Player) -> bool:
        return self.is_in_front_of(player)

    def encounter_choice(self) -> DialogueChoice:
        return DialogueChoice(
            question="O que voce faz?",
            options=(
                DialogueOption(
                    text="Observar",
                    response=f"{self.description} Vida: {self.current_health}/{self.max_health}. Armadura: {self.armor}.",
                    tags=("observar",),
                    event="observe",
                ),
                DialogueOption(
                    text="Ameacar",
                    response=f"{self.name} recua um passo, mas a sombra dela parece ficar no lugar.",
                    tags=("ameacar",),
                    event="threaten",
                ),
                DialogueOption(
                    text="Recuar",
                    response="Voce recua antes que o encontro vire algo pior.",
                    tags=("recuar",),
                    event="retreat",
                ),
                DialogueOption(
                    text="Iniciar combate",
                    response="Combate visual ainda nao implementado.",
                    tags=("combate",),
                    event="start_combat",
                ),
            ),
        )

    def encounter_messages(self) -> tuple[str, ...]:
        return (
            self.description,
            f"Vida: {self.current_health}/{self.max_health} | Armadura: {self.armor}",
        )

    def draw(self, pygame, surface, camera=None, assets=None, highlighted: bool = False) -> None:
        world_x = self.x * TILE_SIZE
        world_y = self.y * TILE_SIZE
        pixel_x, pixel_y = camera.world_to_screen(world_x, world_y) if camera else (world_x, world_y)
        if assets:
            if highlighted:
                surface.blit(assets.interaction_marker, (pixel_x + 10, pixel_y - 10))
            surface.blit(assets.creature, (pixel_x, pixel_y))
            return
        pygame.draw.rect(surface, (82, 55, 120), pygame.Rect(pixel_x + 8, pixel_y + 12, 16, 15))


def load_game_creature(storage: JsonStore | None, x: int, y: int) -> Creature:
    core_creature = _load_first_core_creature(storage)
    if core_creature is None:
        return default_creature(x, y)
    return from_core_creature(core_creature, x, y)


def from_core_creature(creature: CoreCreature, x: int, y: int) -> Creature:
    return Creature(
        id=creature.id,
        name=creature.name,
        x=x,
        y=y,
        description=creature.description or f"{creature.name} observa em silencio.",
        current_health=creature.current_health,
        max_health=creature.max_health,
        armor=creature.armor,
        hostile=True,
    )


def default_creature(x: int, y: int) -> Creature:
    return Creature(
        id=DEFAULT_CREATURE_ID,
        name=DEFAULT_CREATURE_NAME,
        x=x,
        y=y,
        description=DEFAULT_CREATURE_DESCRIPTION,
        current_health=12,
        max_health=12,
        armor=2,
        hostile=True,
    )


def _load_first_core_creature(storage: JsonStore | None) -> CoreCreature | None:
    if storage is None:
        return None
    try:
        creatures = list_creatures(storage)
    except ValueError:
        return None
    return creatures[0] if creatures else None
