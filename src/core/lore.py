"""Unified read-only queries for official MAGIK lore catalogs.

This module composes official catalog data only. It does not activate quests,
apply item effects, teach spells, grant magic marks, spawn encounters, or
change combat state.
"""

from __future__ import annotations

import unicodedata
from typing import Any

from src.core.enemies import OfficialEnemy, list_official_enemies
from src.core.items import OfficialItem, list_official_items
from src.core.magic_marks import MagicMark, filter_magic_marks_by_school, list_magic_marks
from src.core.official_npcs import (
    OfficialNPC,
    filter_official_npcs_by_area,
    filter_official_npcs_by_location,
    list_official_npcs,
)
from src.core.quests import (
    OfficialQuest,
    filter_quests_by_area,
    filter_quests_by_npc,
    list_official_quests,
)
from src.core.spells import OfficialSpell, filter_spells_by_school, list_official_spells
from src.core.world import (
    OfficialLocation,
    OfficialRegion,
    get_location_by_id,
    list_official_locations,
    list_regions,
)
from src.storage.types import JsonStore


def list_lore_locations(storage: JsonStore) -> list[OfficialLocation]:
    return list_official_locations(storage)


def list_lore_npcs_by_area(storage: JsonStore, area: str) -> list[OfficialNPC]:
    return filter_official_npcs_by_area(list_official_npcs(storage), area)


def list_lore_npcs_by_location(storage: JsonStore, location_id: str) -> list[OfficialNPC]:
    return filter_official_npcs_by_location(list_official_npcs(storage), location_id)


def list_lore_quests_by_area(storage: JsonStore, area: str) -> list[OfficialQuest]:
    return filter_quests_by_area(list_official_quests(storage), area)


def list_lore_quests_by_npc(storage: JsonStore, npc_id: str) -> list[OfficialQuest]:
    return filter_quests_by_npc(list_official_quests(storage), npc_id)


def list_lore_enemies_by_region(storage: JsonStore, region_id: str) -> list[OfficialEnemy]:
    normalized = region_id.strip().casefold()
    return [
        enemy
        for enemy in list_official_enemies(storage)
        if any(item.casefold() == normalized for item in enemy.region_ids)
    ]


def list_lore_enemies_by_location(storage: JsonStore, location_id: str) -> list[OfficialEnemy]:
    normalized = location_id.strip().casefold()
    return [
        enemy
        for enemy in list_official_enemies(storage)
        if any(item.casefold() == normalized for item in enemy.location_ids)
    ]


def list_lore_items_by_origin(storage: JsonStore, origin: str) -> list[OfficialItem]:
    normalized = _normalize_text(origin)
    return [item for item in list_official_items(storage) if normalized in _normalize_text(item.origin)]


def list_lore_items_by_rarity(storage: JsonStore, rarity: str) -> list[OfficialItem]:
    normalized = _normalize_text(rarity)
    return [item for item in list_official_items(storage) if _normalize_text(item.rarity) == normalized]


def list_lore_items_by_location(storage: JsonStore, location_id: str) -> list[OfficialItem]:
    normalized = location_id.strip().casefold()
    return [
        item
        for item in list_official_items(storage)
        if any(location.casefold() == normalized for location in item.location_ids)
    ]


def list_lore_spells_by_school(storage: JsonStore, school: str) -> list[OfficialSpell]:
    return filter_spells_by_school(list_official_spells(storage), school)


def list_lore_spells_by_location(storage: JsonStore, location: OfficialLocation) -> list[OfficialSpell]:
    normalized_location_name = _normalize_text(location.name)
    return [
        spell
        for spell in list_official_spells(storage)
        if _normalize_text(spell.region) == normalized_location_name
    ]


def list_lore_magic_marks_by_school(storage: JsonStore, school: str) -> list[MagicMark]:
    return filter_magic_marks_by_school(list_magic_marks(storage), school)


def get_lore_summary_for_location(storage: JsonStore, location_id: str) -> dict[str, Any]:
    location = get_location_by_id(storage, location_id)
    regions = list_regions(storage)
    region = _find_region(regions, location.region_id)
    locations_by_id = {item.id: item for item in list_official_locations(storage)}
    connected_locations = [
        locations_by_id[connected_id]
        for connected_id in location.connections
        if connected_id in locations_by_id
    ]
    npcs = list_lore_npcs_by_location(storage, location.id)
    quests = _list_quests_by_location(storage, location.id)
    enemies = list_lore_enemies_by_location(storage, location.id)
    items = list_lore_items_by_location(storage, location.id)
    spells = list_lore_spells_by_location(storage, location)
    marks = _magic_marks_granted_by_npcs(storage, npcs)

    return {
        "location": location.to_dict(),
        "region": region.to_dict() if region else None,
        "connected_locations": [item.to_dict() for item in connected_locations],
        "npcs": [npc.to_dict() for npc in npcs],
        "quests": [quest.to_dict() for quest in quests],
        "enemies": [enemy.to_dict() for enemy in enemies],
        "items": [item.to_dict() for item in items],
        "spells": [spell.to_dict() for spell in spells],
        "magic_marks": [mark.to_dict() for mark in marks],
    }


def _list_quests_by_location(storage: JsonStore, location_id: str) -> list[OfficialQuest]:
    normalized = location_id.strip().casefold()
    return [
        quest
        for quest in list_official_quests(storage)
        if any(item.casefold() == normalized for item in quest.location_ids)
    ]


def _magic_marks_granted_by_npcs(storage: JsonStore, npcs: list[OfficialNPC]) -> list[MagicMark]:
    mark_ids = {npc.grants_magic_mark_id for npc in npcs if npc.grants_magic_mark_id}
    if not mark_ids:
        return []
    return [mark for mark in list_magic_marks(storage) if mark.id in mark_ids]


def _find_region(regions: list[OfficialRegion], region_id: str | None) -> OfficialRegion | None:
    if not region_id:
        return None
    normalized = region_id.strip().casefold()
    for region in regions:
        if region.id.casefold() == normalized:
            return region
    return None


def _normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.strip().casefold())
    return "".join(character for character in normalized if not unicodedata.combining(character))
