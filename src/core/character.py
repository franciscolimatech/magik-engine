"""Character sheet models and helpers."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class Character:
    name: str
    character_class: str
    max_health: int
    current_health: int
    armor: int
    equipment: list[str] = field(default_factory=list)
    living_weapon: str | None = None
    can_disappear_in_shadows: bool = False
    chain_debts: int = 0
    last_ikisaki_result: int | None = None
    ikisaki_available: bool = True

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["class"] = data.pop("character_class")
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Character":
        payload = dict(data)
        payload["character_class"] = payload.pop("class")
        return cls(**payload)


def create_miko_meu() -> Character:
    """Create the initial sheet for Miko Meu."""
    return Character(
        name="Miko Meu",
        character_class="Sombrio",
        max_health=25,
        current_health=25,
        armor=5,
        equipment=["Cajado", "Corrente de Ferro"],
        living_weapon="Ikisaki",
        can_disappear_in_shadows=True,
        chain_debts=0,
        last_ikisaki_result=None,
        ikisaki_available=True,
    )


def find_character(characters: list[Character], name: str) -> Character | None:
    normalized = name.strip().casefold()
    return next((character for character in characters if character.name.casefold() == normalized), None)


def load_characters(storage: Any) -> list[Character]:
    default_data = {"characters": [create_miko_meu().to_dict()]}
    data = storage.read_json("characters.json", default=default_data)
    characters_data = data.get("characters", []) if isinstance(data, dict) else data
    return [Character.from_dict(character_data) for character_data in characters_data]


def save_characters(storage: Any, characters: list[Character]) -> None:
    storage.write_json("characters.json", {"characters": [character.to_dict() for character in characters]})


def load_or_create_miko(storage: Any) -> Character:
    characters = load_characters(storage)
    miko = find_character(characters, "Miko Meu")
    if miko is None:
        miko = create_miko_meu()
        characters.append(miko)
        save_characters(storage, characters)
    return miko
