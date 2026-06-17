from pathlib import Path

import pytest

from src.core.abilities import list_abilities
from src.core.character import create_miko_meu
from src.core.combat import apply_magical_damage
from src.core.magic_marks import (
    filter_magic_marks_by_school,
    get_magic_mark,
    list_magic_marks,
    validate_unique_magic_mark_ids,
)
from src.core.spells import (
    filter_spells_by_domain,
    filter_spells_by_school,
    get_official_spell,
    list_official_spells,
    list_spells_by_domain,
    list_spells_by_school,
    validate_spell_evolutions,
    validate_unique_spell_ids,
)
from src.storage.json_storage import JSONStorage
from src.storage.memory import MemoryStorage


def test_official_spell_catalog_file_loads() -> None:
    storage = JSONStorage(Path("data"))

    spells = list_official_spells(storage)

    assert len(spells) == 60
    assert {"Faísca", "Bola de Fogo", "Marca Sombria", "Olhar do Abismo"}.issubset(
        {spell.name for spell in spells}
    )


def test_magic_mark_catalog_file_loads() -> None:
    storage = JSONStorage(Path("data"))

    marks = list_magic_marks(storage)

    assert len(marks) == 7
    assert {"Marca Vermilion", "Marca das Marés", "Marca da Voz Distante"}.issubset(
        {mark.name for mark in marks}
    )


def test_official_spell_ids_are_unique() -> None:
    spells = list_official_spells(JSONStorage(Path("data")))

    validate_unique_spell_ids(spells)

    ids = [spell.id for spell in spells]
    assert len(ids) == len(set(ids))


def test_magic_mark_ids_are_unique() -> None:
    marks = list_magic_marks(JSONStorage(Path("data")))

    validate_unique_magic_mark_ids(marks)

    ids = [mark.id for mark in marks]
    assert len(ids) == len(set(ids))


def test_get_official_spell_by_id() -> None:
    storage = JSONStorage(Path("data"))

    spell = get_official_spell(storage, "faisca")

    assert spell.name == "Faísca"
    assert spell.school == "Sangue e Brasas"
    assert spell.domain == 1
    assert spell.evolves_to == "bola-de-fogo"
    assert len(spell.evolution_requirements) == 3


def test_get_magic_mark_by_id() -> None:
    storage = JSONStorage(Path("data"))

    mark = get_magic_mark(storage, "marca-vermilion")

    assert mark.name == "Marca Vermilion"
    assert mark.school == "Sangue e Brasas"
    assert mark.location_on_body == "Palma da mão"
    assert mark.grants_basic_spells is True


def test_filter_spells_by_school() -> None:
    storage = JSONStorage(Path("data"))
    spells = list_official_spells(storage)

    shadow_spells = filter_spells_by_school(spells, "sombras")
    stored_shadow_spells = list_spells_by_school(storage, "Sombras")

    assert shadow_spells == stored_shadow_spells
    assert len(shadow_spells) == 11
    assert all(spell.school == "Sombras" for spell in shadow_spells)


def test_filter_spells_by_domain() -> None:
    storage = JSONStorage(Path("data"))
    spells = list_official_spells(storage)

    domain_three = filter_spells_by_domain(spells, 3)
    stored_domain_three = list_spells_by_domain(storage, 3)

    assert domain_three == stored_domain_three
    assert len(domain_three) == 17
    assert all(spell.domain == 3 for spell in domain_three)


def test_filter_magic_marks_by_school() -> None:
    marks = list_magic_marks(JSONStorage(Path("data")))

    water_marks = filter_magic_marks_by_school(marks, "água")

    assert [mark.name for mark in water_marks] == ["Marca das Marés"]


def test_spell_evolutions_point_to_existing_spells() -> None:
    spells = list_official_spells(JSONStorage(Path("data")))

    validate_spell_evolutions(spells)

    valid_ids = {spell.id for spell in spells}
    assert all(spell.evolves_to in valid_ids for spell in spells if spell.evolves_to)


def test_missing_or_empty_spell_json_uses_safe_fallback(tmp_path) -> None:
    storage = JSONStorage(tmp_path)

    assert list_official_spells(storage) == []

    storage.write_json("spells.json", {})
    assert list_official_spells(storage) == []


def test_missing_or_empty_magic_mark_json_uses_safe_fallback(tmp_path) -> None:
    storage = JSONStorage(tmp_path)

    assert list_magic_marks(storage) == []

    storage.write_json("magic_marks.json", {})
    assert list_magic_marks(storage) == []


def test_invalid_spell_evolution_is_rejected() -> None:
    storage = MemoryStorage(
        {
            "spells.json": {
                "spells": [
                    {
                        "id": "magia-teste",
                        "name": "Magia Teste",
                        "school": "Teste",
                        "domain": 1,
                        "region": "Lugar de Teste",
                        "description": "Magia de teste.",
                        "effect": "Efeito descritivo.",
                        "evolves_to": "magia-inexistente",
                        "evolution_requirements": [],
                        "tags": ["oficial", "lore"],
                        "notes": [],
                    }
                ]
            }
        }
    )

    with pytest.raises(ValueError, match="Evolucao invalida"):
        list_official_spells(storage)


def test_existing_abilities_continue_working_with_spell_catalog() -> None:
    miko = create_miko_meu()

    abilities = list_abilities(miko)

    assert any(ability.id == "shadow_staff" for ability in abilities)
    assert any(ability.id == "ikisaki_roulette" for ability in abilities)


def test_magical_damage_rule_is_unchanged_by_spell_catalog() -> None:
    result = apply_magical_damage(current_health=12, armor=8, damage=5)

    assert result.current_health == 7
    assert result.armor == 8
    assert "Magia ignorou armadura" in result.description
