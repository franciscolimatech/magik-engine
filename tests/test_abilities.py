import pytest

from src.core.abilities import (
    Ability,
    add_ability,
    get_ability,
    list_abilities,
    remove_ability,
    restore_ability_uses,
    use_ability,
)
from src.core.character import create_miko_meu


def test_add_and_list_ability() -> None:
    character = create_miko_meu()
    ability = Ability(id="shield", name="Escudo Rapido", type="defesa", effect="Reduz impacto.")

    add_ability(character, ability)

    assert "shield" in {current.id for current in list_abilities(character)}


def test_get_existing_ability() -> None:
    character = create_miko_meu()

    ability = get_ability(character, "ikisaki_roulette")

    assert ability.name == "Roleta Sombria: Dez Elos de Ikisaki"


def test_get_missing_ability_raises_error() -> None:
    character = create_miko_meu()

    with pytest.raises(ValueError):
        get_ability(character, "nao-existe")


def test_remove_ability() -> None:
    character = create_miko_meu()

    remove_ability(character, "shadow_switch")

    assert "shadow_switch" not in {ability.id for ability in list_abilities(character)}


def test_add_ability_rejects_duplicate() -> None:
    character = create_miko_meu()

    with pytest.raises(ValueError):
        add_ability(character, Ability(id="shadow_staff", name="Outro Cajado", type="magia"))


def test_use_limited_ability_reduces_remaining_uses() -> None:
    character = create_miko_meu()

    result = use_ability(character, "shadow_switch")

    assert result.remaining_uses == 0
    assert get_ability(character, "shadow_switch").remaining_uses == 0


def test_use_ability_blocks_when_no_remaining_uses() -> None:
    character = create_miko_meu()
    use_ability(character, "shadow_switch")

    with pytest.raises(ValueError):
        use_ability(character, "shadow_switch")


def test_restore_ability_uses() -> None:
    character = create_miko_meu()
    use_ability(character, "shadow_switch")

    restore_ability_uses(character, "todos")

    assert get_ability(character, "shadow_switch").remaining_uses == 1
