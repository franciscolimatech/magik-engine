from pathlib import Path

import pytest

from src.core.combat import apply_physical_damage
from src.core.creatures import create_creature, list_creatures
from src.core.enemies import (
    get_official_enemy,
    list_official_enemies,
    validate_enemy_locations,
    validate_unique_enemy_ids,
)
from src.core.world import list_official_locations
from src.storage.json_storage import JSONStorage
from src.storage.memory import MemoryStorage


def test_official_enemy_catalog_file_loads() -> None:
    storage = JSONStorage(Path("data"))

    enemies = list_official_enemies(storage)

    assert len(enemies) == 85
    assert {"Goblins do véu", "Wrym Viridian", "Supervisor de Escavação"}.issubset(
        {enemy.name for enemy in enemies}
    )


def test_official_enemy_ids_are_unique() -> None:
    storage = JSONStorage(Path("data"))
    enemies = list_official_enemies(storage)

    validate_unique_enemy_ids(enemies)

    ids = [enemy.id for enemy in enemies]
    assert len(ids) == len(set(ids))


def test_get_official_enemy_by_id() -> None:
    storage = JSONStorage(Path("data"))

    enemy = get_official_enemy(storage, "goblins-do-veu")

    assert enemy.name == "Goblins do véu"
    assert enemy.max_health == 10
    assert enemy.armor == 5
    assert enemy.drops[0].name == "Flecha Torta"


def test_official_enemies_have_minimum_fields() -> None:
    storage = JSONStorage(Path("data"))

    enemies = list_official_enemies(storage)

    assert all(enemy.id for enemy in enemies)
    assert all(enemy.name for enemy in enemies)
    assert all(enemy.type for enemy in enemies)
    assert all(enemy.description for enemy in enemies)
    assert all(enemy.max_health > 0 for enemy in enemies)
    assert all(enemy.armor >= 0 for enemy in enemies)
    assert all("oficial" in enemy.tags for enemy in enemies)
    assert all("lore" in enemy.tags for enemy in enemies)


def test_missing_enemy_json_uses_safe_fallback(tmp_path) -> None:
    storage = JSONStorage(tmp_path)

    enemies = list_official_enemies(storage)

    assert enemies == []


def test_empty_enemy_json_uses_safe_fallback(tmp_path) -> None:
    storage = JSONStorage(tmp_path)
    storage.write_json("enemies.json", {})

    enemies = list_official_enemies(storage)

    assert enemies == []


def test_enemy_location_ids_point_to_existing_locations() -> None:
    storage = JSONStorage(Path("data"))

    enemies = list_official_enemies(storage)
    valid_location_ids = {location.id for location in list_official_locations(storage)}

    validate_enemy_locations(enemies, valid_location_ids)


def test_invalid_enemy_location_is_rejected() -> None:
    storage = MemoryStorage(
        {
            "enemies.json": {
                "enemies": [
                    {
                        "id": "inimigo-teste",
                        "name": "Inimigo Teste",
                        "type": "criatura",
                        "description": "Criatura de teste.",
                        "region_ids": ["pais-de-magik"],
                        "location_ids": ["local-inexistente"],
                        "max_health": 10,
                        "armor": 0,
                        "drops": [],
                        "tags": ["oficial", "lore"],
                        "notes": [],
                    }
                ]
            }
        }
    )

    with pytest.raises(ValueError, match="Local invalido"):
        list_official_enemies(storage)


def test_enemy_catalog_does_not_create_active_creatures() -> None:
    storage = MemoryStorage(
        {
            "creatures.json": {"creatures": []},
            "enemies.json": {
                "enemies": [
                    {
                        "id": "inimigo-catalogado",
                        "name": "Inimigo Catalogado",
                        "type": "criatura",
                        "description": "Entrada apenas de catalogo.",
                        "region_ids": ["pais-de-magik"],
                        "location_ids": [],
                        "max_health": 10,
                        "armor": 0,
                        "drops": [],
                        "tags": ["oficial", "lore"],
                        "notes": [],
                    }
                ]
            },
        }
    )

    enemies = list_official_enemies(storage)

    assert enemies[0].name == "Inimigo Catalogado"
    assert list_creatures(storage) == []


def test_existing_creatures_continue_working_after_enemy_catalog() -> None:
    storage = MemoryStorage({"creatures.json": {"creatures": []}})

    creature = create_creature(storage, "Sombra de Teste", "criatura", 12, armor=3)

    assert creature.id == "sombra-de-teste"
    assert list_creatures(storage)[0].name == "Sombra de Teste"


def test_combat_physical_damage_rule_is_unchanged() -> None:
    result = apply_physical_damage(current_health=20, armor=5, damage=8)

    assert result.current_health == 20
    assert result.armor == 0
    assert "excedente foi perdido" in result.description
