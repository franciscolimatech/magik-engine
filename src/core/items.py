"""Official MAGIK item catalog helpers.

Items in this module are reference data only. Effects are stored as text for
the master and are not applied to combat, inventory, healing, armor, or rolls.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import unicodedata
from typing import Any

from src.core.world import list_official_locations
from src.storage.types import JsonStore


@dataclass(frozen=True)
class OfficialItem:
    id: str
    name: str
    type: str
    description: str
    origin: str
    rarity: str
    effect: str
    region_ids: list[str] = field(default_factory=list)
    location_ids: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "OfficialItem":
        try:
            item = cls(
                id=str(data["id"]),
                name=str(data["name"]),
                type=str(data.get("type", "especial")),
                description=str(data.get("description", "")),
                origin=str(data.get("origin", "")),
                rarity=str(data.get("rarity", "")),
                effect=str(data.get("effect", "")),
                region_ids=list(data.get("region_ids", [])),
                location_ids=list(data.get("location_ids", [])),
                tags=list(data.get("tags", [])),
                notes=list(data.get("notes", [])),
            )
        except KeyError as exc:
            raise ValueError(f"Item oficial invalido: campo ausente {exc}.") from exc
        validate_item(item)
        return item


def default_item_catalog_data() -> dict[str, Any]:
    return {"items": []}


def list_official_items(storage: JsonStore) -> list[OfficialItem]:
    data = storage.read_json("items.json", default=default_item_catalog_data())
    items_data = _read_collection(data, "items", "items.json")
    items = [OfficialItem.from_dict(item) for item in items_data]
    validate_unique_item_ids(items)
    validate_item_locations(items, _load_valid_location_ids(storage))
    return items


def get_official_item(storage: JsonStore, item_id: str) -> OfficialItem:
    normalized = item_id.strip().casefold()
    for item in list_official_items(storage):
        if item.id.casefold() == normalized:
            return item
    raise ValueError(f"Item oficial nao encontrado: {item_id}.")


def filter_items_by_rarity(items: list[OfficialItem], rarity: str) -> list[OfficialItem]:
    normalized = _normalize_text(rarity)
    return [item for item in items if _normalize_text(item.rarity) == normalized]


def filter_items_by_origin(items: list[OfficialItem], origin: str) -> list[OfficialItem]:
    normalized = _normalize_text(origin)
    return [item for item in items if normalized in _normalize_text(item.origin)]


def list_items_by_rarity(storage: JsonStore, rarity: str) -> list[OfficialItem]:
    return filter_items_by_rarity(list_official_items(storage), rarity)


def list_items_by_origin(storage: JsonStore, origin: str) -> list[OfficialItem]:
    return filter_items_by_origin(list_official_items(storage), origin)


def validate_unique_item_ids(items: list[OfficialItem]) -> None:
    seen: set[str] = set()
    for item in items:
        normalized = item.id.strip().casefold()
        if not normalized:
            raise ValueError("Id do item oficial e obrigatorio.")
        if normalized in seen:
            raise ValueError(f"Id de item oficial duplicado: {item.id}.")
        seen.add(normalized)


def validate_item_locations(items: list[OfficialItem], valid_location_ids: set[str]) -> None:
    for item in items:
        for location_id in item.location_ids:
            if location_id not in valid_location_ids:
                raise ValueError(f"Local invalido em {item.id}: {location_id}.")


def validate_item(item: OfficialItem) -> None:
    if not item.id.strip():
        raise ValueError("Id do item oficial e obrigatorio.")
    if not item.name.strip():
        raise ValueError("Nome do item oficial e obrigatorio.")
    if not item.type.strip():
        raise ValueError("Tipo do item oficial e obrigatorio.")
    if not item.description.strip():
        raise ValueError("Descricao do item oficial e obrigatoria.")
    if not item.origin.strip():
        raise ValueError("Origem do item oficial e obrigatoria.")
    if not item.rarity.strip():
        raise ValueError("Raridade do item oficial e obrigatoria.")
    if not item.effect.strip():
        raise ValueError("Efeito do item oficial e obrigatorio.")
    if not all(isinstance(region_id, str) for region_id in item.region_ids):
        raise ValueError("region_ids deve conter apenas strings.")
    if not all(isinstance(location_id, str) for location_id in item.location_ids):
        raise ValueError("location_ids deve conter apenas strings.")
    if not all(isinstance(tag, str) for tag in item.tags):
        raise ValueError("tags deve conter apenas strings.")
    if not all(isinstance(note, str) for note in item.notes):
        raise ValueError("notes deve conter apenas strings.")


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


def _normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.strip().casefold())
    return "".join(character for character in normalized if not unicodedata.combining(character))
