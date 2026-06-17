from pathlib import Path

import pytest

from src.core.character import add_equipment, load_or_create_miko, remove_equipment
from src.core.combat import apply_physical_damage
from src.core.items import (
    filter_items_by_origin,
    filter_items_by_rarity,
    get_official_item,
    list_items_by_origin,
    list_items_by_rarity,
    list_official_items,
    validate_item_locations,
    validate_unique_item_ids,
)
from src.core.world import list_official_locations
from src.storage.json_storage import JSONStorage
from src.storage.memory import MemoryStorage


def test_official_item_catalog_file_loads() -> None:
    storage = JSONStorage(Path("data"))

    items = list_official_items(storage)

    assert len(items) == 219
    assert {
        "Pena da Galinha-Nanica Primordial",
        "Flecha Torta",
        "Machado da Gargalhada Final",
    }.issubset({item.name for item in items})


def test_official_item_ids_are_unique() -> None:
    storage = JSONStorage(Path("data"))
    items = list_official_items(storage)

    validate_unique_item_ids(items)

    ids = [item.id for item in items]
    assert len(ids) == len(set(ids))


def test_get_official_item_by_id() -> None:
    storage = JSONStorage(Path("data"))

    item = get_official_item(storage, "pena-da-galinha-nanica-primordial")

    assert item.name == "Pena da Galinha-Nanica Primordial"
    assert item.type == "especial"
    assert item.origin == "Desconhecida"
    assert item.rarity == "Relíquia"
    assert "repetir qualquer rolagem" in item.effect


def test_official_items_have_minimum_fields() -> None:
    storage = JSONStorage(Path("data"))

    items = list_official_items(storage)

    assert all(item.id for item in items)
    assert all(item.name for item in items)
    assert all(item.type for item in items)
    assert all(item.description for item in items)
    assert all(item.origin for item in items)
    assert all(item.rarity for item in items)
    assert all(item.effect for item in items)
    assert all("oficial" in item.tags for item in items)
    assert all("lore" in item.tags for item in items)


def test_missing_item_json_uses_safe_fallback(tmp_path) -> None:
    storage = JSONStorage(tmp_path)

    items = list_official_items(storage)

    assert items == []


def test_empty_item_json_uses_safe_fallback(tmp_path) -> None:
    storage = JSONStorage(tmp_path)
    storage.write_json("items.json", {})

    items = list_official_items(storage)

    assert items == []


def test_filter_items_by_rarity() -> None:
    storage = JSONStorage(Path("data"))
    items = list_official_items(storage)

    relics = filter_items_by_rarity(items, "relíquia")
    stored_relics = list_items_by_rarity(storage, "Relíquia")

    assert relics
    assert relics == stored_relics
    assert all(item.rarity == "Relíquia" for item in relics)


def test_filter_items_by_origin() -> None:
    storage = JSONStorage(Path("data"))
    items = list_official_items(storage)

    estrada_items = filter_items_by_origin(items, "Estrada do Viajante")
    stored_estrada_items = list_items_by_origin(storage, "estrada")

    assert any(item.name == "Besta da Primeira Flecha" for item in estrada_items)
    assert estrada_items == stored_estrada_items
    assert all("Estrada do Viajante" in item.origin for item in estrada_items)


def test_item_location_ids_point_to_existing_locations() -> None:
    storage = JSONStorage(Path("data"))

    items = list_official_items(storage)
    valid_location_ids = {location.id for location in list_official_locations(storage)}

    validate_item_locations(items, valid_location_ids)


def test_invalid_item_location_is_rejected() -> None:
    storage = MemoryStorage(
        {
            "items.json": {
                "items": [
                    {
                        "id": "item-teste",
                        "name": "Item Teste",
                        "type": "especial",
                        "description": "Item de teste.",
                        "origin": "Lugar de Teste",
                        "rarity": "Comum",
                        "effect": "Sem efeito ativo.",
                        "region_ids": [],
                        "location_ids": ["local-inexistente"],
                        "tags": ["oficial", "lore"],
                        "notes": [],
                    }
                ]
            }
        }
    )

    with pytest.raises(ValueError, match="Local invalido"):
        list_official_items(storage)


def test_item_catalog_does_not_change_character_equipment() -> None:
    storage = MemoryStorage()
    miko = load_or_create_miko(storage)

    items = list_official_items(storage)

    assert items == []
    assert load_or_create_miko(storage).equipment == miko.equipment


def test_existing_character_equipment_still_works() -> None:
    storage = MemoryStorage()

    with_item = add_equipment(storage, "miko-meu", "Amuleto")
    without_item = remove_equipment(storage, "miko-meu", "Amuleto")

    assert "Amuleto" in with_item.equipment
    assert "Amuleto" not in without_item.equipment


def test_combat_physical_damage_rule_is_unchanged_after_item_catalog() -> None:
    result = apply_physical_damage(current_health=20, armor=5, damage=8)

    assert result.current_health == 20
    assert result.armor == 0
    assert "excedente foi perdido" in result.description
