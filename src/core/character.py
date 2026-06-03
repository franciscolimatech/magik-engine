"""Character sheet models and helpers."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import re
from typing import Any

from src.core.abilities import Ability
from src.storage.types import JsonStore


MIKO_ID = "miko-meu"


@dataclass
class Character:
    name: str
    character_class: str
    max_health: int
    current_health: int
    armor: int
    id: str = ""
    equipment: list[str] = field(default_factory=list)
    abilities: list[dict[str, Any]] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    status: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    special_systems: list[str] = field(default_factory=list)
    living_weapon: str | None = None
    can_disappear_in_shadows: bool = False
    chain_debts: int = 0
    last_ikisaki_result: int | None = None
    ikisaki_available: bool = True

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["class"] = data.pop("character_class")
        if not data["id"]:
            data["id"] = generate_character_id(self.name)
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Character":
        payload = dict(data)
        try:
            payload["character_class"] = payload.pop("class")
            payload.setdefault("id", generate_character_id(str(payload["name"])))
            payload.setdefault("equipment", [])
            payload.setdefault("abilities", [])
            payload.setdefault("notes", [])
            payload.setdefault("status", [])
            payload.setdefault("tags", [])
            payload.setdefault("special_systems", [])
            payload.setdefault("living_weapon", None)
            payload.setdefault("can_disappear_in_shadows", False)
            payload.setdefault("chain_debts", 0)
            payload.setdefault("last_ikisaki_result", None)
            payload.setdefault("ikisaki_available", True)
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
        id=MIKO_ID,
        equipment=["Cajado", "Corrente de Ferro"],
        abilities=[
            Ability(
                id="ikisaki_roulette",
                name="Roleta Sombria: Dez Elos de Ikisaki",
                description="Usa o sistema especial da Ikisaki.",
                type="unica",
                use="livre",
                effect="Rola 1d10 na Roleta Sombria e aplica o elo sorteado.",
                cost="Preco conforme o elo sorteado.",
                requires_test=False,
                suggested_test=None,
                notes="Use a opcao especial da Ikisaki no menu principal.",
            ).to_dict(),
            Ability(
                id="shadow_staff",
                name="Cajado Sombrio",
                description="Usa o sistema especial do Cajado Sombrio.",
                type="magia",
                use="livre",
                effect="Permite escolher uma magia simples do Cajado Sombrio.",
                cost="Sem mana nesta etapa.",
                requires_test=True,
                suggested_test="Teste sugerido pela magia escolhida.",
                notes="Use a opcao especial do Cajado Sombrio no menu principal.",
            ).to_dict(),
            Ability(
                id="disappear_in_shadows",
                name="Desaparecer nas Sombras",
                description="Miko pode desaparecer nas sombras.",
                type="utilidade",
                use="livre",
                effect="Ajuda Miko a sumir, se esconder ou reposicionar narrativamente nas sombras.",
                cost="Depende da cena e da decisao do mestre.",
                requires_test=True,
                suggested_test="Furtividade ou Agilidade",
            ).to_dict(),
            Ability(
                id="shadow_switch",
                name="Switch Sombrio",
                description="Risco narrativo ligado as Dividas de Corrente e a Ikisaki.",
                type="transformacao",
                use="limitado",
                effect="Indica uma possivel tomada sombria da cena pela maldicao.",
                cost="Grave; depende da cena e da decisao do mestre.",
                usage_limit=1,
                remaining_uses=1,
                requires_test=False,
                notes="Nao ativa automaticamente; o mestre decide quando e como entra em cena.",
            ).to_dict(),
        ],
        notes=[],
        status=[],
        tags=["personagem inicial", "sombrio"],
        special_systems=["ikisaki", "shadow_staff"],
        living_weapon="Ikisaki",
        can_disappear_in_shadows=True,
        chain_debts=0,
        last_ikisaki_result=None,
        ikisaki_available=True,
    )


def find_character(characters: list[Character], name: str) -> Character | None:
    normalized = name.strip().casefold()
    return next((character for character in characters if character.name.casefold() == normalized), None)


def find_character_by_id(characters: list[Character], character_id: str) -> Character | None:
    normalized = character_id.strip().casefold()
    return next((character for character in characters if character.id.casefold() == normalized), None)


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

    characters = [Character.from_dict(character_data) for character_data in characters_data]
    if not characters:
        characters = [create_miko_meu()]
        save_characters(storage, characters)
    return characters


def save_characters(storage: JsonStore, characters: list[Character]) -> None:
    _ensure_unique_ids(characters)
    storage.write_json("characters.json", {"characters": [character.to_dict() for character in characters]})


def list_characters(storage: JsonStore) -> list[Character]:
    return load_characters(storage)


def get_character(storage: JsonStore, character_id: str) -> Character:
    character = find_character_by_id(load_characters(storage), character_id)
    if character is None:
        raise ValueError(f"Personagem nao encontrado: {character_id}.")
    return character


def create_character(
    storage: JsonStore,
    name: str,
    character_class: str,
    max_health: int,
    armor: int = 0,
    character_id: str | None = None,
    equipment: list[str] | None = None,
    abilities: list[dict[str, Any]] | None = None,
    notes: list[str] | None = None,
    status: list[str] | None = None,
    tags: list[str] | None = None,
    special_systems: list[str] | None = None,
) -> Character:
    if not name.strip():
        raise ValueError("Nome do personagem e obrigatorio.")
    if not character_class.strip():
        raise ValueError("Classe do personagem e obrigatoria.")
    if max_health <= 0:
        raise ValueError("Vida maxima deve ser maior que zero.")
    if armor < 0:
        raise ValueError("Armadura nao pode ser negativa.")

    characters = load_characters(storage)
    if character_id is not None:
        new_id = generate_character_id(character_id)
        if find_character_by_id(characters, new_id) is not None:
            raise ValueError(f"Id de personagem duplicado: {new_id}.")
    else:
        new_id = _unique_character_id(characters, generate_character_id(name))
    character = Character(
        id=new_id,
        name=name.strip(),
        character_class=character_class.strip(),
        max_health=max_health,
        current_health=max_health,
        armor=armor,
        equipment=equipment or [],
        abilities=abilities or [],
        notes=notes or [],
        status=status or [],
        tags=tags or [],
        special_systems=special_systems or [],
    )
    characters.append(character)
    save_characters(storage, characters)
    return character


def update_character(storage: JsonStore, character: Character) -> Character:
    characters = load_characters(storage)
    existing_index = next(
        (index for index, current in enumerate(characters) if current.id.casefold() == character.id.casefold()),
        None,
    )
    if existing_index is None:
        raise ValueError(f"Personagem nao encontrado: {character.id}.")
    characters[existing_index] = character
    save_characters(storage, characters)
    return character


def remove_character(storage: JsonStore, character_id: str, confirm: bool = False) -> Character:
    if not confirm:
        raise ValueError("Remocao de personagem exige confirmacao explicita.")
    characters = load_characters(storage)
    character = get_character(storage, character_id)
    remaining = [current for current in characters if current.id.casefold() != character.id.casefold()]
    save_characters(storage, remaining)
    return character


def update_character_health(storage: JsonStore, character_id: str, current_health: int) -> Character:
    character = get_character(storage, character_id)
    if current_health < 0:
        raise ValueError("Vida atual nao pode ser negativa.")
    if current_health > character.max_health:
        raise ValueError("Vida atual nao pode ultrapassar a vida maxima.")
    character.current_health = current_health
    return update_character(storage, character)


def update_character_armor(storage: JsonStore, character_id: str, armor: int) -> Character:
    character = get_character(storage, character_id)
    if armor < 0:
        raise ValueError("Armadura nao pode ser negativa.")
    character.armor = armor
    return update_character(storage, character)


def add_equipment(storage: JsonStore, character_id: str, item: str) -> Character:
    cleaned = item.strip()
    if not cleaned:
        raise ValueError("Equipamento nao pode ser vazio.")
    character = get_character(storage, character_id)
    character.equipment.append(cleaned)
    return update_character(storage, character)


def remove_equipment(storage: JsonStore, character_id: str, item: str) -> Character:
    cleaned = item.strip()
    character = get_character(storage, character_id)
    try:
        character.equipment.remove(cleaned)
    except ValueError as exc:
        raise ValueError(f"Equipamento nao encontrado: {cleaned}.") from exc
    return update_character(storage, character)


def add_note(storage: JsonStore, character_id: str, note: str) -> Character:
    cleaned = note.strip()
    if not cleaned:
        raise ValueError("Observacao nao pode ser vazia.")
    character = get_character(storage, character_id)
    character.notes.append(cleaned)
    return update_character(storage, character)


def load_or_create_miko(storage: JsonStore) -> Character:
    characters = load_characters(storage)
    miko = find_character_by_id(characters, MIKO_ID) or find_character(characters, "Miko Meu")
    if miko is None:
        miko = create_miko_meu()
        characters.append(miko)
        save_characters(storage, characters)
    return miko


def save_character(storage: JsonStore, character: Character) -> None:
    characters = load_characters(storage)
    existing_index = next(
        (index for index, current in enumerate(characters) if current.id.casefold() == character.id.casefold()),
        None,
    )
    if existing_index is None:
        characters.append(character)
    else:
        characters[existing_index] = character
    save_characters(storage, characters)


def generate_character_id(name: str) -> str:
    normalized = _normalize_ascii(name)
    slug = re.sub(r"[^a-z0-9]+", "-", normalized).strip("-")
    return slug or "personagem"


def _unique_character_id(characters: list[Character], base_id: str) -> str:
    normalized_base = generate_character_id(base_id)
    existing_ids = {character.id.casefold() for character in characters}
    if normalized_base.casefold() not in existing_ids:
        return normalized_base
    suffix = 2
    while f"{normalized_base}-{suffix}".casefold() in existing_ids:
        suffix += 1
    return f"{normalized_base}-{suffix}"


def _ensure_unique_ids(characters: list[Character]) -> None:
    seen: set[str] = set()
    for character in characters:
        if not character.id:
            character.id = generate_character_id(character.name)
        normalized = character.id.casefold()
        if normalized in seen:
            raise ValueError(f"Id de personagem duplicado: {character.id}.")
        seen.add(normalized)


def _normalize_ascii(value: str) -> str:
    import unicodedata

    normalized = unicodedata.normalize("NFKD", value.strip().casefold())
    return "".join(character for character in normalized if not unicodedata.combining(character))
