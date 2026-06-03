"""Character sheet models and helpers."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from src.storage.types import JsonStore


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
        try:
            payload["character_class"] = payload.pop("class")
            return cls(**payload)
        except KeyError as exc:
            raise ValueError(f"Ficha de personagem invalida: campo ausente {exc}.") from exc
        except TypeError as exc:
            raise ValueError("Ficha de personagem invalida: campos inesperados ou mal formatados.") from exc


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


def load_characters(storage: JsonStore) -> list[Character]:
    default_data = {"characters": [create_miko_meu().to_dict()]}
    data = storage.read_json("characters.json", default=default_data)

    if isinstance(data, dict):
        characters_data = data.get("characters", [])
    elif isinstance(data, list):
        characters_data = data
    else:
        raise ValueError("characters.json deve conter uma lista ou um objeto com a chave 'characters'.")

    if not isinstance(characters_data, list):
        raise ValueError("A chave 'characters' deve conter uma lista de fichas.")
    if not all(isinstance(character_data, dict) for character_data in characters_data):
        raise ValueError("Cada ficha em characters.json deve ser um objeto JSON.")

    return [Character.from_dict(character_data) for character_data in characters_data]


def save_characters(storage: JsonStore, characters: list[Character]) -> None:
    storage.write_json("characters.json", {"characters": [character.to_dict() for character in characters]})


def load_or_create_miko(storage: JsonStore) -> Character:
    characters = load_characters(storage)
    miko = find_character(characters, "Miko Meu")
    if miko is None:
        miko = create_miko_meu()
        characters.append(miko)
        save_characters(storage, characters)
    return miko


def save_character(storage: JsonStore, character: Character) -> None:
    characters = load_characters(storage)
    existing_index = next(
        (index for index, current in enumerate(characters) if current.name.casefold() == character.name.casefold()),
        None,
    )
    if existing_index is None:
        characters.append(character)
    else:
        characters[existing_index] = character
    save_characters(storage, characters)
