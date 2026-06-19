"""Declarative narrative interactions for playable areas.

Area interactions are lightweight exploration hooks. They can show text and
record narrative flags, but they do not create quests, rewards, inventory
changes, combat effects, or mechanical bonuses.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.game.save import GameSave
    from src.storage.types import JsonStore


SHADOW_TRAIL_INTERACTION_ID = "rastro-da-sombra-clareira"
FOREST_CLEARING_AREA_ID = "floresta-do-avesso-clareira"
FLORESTA_DO_AVESSO_LOCATION_ID = "floresta-do-avesso"
NOX_TRAIL_MENTIONED_FLAG = "nox_mencionou_rastro_na_clareira"
SHADOW_TRAIL_INVESTIGATED_FLAG = "investigou_rastro_da_sombra"


@dataclass(frozen=True)
class AreaInteraction:
    id: str
    area_id: str
    x: int
    y: int
    label: str
    speaker: str
    messages: tuple[str, ...]
    location_id: str | None = None
    required_story_flags: tuple[str, ...] = ()
    blocked_story_flags: tuple[str, ...] = ()
    add_story_flags: tuple[str, ...] = ()
    consequence_id: str | None = None
    consequence_text: str | None = None
    repeatable: bool = True
    marker_style: str = "rune"
    narrative_conditions: dict[str, Any] = field(init=False)
    narrative_effects: dict[str, Any] = field(init=False)

    def __post_init__(self) -> None:
        conditions: dict[str, Any] = {}
        if self.required_story_flags:
            conditions["required_story_flags"] = list(self.required_story_flags)
        if self.blocked_story_flags:
            conditions["blocked_story_flags"] = list(self.blocked_story_flags)
        effects: dict[str, Any] = {}
        if self.add_story_flags:
            effects["add_story_flags"] = list(self.add_story_flags)
        if self.consequence_id and self.consequence_text:
            effects["narrative_consequence"] = {
                "id": self.consequence_id,
                "location_id": self.location_id,
                "text": self.consequence_text,
            }
        object.__setattr__(self, "narrative_conditions", conditions)
        object.__setattr__(self, "narrative_effects", effects)

    @property
    def position(self) -> tuple[int, int]:
        return self.x, self.y


SHADOW_TRAIL_INTERACTION = AreaInteraction(
    id=SHADOW_TRAIL_INTERACTION_ID,
    area_id=FOREST_CLEARING_AREA_ID,
    x=8,
    y=5,
    label="investigar rastro",
    speaker="Rastro na Clareira",
    messages=(
        "O ar dobra ao redor dos seus dedos.",
        "Por um instante, sua sombra se atrasa.",
    ),
    location_id=FLORESTA_DO_AVESSO_LOCATION_ID,
    required_story_flags=(NOX_TRAIL_MENTIONED_FLAG,),
    add_story_flags=(SHADOW_TRAIL_INVESTIGATED_FLAG,),
    consequence_id="rastro-da-sombra-investigado",
    consequence_text="O personagem investigou o rastro da sombra na Clareira da Floresta do Avesso.",
    repeatable=True,
    marker_style="rune",
)


AREA_INTERACTIONS = (SHADOW_TRAIL_INTERACTION,)


def list_area_interactions(area_id: str | None = None) -> list[AreaInteraction]:
    if area_id is None:
        return list(AREA_INTERACTIONS)
    normalized = area_id.strip().casefold()
    return [interaction for interaction in AREA_INTERACTIONS if interaction.area_id.casefold() == normalized]


def get_area_interaction(interaction_id: str) -> AreaInteraction:
    normalized = interaction_id.strip().casefold()
    for interaction in AREA_INTERACTIONS:
        if interaction.id.casefold() == normalized:
            return interaction
    raise ValueError(f"Interacao de area nao encontrada: {interaction_id}.")


def area_interaction_available(
    interaction: AreaInteraction,
    save: "GameSave | None",
    location_id: str,
) -> bool:
    from src.game.narrative_conditions import conditions_met

    if interaction.location_id is not None and interaction.location_id != location_id:
        return False
    if not interaction.narrative_conditions:
        return True
    if save is None:
        return False
    return conditions_met(save, interaction.narrative_conditions)


def apply_area_interaction_effects_to_storage(
    storage: "JsonStore",
    interaction: AreaInteraction,
    save_id: str = "default",
) -> "GameSave":
    from src.game.narrative_conditions import apply_narrative_effects_to_storage

    return apply_narrative_effects_to_storage(storage, save_id, interaction.narrative_effects)
