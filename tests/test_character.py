import pytest

from src.core.character import (
    add_equipment,
    create_character,
    create_miko_meu,
    get_character,
    list_characters,
    load_or_create_miko,
    remove_character,
    remove_equipment,
    save_character,
    save_characters,
    update_character_armor,
    update_character_health,
)
from src.core.combat import apply_physical_damage
from src.storage.json_storage import JSONStorage
from src.storage.memory import MemoryStorage
from src.systems.ikisaki import use_shadow_roulette


def test_create_miko_meu_has_initial_sheet() -> None:
    miko = create_miko_meu()

    assert miko.name == "Miko Meu"
    assert miko.id == "miko-meu"
    assert miko.character_class == "Sombrio"
    assert miko.max_health == 25
    assert miko.current_health == 25
    assert miko.armor == 5
    assert miko.equipment == ["Cajado", "Corrente de Ferro"]
    assert miko.living_weapon == "Ikisaki"
    assert miko.can_disappear_in_shadows is True
    assert miko.chain_debts == 0
    assert miko.last_ikisaki_result is None
    assert miko.ikisaki_available is True
    assert "ikisaki" in miko.special_systems
    assert "shadow_staff" in miko.special_systems
    assert {ability["id"] for ability in miko.abilities} >= {
        "ikisaki_roulette",
        "shadow_staff",
        "disappear_in_shadows",
        "shadow_switch",
    }


def test_save_and_load_miko_from_json_storage(tmp_path) -> None:
    storage = JSONStorage(tmp_path)
    original = create_miko_meu()
    original.chain_debts = 2
    save_characters(storage, [original])

    loaded = load_or_create_miko(storage)

    assert loaded.name == "Miko Meu"
    assert loaded.chain_debts == 2


def test_list_characters_includes_miko_by_default() -> None:
    storage = MemoryStorage({"characters.json": {"characters": []}})

    characters = list_characters(storage)

    assert [character.id for character in characters] == ["miko-meu"]


def test_get_character_by_existing_id() -> None:
    storage = MemoryStorage({"characters.json": {"characters": [create_miko_meu().to_dict()]}})

    character = get_character(storage, "miko-meu")

    assert character.name == "Miko Meu"


def test_get_character_by_missing_id_raises_error() -> None:
    storage = MemoryStorage({"characters.json": {"characters": [create_miko_meu().to_dict()]}})

    with pytest.raises(ValueError):
        get_character(storage, "nao-existe")


def test_create_character_generates_unique_id() -> None:
    storage = MemoryStorage({"characters.json": {"characters": [create_miko_meu().to_dict()]}})

    first = create_character(storage, name="Lia", character_class="Guardia", max_health=30)
    second = create_character(storage, name="Lia", character_class="Guardia", max_health=30)

    assert first.id == "lia"
    assert second.id == "lia-2"


def test_old_character_without_origin_still_loads() -> None:
    miko_data = create_miko_meu().to_dict()
    for field_name in ("origin_location_id", "origin_region_id", "background_summary", "personal_goal"):
        miko_data.pop(field_name, None)
    storage = MemoryStorage({"characters.json": {"characters": [miko_data]}})

    character = get_character(storage, "miko-meu")

    assert character.origin_location_id is None
    assert character.origin_region_id is None
    assert character.background_summary == ""
    assert character.personal_goal == ""


def test_create_character_can_store_official_origin() -> None:
    storage = MemoryStorage({"characters.json": {"characters": [create_miko_meu().to_dict()]}})

    character = create_character(
        storage,
        name="Lia",
        character_class="Guia",
        max_health=20,
        origin_location_id="floresta-do-avesso",
        background_summary="Nasceu ouvindo arvores que nao deveriam falar.",
        personal_goal="Descobrir por que a floresta chamou seu nome.",
    )

    assert character.origin_location_id == "floresta-do-avesso"
    assert character.origin_region_id == "pais-de-magik"
    assert character.background_summary == "Nasceu ouvindo arvores que nao deveriam falar."
    assert character.personal_goal == "Descobrir por que a floresta chamou seu nome."


def test_create_character_rejects_invalid_origin_location() -> None:
    storage = MemoryStorage({"characters.json": {"characters": [create_miko_meu().to_dict()]}})

    with pytest.raises(ValueError, match="Local oficial nao encontrado"):
        create_character(
            storage,
            name="Lia",
            character_class="Guia",
            max_health=20,
            origin_location_id="lugar-inexistente",
        )


def test_character_origin_does_not_change_combat_rule() -> None:
    storage = MemoryStorage({"characters.json": {"characters": [create_miko_meu().to_dict()]}})
    character = create_character(
        storage,
        name="Lia",
        character_class="Guia",
        max_health=20,
        armor=5,
        origin_location_id="cidade-de-pedralume",
    )

    result = apply_physical_damage(character.current_health, character.armor, 8)

    assert result.current_health == 20
    assert result.armor == 0


def test_create_character_rejects_duplicate_explicit_id() -> None:
    storage = MemoryStorage({"characters.json": {"characters": [create_miko_meu().to_dict()]}})

    with pytest.raises(ValueError):
        create_character(
            storage,
            name="Outro Miko",
            character_class="Sombrio",
            max_health=20,
            character_id="miko-meu",
        )


def test_update_character_health() -> None:
    storage = MemoryStorage({"characters.json": {"characters": [create_miko_meu().to_dict()]}})

    updated = update_character_health(storage, "miko-meu", 12)

    assert updated.current_health == 12
    assert get_character(storage, "miko-meu").current_health == 12


def test_update_character_armor() -> None:
    storage = MemoryStorage({"characters.json": {"characters": [create_miko_meu().to_dict()]}})

    updated = update_character_armor(storage, "miko-meu", 3)

    assert updated.armor == 3
    assert get_character(storage, "miko-meu").armor == 3


def test_add_and_remove_equipment() -> None:
    storage = MemoryStorage({"characters.json": {"characters": [create_miko_meu().to_dict()]}})

    with_item = add_equipment(storage, "miko-meu", "Lanterna")
    without_item = remove_equipment(storage, "miko-meu", "Lanterna")

    assert "Lanterna" in with_item.equipment
    assert "Lanterna" not in without_item.equipment


def test_save_character_does_not_overwrite_other_characters() -> None:
    storage = MemoryStorage({"characters.json": {"characters": [create_miko_meu().to_dict()]}})
    ally = create_character(storage, name="Lia", character_class="Guardia", max_health=30)
    ally.current_health = 10

    save_character(storage, ally)
    characters = list_characters(storage)

    assert {character.id for character in characters} == {"miko-meu", "lia"}
    assert get_character(storage, "lia").current_health == 10


def test_remove_character_requires_confirmation() -> None:
    storage = MemoryStorage({"characters.json": {"characters": [create_miko_meu().to_dict()]}})
    create_character(storage, name="Lia", character_class="Guardia", max_health=30)

    with pytest.raises(ValueError):
        remove_character(storage, "lia")

    removed = remove_character(storage, "lia", confirm=True)

    assert removed.id == "lia"
    assert {character.id for character in list_characters(storage)} == {"miko-meu"}


def test_ikisaki_still_works_for_miko() -> None:
    miko = create_miko_meu()

    result = use_shadow_roulette(miko, forced_roll=7)

    assert result.link_name == "Corrente Come-Medo"
    assert miko.chain_debts == 1
