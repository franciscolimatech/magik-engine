from pathlib import Path

import pytest

from src.core.combat import apply_physical_damage
from src.core.enemies import list_official_enemies
from src.core.items import list_official_items
from src.core.magic_marks import list_magic_marks
from src.core.npcs import create_npc, list_npcs
from src.core.official_npcs import (
    filter_official_npcs_by_area,
    filter_official_npcs_by_location,
    get_official_npc,
    list_official_npcs,
    list_official_npcs_by_area,
    list_official_npcs_by_location,
    validate_official_npc_references,
    validate_unique_official_npc_ids,
)
from src.core.quests import (
    filter_quests_by_area,
    filter_quests_by_npc,
    get_official_quest,
    list_official_quests,
    list_official_quests_by_area,
    list_official_quests_by_npc,
    validate_quest_references,
    validate_unique_quest_ids,
)
from src.core.world import list_official_locations
from src.storage.json_storage import JSONStorage
from src.storage.memory import MemoryStorage


def test_official_npc_catalog_file_loads() -> None:
    storage = JSONStorage(Path("data"))

    npcs = list_official_npcs(storage)

    assert len(npcs) == 66
    assert {"Velho Nox", "Bruxa das Águas Calmas", "Prefeita Mirela Ondaclara"}.issubset(
        {npc.name for npc in npcs}
    )


def test_official_quest_catalog_file_loads() -> None:
    storage = JSONStorage(Path("data"))

    quests = list_official_quests(storage)

    assert len(quests) == 77
    assert {"Missão da Marca Sombria", "O Futuro Afogado", "Uma Pena de Sabedoria"}.issubset(
        {quest.title for quest in quests}
    )


def test_official_npc_ids_are_unique() -> None:
    npcs = list_official_npcs(JSONStorage(Path("data")))

    validate_unique_official_npc_ids(npcs)

    ids = [npc.id for npc in npcs]
    assert len(ids) == len(set(ids))


def test_official_quest_ids_are_unique() -> None:
    quests = list_official_quests(JSONStorage(Path("data")))

    validate_unique_quest_ids(quests)

    ids = [quest.id for quest in quests]
    assert len(ids) == len(set(ids))


def test_get_official_npc_by_id() -> None:
    npc = get_official_npc(JSONStorage(Path("data")), "velho-nox")

    assert npc.name == "Velho Nox"
    assert npc.area == "Floresta do Avesso"
    assert npc.grants_magic_mark_id == "marca-sombria"
    assert "missao-da-marca-sombria" in npc.quest_ids


def test_get_official_quest_by_id() -> None:
    quest = get_official_quest(JSONStorage(Path("data")), "missao-da-marca-sombria")

    assert quest.title == "Missão da Marca Sombria"
    assert quest.giver_npc_id == "velho-nox"
    assert quest.reward_magic_mark_ids == ["marca-sombria"]
    assert quest.status == "catalogo"


def test_missing_official_npc_or_quest_raises_error() -> None:
    storage = JSONStorage(Path("data"))

    with pytest.raises(ValueError, match="NPC oficial nao encontrado"):
        get_official_npc(storage, "npc-inexistente")
    with pytest.raises(ValueError, match="Missao oficial nao encontrada"):
        get_official_quest(storage, "missao-inexistente")


def test_filter_official_npcs_by_area_and_location() -> None:
    storage = JSONStorage(Path("data"))
    npcs = list_official_npcs(storage)

    by_area = filter_official_npcs_by_area(npcs, "floresta do avesso")
    by_location = filter_official_npcs_by_location(npcs, "floresta-do-avesso")

    assert by_area == list_official_npcs_by_area(storage, "Floresta do Avesso")
    assert by_location == list_official_npcs_by_location(storage, "floresta-do-avesso")
    assert any(npc.id == "senhor-espelho" for npc in by_area)
    assert by_area == by_location


def test_filter_quests_by_area_and_npc() -> None:
    storage = JSONStorage(Path("data"))
    quests = list_official_quests(storage)

    by_area = filter_quests_by_area(quests, "floresta viridian")
    by_npc = filter_quests_by_npc(quests, "velho-nox")

    assert by_area == list_official_quests_by_area(storage, "Floresta Viridian")
    assert by_npc == list_official_quests_by_npc(storage, "velho-nox")
    assert any(quest.id == "missao-da-marca-viridian" for quest in by_area)
    assert {quest.id for quest in by_npc} == {
        "missao-da-marca-sombria",
        "o-sonho-que-nao-era-meu",
    }


def test_official_npc_location_and_magic_mark_references_are_valid() -> None:
    storage = JSONStorage(Path("data"))
    npcs = list_official_npcs(storage)
    quests = list_official_quests(storage)
    valid_location_ids = {location.id for location in list_official_locations(storage)}
    valid_magic_mark_ids = {mark.id for mark in list_magic_marks(storage)}
    valid_quest_ids = {quest.id for quest in quests}

    validate_official_npc_references(npcs, valid_location_ids, valid_magic_mark_ids, valid_quest_ids)


def test_quest_location_magic_mark_and_npc_references_are_valid() -> None:
    storage = JSONStorage(Path("data"))
    quests = list_official_quests(storage)
    npcs = list_official_npcs(storage)
    valid_location_ids = {location.id for location in list_official_locations(storage)}
    valid_magic_mark_ids = {mark.id for mark in list_magic_marks(storage)}
    valid_npc_ids = {npc.id for npc in npcs}
    valid_item_ids = {item.id for item in list_official_items(storage)}
    valid_enemy_ids = {enemy.id for enemy in list_official_enemies(storage)}

    validate_quest_references(
        quests,
        valid_location_ids,
        valid_item_ids,
        valid_magic_mark_ids,
        valid_enemy_ids,
        valid_npc_ids,
    )


def test_missing_or_empty_official_npc_json_uses_safe_fallback(tmp_path) -> None:
    storage = JSONStorage(tmp_path)

    assert list_official_npcs(storage) == []

    storage.write_json("official_npcs.json", {})
    assert list_official_npcs(storage) == []


def test_missing_or_empty_quest_json_uses_safe_fallback(tmp_path) -> None:
    storage = JSONStorage(tmp_path)

    assert list_official_quests(storage) == []

    storage.write_json("quests.json", {})
    assert list_official_quests(storage) == []


def test_active_npcs_continue_separate_from_official_catalog() -> None:
    storage = MemoryStorage({"npcs.json": {"npcs": []}})

    active_npc = create_npc(storage, "Nara", "comerciante")
    official_npcs = list_official_npcs(storage)

    assert active_npc.id == "nara"
    assert [npc.id for npc in list_npcs(storage)] == ["nara"]
    assert official_npcs == []


def test_combat_rule_is_unchanged_by_official_npc_and_quest_catalogs() -> None:
    result = apply_physical_damage(current_health=20, armor=5, damage=8)

    assert result.current_health == 20
    assert result.armor == 0
    assert "excedente foi perdido" in result.description
