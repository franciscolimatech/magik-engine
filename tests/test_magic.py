from src.core.magic import apply_healing, apply_magic_damage, record_narrative_effect


def test_magic_damage_ignores_armor() -> None:
    result = apply_magic_damage(current_health=12, armor=8, damage=5)

    assert result.armor == 8
    assert result.current_health == 7


def test_healing_does_not_exceed_max_health() -> None:
    result = apply_healing(current_health=20, max_health=25, amount=10)

    assert result.current_health == 25
    assert result.amount_healed == 5


def test_narrative_magic_effect_is_recorded_as_text() -> None:
    result = record_narrative_effect("Criar uma ilusao simples.")

    assert result.effect_text == "Criar uma ilusao simples."
