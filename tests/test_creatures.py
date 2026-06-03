import pytest

from src.core.creatures import (
    add_creature_note,
    add_creature_status,
    apply_magical_damage_to_creature,
    apply_physical_damage_to_creature,
    create_creature,
    get_creature,
    heal_creature,
    list_creatures,
    remove_creature_status,
)
from src.storage.memory import MemoryStorage


def test_create_creature() -> None:
    storage = MemoryStorage({"creatures.json": {"creatures": []}})

    creature = create_creature(storage, "Kriot de Teste", "criatura", 20, armor=3)

    assert creature.id == "kriot-de-teste"
    assert creature.current_health == 20
    assert creature.armor == 3


def test_list_creatures() -> None:
    storage = MemoryStorage({"creatures.json": {"creatures": []}})
    create_creature(storage, "Kriot", "criatura", 20)

    assert [creature.name for creature in list_creatures(storage)] == ["Kriot"]


def test_get_existing_creature() -> None:
    storage = MemoryStorage({"creatures.json": {"creatures": []}})
    create_creature(storage, "Kriot", "criatura", 20)

    assert get_creature(storage, "kriot").name == "Kriot"


def test_get_missing_creature_raises_error() -> None:
    storage = MemoryStorage({"creatures.json": {"creatures": []}})

    with pytest.raises(ValueError):
        get_creature(storage, "fantasma")


def test_create_creature_rejects_duplicate_explicit_id() -> None:
    storage = MemoryStorage({"creatures.json": {"creatures": []}})
    create_creature(storage, "Kriot", "criatura", 20, creature_id="kriot")

    with pytest.raises(ValueError):
        create_creature(storage, "Outro Kriot", "criatura", 20, creature_id="kriot")


def test_apply_physical_damage_to_creature_hits_armor_first() -> None:
    storage = MemoryStorage({"creatures.json": {"creatures": []}})
    create_creature(storage, "Kriot", "criatura", 20, armor=5)

    creature, description = apply_physical_damage_to_creature(storage, "kriot", 8)

    assert creature.armor == 0
    assert creature.current_health == 20
    assert "excedente foi perdido" in description


def test_apply_magical_damage_to_creature_ignores_armor() -> None:
    storage = MemoryStorage({"creatures.json": {"creatures": []}})
    create_creature(storage, "Kriot", "criatura", 20, armor=5)

    creature, _description = apply_magical_damage_to_creature(storage, "kriot", 8)

    assert creature.armor == 5
    assert creature.current_health == 12


def test_heal_creature_does_not_exceed_max_health() -> None:
    storage = MemoryStorage({"creatures.json": {"creatures": []}})
    create_creature(storage, "Kriot", "criatura", 20)
    apply_magical_damage_to_creature(storage, "kriot", 8)

    creature, _description = heal_creature(storage, "kriot", 20)

    assert creature.current_health == 20


def test_add_and_remove_creature_status() -> None:
    storage = MemoryStorage({"creatures.json": {"creatures": []}})
    create_creature(storage, "Kriot", "criatura", 20)

    with_status = add_creature_status(storage, "kriot", "atordoado")
    without_status = remove_creature_status(storage, "kriot", "atordoado")

    assert "atordoado" in with_status.status
    assert "atordoado" not in without_status.status


def test_add_creature_note() -> None:
    storage = MemoryStorage({"creatures.json": {"creatures": []}})
    create_creature(storage, "Kriot", "criatura", 20)

    creature = add_creature_note(storage, "kriot", "Nao e oficial; exemplo de teste.")

    assert creature.notes == ["Nao e oficial; exemplo de teste."]
