from pathlib import Path

import pytest

from src.core.character import load_or_create_miko
from src.core.combat import apply_physical_damage
from src.core.creatures import Creature, list_creatures
from src.core.lore import (
    get_lore_summary_for_location,
    list_lore_enemies_by_location,
    list_lore_items_by_origin,
    list_lore_items_by_rarity,
    list_lore_locations,
    list_lore_magic_marks_by_school,
    list_lore_npcs_by_area,
    list_lore_npcs_by_location,
    list_lore_quests_by_area,
    list_lore_quests_by_npc,
    list_lore_spells_by_school,
)
from src.core.npcs import create_npc, list_npcs
from src.storage.json_storage import JSONStorage
from src.storage.memory import MemoryStorage


CATALOG_FILES = (
    "regions.json",
    "locations.json",
    "enemies.json",
    "items.json",
    "spells.json",
    "magic_marks.json",
    "official_npcs.json",
    "quests.json",
)


def test_lore_summary_for_existing_location() -> None:
    storage = JSONStorage(Path("data"))

    summary = get_lore_summary_for_location(storage, "floresta-do-avesso")

    assert summary["location"]["id"] == "floresta-do-avesso"
    assert summary["region"]["id"] == "pais-de-magik"
    assert any(npc["id"] == "velho-nox" for npc in summary["npcs"])
    assert any(quest["id"] == "missao-da-marca-sombria" for quest in summary["quests"])
    assert any(mark["id"] == "marca-sombria" for mark in summary["magic_marks"])


def test_lore_summary_for_missing_location_raises_controlled_error() -> None:
    storage = JSONStorage(Path("data"))

    with pytest.raises(ValueError, match="Local oficial nao encontrado"):
        get_lore_summary_for_location(storage, "local-inexistente")


def test_lore_npcs_appear_in_correct_area_and_location() -> None:
    storage = JSONStorage(Path("data"))

    by_area = list_lore_npcs_by_area(storage, "Floresta do Avesso")
    by_location = list_lore_npcs_by_location(storage, "floresta-do-avesso")

    assert [npc.id for npc in by_area] == [npc.id for npc in by_location]
    assert {npc.id for npc in by_area} >= {"velho-nox", "senhor-espelho"}


def test_lore_quests_appear_by_area_and_npc() -> None:
    storage = JSONStorage(Path("data"))

    area_quests = list_lore_quests_by_area(storage, "Floresta Viridian")
    npc_quests = list_lore_quests_by_npc(storage, "velho-nox")

    assert any(quest.id == "missao-da-marca-viridian" for quest in area_quests)
    assert {quest.id for quest in npc_quests} == {
        "missao-da-marca-sombria",
        "o-sonho-que-nao-era-meu",
    }


def test_lore_filters_spells_items_and_magic_marks() -> None:
    storage = JSONStorage(Path("data"))

    shadow_spells = list_lore_spells_by_school(storage, "Sombras")
    common_items = list_lore_items_by_rarity(storage, "Comum")
    estrada_items = list_lore_items_by_origin(storage, "Estrada do Viajante")
    shadow_marks = list_lore_magic_marks_by_school(storage, "Sombras")

    assert len(shadow_spells) == 11
    assert all(spell.school == "Sombras" for spell in shadow_spells)
    assert common_items
    assert all(item.rarity == "Comum" for item in common_items)
    assert any(item.name == "Besta da Primeira Flecha" for item in estrada_items)
    assert [mark.id for mark in shadow_marks] == ["marca-sombria"]


def test_lore_lists_enemies_by_reliable_location() -> None:
    storage = JSONStorage(Path("data"))

    enemies = list_lore_enemies_by_location(storage, "floresta-do-avesso")

    assert enemies
    assert any(enemy.id == "sombras-perdidas" for enemy in enemies)
    assert all("floresta-do-avesso" in enemy.location_ids for enemy in enemies)


def test_lore_summary_includes_connected_locations() -> None:
    storage = JSONStorage(Path("data"))

    summary = get_lore_summary_for_location(storage, "floresta-do-avesso")
    connected_ids = {location["id"] for location in summary["connected_locations"]}

    assert connected_ids == {
        "brisvale",
        "norwick",
        "arkenford",
        "brejo-do-esquecimento",
    }


def test_lore_layer_does_not_change_catalog_json_files() -> None:
    base_path = Path("data")
    before = {
        filename: (base_path / filename).read_bytes()
        for filename in CATALOG_FILES
    }
    storage = JSONStorage(base_path)

    list_lore_locations(storage)
    get_lore_summary_for_location(storage, "floresta-do-avesso")
    list_lore_npcs_by_area(storage, "Floresta do Avesso")
    list_lore_quests_by_npc(storage, "velho-nox")

    after = {
        filename: (base_path / filename).read_bytes()
        for filename in CATALOG_FILES
    }
    assert after == before


def test_active_characters_npcs_and_creatures_remain_compatible_with_lore_layer() -> None:
    storage = MemoryStorage(
        {
            "npcs.json": {"npcs": []},
            "creatures.json": {
                "creatures": [
                    Creature(
                        id="criatura-teste",
                        name="Criatura Teste",
                        type="criatura",
                        max_health=10,
                        current_health=10,
                    ).to_dict()
                ]
            },
        }
    )

    miko = load_or_create_miko(storage)
    npc = create_npc(storage, "Nara", "comerciante")
    lore_summary = get_lore_summary_for_location(JSONStorage(Path("data")), "floresta-do-avesso")

    assert miko.id == "miko-meu"
    assert npc.id == "nara"
    assert [active_npc.id for active_npc in list_npcs(storage)] == ["nara"]
    assert [creature.id for creature in list_creatures(storage)] == ["criatura-teste"]
    assert lore_summary["location"]["id"] == "floresta-do-avesso"


def test_combat_rule_is_unchanged_by_lore_layer() -> None:
    result = apply_physical_damage(current_health=20, armor=5, damage=8)

    assert result.current_health == 20
    assert result.armor == 0
    assert "excedente foi perdido" in result.description
