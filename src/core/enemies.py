"""Official MAGIK enemy catalog helpers.

This module keeps lore catalog data separate from active creatures. Enemies
listed here are reference entries only; they are not spawned, balanced, or
connected to combat automatically.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from src.core.world import list_official_locations
from src.storage.types import JsonStore


@dataclass(frozen=True)
class EnemyDrop:
    name: str
    chance: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EnemyDrop":
        try:
            drop = cls(
                name=str(data["name"]),
                chance=str(data["chance"]),
            )
        except KeyError as exc:
            raise ValueError(f"Drop de inimigo invalido: campo ausente {exc}.") from exc
        validate_enemy_drop(drop)
        return drop


@dataclass(frozen=True)
class OfficialEnemy:
    id: str
    name: str
    type: str
    description: str
    region_ids: list[str] = field(default_factory=list)
    location_ids: list[str] = field(default_factory=list)
    max_health: int = 1
    armor: int = 0
    drops: list[EnemyDrop] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["drops"] = [drop.to_dict() for drop in self.drops]
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "OfficialEnemy":
        try:
            enemy = cls(
                id=str(data["id"]),
                name=str(data["name"]),
                type=str(data.get("type", "criatura")),
                description=str(data.get("description", "")),
                region_ids=list(data.get("region_ids", [])),
                location_ids=list(data.get("location_ids", [])),
                max_health=int(data.get("max_health", 1)),
                armor=int(data.get("armor", 0)),
                drops=[EnemyDrop.from_dict(drop) for drop in data.get("drops", [])],
                tags=list(data.get("tags", [])),
                notes=list(data.get("notes", [])),
            )
        except KeyError as exc:
            raise ValueError(f"Inimigo oficial invalido: campo ausente {exc}.") from exc
        validate_enemy(enemy)
        return enemy


def default_enemy_catalog_data() -> dict[str, Any]:
    return {"enemies": []}


def list_official_enemies(storage: JsonStore) -> list[OfficialEnemy]:
    data = storage.read_json("enemies.json", default=default_enemy_catalog_data())
    enemies_data = _read_collection(data, "enemies", "enemies.json")
    enemies = [OfficialEnemy.from_dict(item) for item in enemies_data]
    validate_unique_enemy_ids(enemies)
    validate_enemy_locations(enemies, _load_valid_location_ids(storage))
    return enemies


def get_official_enemy(storage: JsonStore, enemy_id: str) -> OfficialEnemy:
    normalized = enemy_id.strip().casefold()
    for enemy in list_official_enemies(storage):
        if enemy.id.casefold() == normalized:
            return enemy
    raise ValueError(f"Inimigo oficial nao encontrado: {enemy_id}.")


def validate_unique_enemy_ids(enemies: list[OfficialEnemy]) -> None:
    seen: set[str] = set()
    for enemy in enemies:
        normalized = enemy.id.strip().casefold()
        if not normalized:
            raise ValueError("Id do inimigo oficial e obrigatorio.")
        if normalized in seen:
            raise ValueError(f"Id de inimigo oficial duplicado: {enemy.id}.")
        seen.add(normalized)


def validate_enemy_locations(enemies: list[OfficialEnemy], valid_location_ids: set[str]) -> None:
    for enemy in enemies:
        for location_id in enemy.location_ids:
            if location_id not in valid_location_ids:
                raise ValueError(f"Local invalido em {enemy.id}: {location_id}.")


def validate_enemy(enemy: OfficialEnemy) -> None:
    if not enemy.id.strip():
        raise ValueError("Id do inimigo oficial e obrigatorio.")
    if not enemy.name.strip():
        raise ValueError("Nome do inimigo oficial e obrigatorio.")
    if not enemy.type.strip():
        raise ValueError("Tipo do inimigo oficial e obrigatorio.")
    if not enemy.description.strip():
        raise ValueError("Descricao do inimigo oficial e obrigatoria.")
    if enemy.max_health <= 0:
        raise ValueError("Vida maxima do inimigo oficial deve ser maior que zero.")
    if enemy.armor < 0:
        raise ValueError("Armadura do inimigo oficial nao pode ser negativa.")
    if not all(isinstance(region_id, str) for region_id in enemy.region_ids):
        raise ValueError("region_ids deve conter apenas strings.")
    if not all(isinstance(location_id, str) for location_id in enemy.location_ids):
        raise ValueError("location_ids deve conter apenas strings.")
    if not all(isinstance(tag, str) for tag in enemy.tags):
        raise ValueError("tags deve conter apenas strings.")
    if not all(isinstance(note, str) for note in enemy.notes):
        raise ValueError("notes deve conter apenas strings.")


def validate_enemy_drop(drop: EnemyDrop) -> None:
    if not drop.name.strip():
        raise ValueError("Nome do drop e obrigatorio.")
    if not drop.chance.strip():
        raise ValueError("Chance do drop e obrigatoria.")


def _load_valid_location_ids(storage: JsonStore) -> set[str]:
    return {location.id for location in list_official_locations(storage)}


def _read_collection(data: Any, key: str, filename: str) -> list[dict[str, Any]]:
    if isinstance(data, dict):
        collection = data.get(key, [])
    elif isinstance(data, list):
        collection = data
    else:
        raise ValueError(f"{filename} deve conter uma lista ou um objeto com a chave '{key}'.")
    if not isinstance(collection, list):
        raise ValueError(f"A chave '{key}' em {filename} deve conter uma lista.")
    if not all(isinstance(item, dict) for item in collection):
        raise ValueError(f"Cada item em {filename} deve ser um objeto JSON.")
    return collection
