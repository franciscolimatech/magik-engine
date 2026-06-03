"""Creature and enemy management."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import re
from typing import Any

from src.core.abilities import Ability
from src.core.combat import apply_magical_damage, apply_physical_damage
from src.core.magic import apply_healing
from src.storage.types import JsonStore


CREATURE_TYPES = {
    "criatura",
    "inimigo",
    "chefe",
    "animal",
    "entidade",
    "morto-vivo",
    "espirito",
    "humanoide",
    "outro",
}


@dataclass
class Creature:
    id: str
    name: str
    type: str
    max_health: int
    current_health: int
    armor: int = 0
    description: str = ""
    abilities: list[dict[str, Any]] = field(default_factory=list)
    status: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    location: str | None = None
    threat_level: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Creature":
        try:
            creature = cls(
                id=str(data["id"]),
                name=str(data["name"]),
                type=str(data.get("type", "criatura")),
                max_health=int(data["max_health"]),
                current_health=int(data.get("current_health", data["max_health"])),
                armor=int(data.get("armor", 0)),
                description=str(data.get("description", "")),
                abilities=list(data.get("abilities", [])),
                status=list(data.get("status", [])),
                tags=list(data.get("tags", [])),
                notes=list(data.get("notes", [])),
                location=data.get("location"),
                threat_level=data.get("threat_level"),
            )
        except KeyError as exc:
            raise ValueError(f"Criatura invalida: campo ausente {exc}.") from exc
        validate_creature(creature)
        return creature


def default_creature_data() -> dict[str, Any]:
    return {"creatures": []}


def list_creatures(storage: JsonStore) -> list[Creature]:
    data = storage.read_json("creatures.json", default=default_creature_data())
    if isinstance(data, dict):
        creatures_data = data.get("creatures", [])
    elif isinstance(data, list):
        creatures_data = data
    else:
        raise ValueError("creatures.json deve conter uma lista ou um objeto com a chave 'creatures'.")
    if not isinstance(creatures_data, list):
        raise ValueError("A chave 'creatures' deve conter uma lista.")
    return [Creature.from_dict(item) for item in creatures_data]


def save_creatures(storage: JsonStore, creatures: list[Creature]) -> None:
    _ensure_unique_ids(creatures)
    storage.write_json("creatures.json", {"creatures": [creature.to_dict() for creature in creatures]})


def get_creature(storage: JsonStore, creature_id: str) -> Creature:
    normalized = creature_id.strip().casefold()
    for creature in list_creatures(storage):
        if creature.id.casefold() == normalized:
            return creature
    raise ValueError(f"Criatura nao encontrada: {creature_id}.")


def create_creature(
    storage: JsonStore,
    name: str,
    creature_type: str,
    max_health: int,
    armor: int = 0,
    creature_id: str | None = None,
    description: str = "",
    location: str | None = None,
    threat_level: str | None = None,
    tags: list[str] | None = None,
) -> Creature:
    if not name.strip():
        raise ValueError("Nome da criatura e obrigatorio.")
    if max_health <= 0:
        raise ValueError("Vida maxima deve ser maior que zero.")
    if armor < 0:
        raise ValueError("Armadura nao pode ser negativa.")

    creatures = list_creatures(storage)
    new_id = _resolve_new_id(creatures, creature_id or name, explicit=creature_id is not None)
    creature = Creature(
        id=new_id,
        name=name.strip(),
        type=creature_type.strip() or "criatura",
        max_health=max_health,
        current_health=max_health,
        armor=armor,
        description=description.strip(),
        location=location.strip() if location else None,
        threat_level=threat_level.strip() if threat_level else None,
        tags=tags or [],
    )
    validate_creature(creature)
    creatures.append(creature)
    save_creatures(storage, creatures)
    return creature


def update_creature(storage: JsonStore, creature: Creature) -> Creature:
    validate_creature(creature)
    creatures = list_creatures(storage)
    for index, current in enumerate(creatures):
        if current.id.casefold() == creature.id.casefold():
            creatures[index] = creature
            save_creatures(storage, creatures)
            return creature
    raise ValueError(f"Criatura nao encontrada: {creature.id}.")


def remove_creature(storage: JsonStore, creature_id: str) -> Creature:
    creature = get_creature(storage, creature_id)
    save_creatures(storage, [current for current in list_creatures(storage) if current.id != creature.id])
    return creature


def update_creature_health(storage: JsonStore, creature_id: str, current_health: int) -> Creature:
    creature = get_creature(storage, creature_id)
    if current_health < 0:
        raise ValueError("Vida atual nao pode ser negativa.")
    if current_health > creature.max_health:
        raise ValueError("Vida atual nao pode ultrapassar a vida maxima.")
    creature.current_health = current_health
    return update_creature(storage, creature)


def update_creature_armor(storage: JsonStore, creature_id: str, armor: int) -> Creature:
    creature = get_creature(storage, creature_id)
    if armor < 0:
        raise ValueError("Armadura nao pode ser negativa.")
    creature.armor = armor
    return update_creature(storage, creature)


def apply_physical_damage_to_creature(storage: JsonStore, creature_id: str, damage: int) -> tuple[Creature, str]:
    creature = get_creature(storage, creature_id)
    result = apply_physical_damage(creature.current_health, creature.armor, damage)
    creature.current_health = result.current_health
    creature.armor = result.armor
    update_creature(storage, creature)
    return creature, result.description


def apply_magical_damage_to_creature(storage: JsonStore, creature_id: str, damage: int) -> tuple[Creature, str]:
    creature = get_creature(storage, creature_id)
    result = apply_magical_damage(creature.current_health, creature.armor, damage)
    creature.current_health = result.current_health
    update_creature(storage, creature)
    return creature, result.description


def heal_creature(storage: JsonStore, creature_id: str, amount: int) -> tuple[Creature, str]:
    creature = get_creature(storage, creature_id)
    result = apply_healing(creature.current_health, creature.max_health, amount)
    creature.current_health = result.current_health
    update_creature(storage, creature)
    return creature, result.description


def add_creature_status(storage: JsonStore, creature_id: str, status: str) -> Creature:
    creature = get_creature(storage, creature_id)
    cleaned = _required_text(status, "status")
    if cleaned not in creature.status:
        creature.status.append(cleaned)
    return update_creature(storage, creature)


def remove_creature_status(storage: JsonStore, creature_id: str, status: str) -> Creature:
    creature = get_creature(storage, creature_id)
    cleaned = _required_text(status, "status")
    try:
        creature.status.remove(cleaned)
    except ValueError as exc:
        raise ValueError(f"Status nao encontrado: {cleaned}.") from exc
    return update_creature(storage, creature)


def add_creature_note(storage: JsonStore, creature_id: str, note: str) -> Creature:
    creature = get_creature(storage, creature_id)
    creature.notes.append(_required_text(note, "observacao"))
    return update_creature(storage, creature)


def validate_creature(creature: Creature) -> None:
    if not creature.id.strip():
        raise ValueError("Id da criatura e obrigatorio.")
    if not creature.name.strip():
        raise ValueError("Nome da criatura e obrigatorio.")
    if creature.type not in CREATURE_TYPES:
        valid = ", ".join(sorted(CREATURE_TYPES))
        raise ValueError(f"Tipo de criatura invalido. Use um destes: {valid}.")
    if creature.max_health <= 0:
        raise ValueError("Vida maxima deve ser maior que zero.")
    if creature.current_health < 0 or creature.current_health > creature.max_health:
        raise ValueError("Vida atual da criatura esta fora do intervalo permitido.")
    if creature.armor < 0:
        raise ValueError("Armadura nao pode ser negativa.")
    for ability in creature.abilities:
        Ability.from_dict(ability)


def generate_creature_id(name: str) -> str:
    normalized = _normalize_ascii(name)
    slug = re.sub(r"[^a-z0-9]+", "-", normalized).strip("-")
    return slug or "criatura"


def _resolve_new_id(creatures: list[Creature], value: str, explicit: bool) -> str:
    candidate = generate_creature_id(value)
    existing = {creature.id.casefold() for creature in creatures}
    if candidate.casefold() not in existing:
        return candidate
    if explicit:
        raise ValueError(f"Id de criatura duplicado: {candidate}.")
    suffix = 2
    while f"{candidate}-{suffix}".casefold() in existing:
        suffix += 1
    return f"{candidate}-{suffix}"


def _ensure_unique_ids(creatures: list[Creature]) -> None:
    seen: set[str] = set()
    for creature in creatures:
        normalized = creature.id.casefold()
        if normalized in seen:
            raise ValueError(f"Id de criatura duplicado: {creature.id}.")
        seen.add(normalized)


def _required_text(value: str, field_name: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise ValueError(f"O campo {field_name} e obrigatorio.")
    return cleaned


def _normalize_ascii(value: str) -> str:
    import unicodedata

    normalized = unicodedata.normalize("NFKD", value.strip().casefold())
    return "".join(character for character in normalized if not unicodedata.combining(character))
