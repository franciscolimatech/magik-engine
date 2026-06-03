"""World state helpers for known MAGIK locations."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from src.storage.types import JsonStore


@dataclass(frozen=True)
class WorldLocation:
    name: str
    type: str
    notes: str = ""
    narrative_hooks: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WorldLocation":
        try:
            return cls(
                name=str(data["name"]),
                type=str(data["type"]),
                notes=str(data.get("notes", "")),
                narrative_hooks=list(data.get("narrative_hooks", [])),
            )
        except KeyError as exc:
            raise ValueError(f"Local do mundo invalido: campo ausente {exc}.") from exc


KNOWN_LOCATIONS: tuple[WorldLocation, ...] = (
    WorldLocation("País de Magik", "região"),
    WorldLocation("Cidade de Pedralume", "capital"),
    WorldLocation("Floresta Viridian", "floresta"),
    WorldLocation("Campos dos Kriots", "regiao"),
    WorldLocation("Lago das Carpas Profetas", "lago"),
    WorldLocation("Estrada do Viajante", "estrada"),
    WorldLocation("Floresta do Avesso", "floresta"),
    WorldLocation("Brejo do Esquecimento", "brejo"),
    WorldLocation("Montanhas Trippi", "montanha"),
    WorldLocation("Vale Vermilion", "vale"),
    WorldLocation("Penhascos do Último Passo", "penhasco"),
    WorldLocation("Avelgard", "cidade"),
    WorldLocation("Varnhollow", "cidade"),
    WorldLocation("Corvenn", "cidade"),
    WorldLocation("Dunwall", "cidade"),
    WorldLocation("Brisvale", "cidade"),
    WorldLocation("Norwick", "cidade"),
    WorldLocation("Eldermor", "cidade"),
    WorldLocation("Arkenfor", "cidade"),
    WorldLocation("Velharth", "cidade"),
    WorldLocation("Stonewatch", "cidade"),
    WorldLocation("Redmoor", "cidade"),
    WorldLocation("Thornwich", "cidade"),
    WorldLocation("Vilarejo dos Gatos Autistas", "mini vilarejo"),
    WorldLocation("Vilarejo dos Gatos com TDAH", "mini vilarejo"),
)


def default_world_state() -> dict[str, Any]:
    return {"locations": [location.to_dict() for location in KNOWN_LOCATIONS]}


def ensure_world_state(storage: JsonStore) -> dict[str, Any]:
    data = storage.read_json("world_state.json", default=default_world_state())
    if not isinstance(data, dict):
        raise ValueError("world_state.json deve conter um objeto JSON.")

    locations = data.get("locations")
    if not isinstance(locations, list):
        data["locations"] = [location.to_dict() for location in KNOWN_LOCATIONS]
        storage.write_json("world_state.json", data)
        return data

    known_by_name = {location.name: location for location in KNOWN_LOCATIONS}
    existing_names = {str(location.get("name")) for location in locations if isinstance(location, dict)}
    missing_locations = [
        location.to_dict()
        for name, location in known_by_name.items()
        if name not in existing_names
    ]
    if missing_locations:
        data["locations"] = locations + missing_locations
        storage.write_json("world_state.json", data)
    return data


def list_locations(storage: JsonStore) -> list[WorldLocation]:
    data = ensure_world_state(storage)
    locations = data["locations"]
    if not all(isinstance(location, dict) for location in locations):
        raise ValueError("Cada local em world_state.json deve ser um objeto JSON.")
    return [WorldLocation.from_dict(location) for location in locations]
