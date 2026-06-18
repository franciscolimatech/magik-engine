"""Official MAGIK quest catalog helpers.

Quest entries are descriptive lore references. They are not active campaign
quests and do not grant rewards, progress, marks, items, or combat encounters
automatically.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import unicodedata
from typing import Any

from src.core.enemies import list_official_enemies
from src.core.items import list_official_items
from src.core.magic_marks import list_magic_marks
from src.core.world import list_official_locations
from src.storage.types import JsonStore


@dataclass(frozen=True)
class OfficialQuest:
    id: str
    title: str
    area: str
    giver_npc_id: str | None
    location_ids: list[str]
    type: str
    description: str
    objectives: list[str] = field(default_factory=list)
    encounter_notes: list[str] = field(default_factory=list)
    reward_text: str = ""
    reward_item_ids: list[str] = field(default_factory=list)
    reward_magic_mark_ids: list[str] = field(default_factory=list)
    enemy_refs: list[str] = field(default_factory=list)
    status: str = "catalogo"
    tags: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "OfficialQuest":
        try:
            quest = cls(
                id=str(data["id"]),
                title=str(data["title"]),
                area=str(data.get("area", "")),
                giver_npc_id=data.get("giver_npc_id"),
                location_ids=list(data.get("location_ids", [])),
                type=str(data.get("type", "secundaria")),
                description=str(data.get("description", "")),
                objectives=list(data.get("objectives", [])),
                encounter_notes=list(data.get("encounter_notes", [])),
                reward_text=str(data.get("reward_text", "")),
                reward_item_ids=list(data.get("reward_item_ids", [])),
                reward_magic_mark_ids=list(data.get("reward_magic_mark_ids", [])),
                enemy_refs=list(data.get("enemy_refs", [])),
                status=str(data.get("status", "catalogo")),
                tags=list(data.get("tags", [])),
                notes=list(data.get("notes", [])),
            )
        except KeyError as exc:
            raise ValueError(f"Missao oficial invalida: campo ausente {exc}.") from exc
        validate_official_quest(quest)
        return quest


def default_quest_catalog_data() -> dict[str, Any]:
    return {"quests": []}


def list_official_quests(storage: JsonStore) -> list[OfficialQuest]:
    data = storage.read_json("quests.json", default=default_quest_catalog_data())
    quest_data = _read_collection(data, "quests", "quests.json")
    quests = [OfficialQuest.from_dict(item) for item in quest_data]
    validate_unique_quest_ids(quests)
    validate_quest_references(
        quests,
        valid_location_ids=_load_valid_location_ids(storage),
        valid_item_ids=_load_valid_item_ids(storage),
        valid_magic_mark_ids=_load_valid_magic_mark_ids(storage),
        valid_enemy_ids=_load_valid_enemy_ids(storage),
    )
    return quests


def get_official_quest(storage: JsonStore, quest_id: str) -> OfficialQuest:
    normalized = quest_id.strip().casefold()
    for quest in list_official_quests(storage):
        if quest.id.casefold() == normalized:
            return quest
    raise ValueError(f"Missao oficial nao encontrada: {quest_id}.")


def filter_quests_by_area(quests: list[OfficialQuest], area: str) -> list[OfficialQuest]:
    normalized = _normalize_text(area)
    return [quest for quest in quests if _normalize_text(quest.area) == normalized]


def filter_quests_by_npc(quests: list[OfficialQuest], npc_id: str) -> list[OfficialQuest]:
    normalized = npc_id.strip().casefold()
    return [
        quest
        for quest in quests
        if quest.giver_npc_id is not None and quest.giver_npc_id.casefold() == normalized
    ]


def list_official_quests_by_area(storage: JsonStore, area: str) -> list[OfficialQuest]:
    return filter_quests_by_area(list_official_quests(storage), area)


def list_official_quests_by_npc(storage: JsonStore, npc_id: str) -> list[OfficialQuest]:
    return filter_quests_by_npc(list_official_quests(storage), npc_id)


def validate_unique_quest_ids(quests: list[OfficialQuest]) -> None:
    seen: set[str] = set()
    for quest in quests:
        normalized = quest.id.strip().casefold()
        if not normalized:
            raise ValueError("Id da missao oficial e obrigatorio.")
        if normalized in seen:
            raise ValueError(f"Id de missao oficial duplicado: {quest.id}.")
        seen.add(normalized)


def validate_quest_references(
    quests: list[OfficialQuest],
    valid_location_ids: set[str],
    valid_item_ids: set[str],
    valid_magic_mark_ids: set[str],
    valid_enemy_ids: set[str],
    valid_npc_ids: set[str] | None = None,
) -> None:
    for quest in quests:
        for location_id in quest.location_ids:
            if location_id not in valid_location_ids:
                raise ValueError(f"Local invalido em {quest.id}: {location_id}.")
        for item_id in quest.reward_item_ids:
            if item_id not in valid_item_ids:
                raise ValueError(f"Item de recompensa invalido em {quest.id}: {item_id}.")
        for mark_id in quest.reward_magic_mark_ids:
            if mark_id not in valid_magic_mark_ids:
                raise ValueError(f"Marca de recompensa invalida em {quest.id}: {mark_id}.")
        for enemy_id in quest.enemy_refs:
            if enemy_id not in valid_enemy_ids:
                raise ValueError(f"Inimigo citado invalido em {quest.id}: {enemy_id}.")
        if valid_npc_ids is not None and quest.giver_npc_id and quest.giver_npc_id not in valid_npc_ids:
            raise ValueError(f"NPC concedente invalido em {quest.id}: {quest.giver_npc_id}.")


def validate_official_quest(quest: OfficialQuest) -> None:
    if not quest.id.strip():
        raise ValueError("Id da missao oficial e obrigatorio.")
    if not quest.title.strip():
        raise ValueError("Titulo da missao oficial e obrigatorio.")
    if not quest.area.strip():
        raise ValueError("Area da missao oficial e obrigatoria.")
    if not quest.type.strip():
        raise ValueError("Tipo da missao oficial e obrigatorio.")
    if not quest.description.strip():
        raise ValueError("Descricao da missao oficial e obrigatoria.")
    if quest.status != "catalogo":
        raise ValueError("Missao oficial deve permanecer com status catalogo.")
    if not all(isinstance(location_id, str) for location_id in quest.location_ids):
        raise ValueError("location_ids deve conter apenas strings.")
    if not all(isinstance(objective, str) for objective in quest.objectives):
        raise ValueError("objectives deve conter apenas strings.")
    if not all(isinstance(note, str) for note in quest.encounter_notes):
        raise ValueError("encounter_notes deve conter apenas strings.")
    if not all(isinstance(item_id, str) for item_id in quest.reward_item_ids):
        raise ValueError("reward_item_ids deve conter apenas strings.")
    if not all(isinstance(mark_id, str) for mark_id in quest.reward_magic_mark_ids):
        raise ValueError("reward_magic_mark_ids deve conter apenas strings.")
    if not all(isinstance(enemy_id, str) for enemy_id in quest.enemy_refs):
        raise ValueError("enemy_refs deve conter apenas strings.")
    if not all(isinstance(tag, str) for tag in quest.tags):
        raise ValueError("tags deve conter apenas strings.")
    if not all(isinstance(note, str) for note in quest.notes):
        raise ValueError("notes deve conter apenas strings.")


def _load_valid_location_ids(storage: JsonStore) -> set[str]:
    return {location.id for location in list_official_locations(storage)}


def _load_valid_item_ids(storage: JsonStore) -> set[str]:
    return {item.id for item in list_official_items(storage)}


def _load_valid_magic_mark_ids(storage: JsonStore) -> set[str]:
    return {mark.id for mark in list_magic_marks(storage)}


def _load_valid_enemy_ids(storage: JsonStore) -> set[str]:
    return {enemy.id for enemy in list_official_enemies(storage)}


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
