"""Official MAGIK NPC catalog helpers.

This catalog is reference lore only. It does not replace active NPCs stored in
``npcs.json`` and does not grant marks, sell items, or start quests
automatically.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import unicodedata
from typing import Any

from src.core.magic_marks import list_magic_marks
from src.core.world import list_official_locations
from src.storage.types import JsonStore


@dataclass(frozen=True)
class OfficialNPC:
    id: str
    name: str
    area: str
    location_ids: list[str]
    role: str
    description: str
    function: str = ""
    grants_magic_mark_id: str | None = None
    sells: list[str] = field(default_factory=list)
    quest_ids: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "OfficialNPC":
        try:
            npc = cls(
                id=str(data["id"]),
                name=str(data["name"]),
                area=str(data.get("area", "")),
                location_ids=list(data.get("location_ids", [])),
                role=str(data.get("role", "outro")),
                description=str(data.get("description", "")),
                function=str(data.get("function", "")),
                grants_magic_mark_id=data.get("grants_magic_mark_id"),
                sells=list(data.get("sells", [])),
                quest_ids=list(data.get("quest_ids", [])),
                tags=list(data.get("tags", [])),
                notes=list(data.get("notes", [])),
            )
        except KeyError as exc:
            raise ValueError(f"NPC oficial invalido: campo ausente {exc}.") from exc
        validate_official_npc(npc)
        return npc


def default_official_npc_catalog_data() -> dict[str, Any]:
    return {"official_npcs": []}


def list_official_npcs(storage: JsonStore) -> list[OfficialNPC]:
    data = storage.read_json("official_npcs.json", default=default_official_npc_catalog_data())
    npc_data = _read_collection(data, "official_npcs", "official_npcs.json")
    npcs = [OfficialNPC.from_dict(item) for item in npc_data]
    validate_unique_official_npc_ids(npcs)
    validate_official_npc_references(
        npcs,
        valid_location_ids=_load_valid_location_ids(storage),
        valid_magic_mark_ids=_load_valid_magic_mark_ids(storage),
    )
    return npcs


def get_official_npc(storage: JsonStore, npc_id: str) -> OfficialNPC:
    normalized = npc_id.strip().casefold()
    for npc in list_official_npcs(storage):
        if npc.id.casefold() == normalized:
            return npc
    raise ValueError(f"NPC oficial nao encontrado: {npc_id}.")


def filter_official_npcs_by_area(npcs: list[OfficialNPC], area: str) -> list[OfficialNPC]:
    normalized = _normalize_text(area)
    return [npc for npc in npcs if _normalize_text(npc.area) == normalized]


def filter_official_npcs_by_location(npcs: list[OfficialNPC], location_id: str) -> list[OfficialNPC]:
    normalized = location_id.strip().casefold()
    return [npc for npc in npcs if any(item.casefold() == normalized for item in npc.location_ids)]


def list_official_npcs_by_area(storage: JsonStore, area: str) -> list[OfficialNPC]:
    return filter_official_npcs_by_area(list_official_npcs(storage), area)


def list_official_npcs_by_location(storage: JsonStore, location_id: str) -> list[OfficialNPC]:
    return filter_official_npcs_by_location(list_official_npcs(storage), location_id)


def validate_unique_official_npc_ids(npcs: list[OfficialNPC]) -> None:
    seen: set[str] = set()
    for npc in npcs:
        normalized = npc.id.strip().casefold()
        if not normalized:
            raise ValueError("Id do NPC oficial e obrigatorio.")
        if normalized in seen:
            raise ValueError(f"Id de NPC oficial duplicado: {npc.id}.")
        seen.add(normalized)


def validate_official_npc_references(
    npcs: list[OfficialNPC],
    valid_location_ids: set[str],
    valid_magic_mark_ids: set[str],
    valid_quest_ids: set[str] | None = None,
) -> None:
    for npc in npcs:
        for location_id in npc.location_ids:
            if location_id not in valid_location_ids:
                raise ValueError(f"Local invalido em {npc.id}: {location_id}.")
        if npc.grants_magic_mark_id and npc.grants_magic_mark_id not in valid_magic_mark_ids:
            raise ValueError(f"Marca magica invalida em {npc.id}: {npc.grants_magic_mark_id}.")
        if valid_quest_ids is not None:
            for quest_id in npc.quest_ids:
                if quest_id not in valid_quest_ids:
                    raise ValueError(f"Missao invalida em {npc.id}: {quest_id}.")


def validate_official_npc(npc: OfficialNPC) -> None:
    if not npc.id.strip():
        raise ValueError("Id do NPC oficial e obrigatorio.")
    if not npc.name.strip():
        raise ValueError("Nome do NPC oficial e obrigatorio.")
    if not npc.area.strip():
        raise ValueError("Area do NPC oficial e obrigatoria.")
    if not npc.role.strip():
        raise ValueError("Papel do NPC oficial e obrigatorio.")
    if not npc.description.strip():
        raise ValueError("Descricao do NPC oficial e obrigatoria.")
    if not all(isinstance(location_id, str) for location_id in npc.location_ids):
        raise ValueError("location_ids deve conter apenas strings.")
    if not all(isinstance(item, str) for item in npc.sells):
        raise ValueError("sells deve conter apenas strings.")
    if not all(isinstance(quest_id, str) for quest_id in npc.quest_ids):
        raise ValueError("quest_ids deve conter apenas strings.")
    if not all(isinstance(tag, str) for tag in npc.tags):
        raise ValueError("tags deve conter apenas strings.")
    if not all(isinstance(note, str) for note in npc.notes):
        raise ValueError("notes deve conter apenas strings.")


def _load_valid_location_ids(storage: JsonStore) -> set[str]:
    return {location.id for location in list_official_locations(storage)}


def _load_valid_magic_mark_ids(storage: JsonStore) -> set[str]:
    return {mark.id for mark in list_magic_marks(storage)}


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
