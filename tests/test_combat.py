from src.core.combat import apply_magical_damage, apply_physical_damage, choose_damage_die, roll_damage


class FixedRng:
    def randint(self, _start: int, _end: int) -> int:
        return 7


def test_choose_damage_die_uses_closest_half_health() -> None:
    assert choose_damage_die(60) == 30
    assert choose_damage_die(40) == 20
    assert choose_damage_die(25) == 10


def test_choose_damage_die_tie_uses_smaller_die() -> None:
    assert choose_damage_die(50) == 20


def test_roll_damage_returns_die_result_and_explanation() -> None:
    result = roll_damage(40, rng=FixedRng())

    assert result.die_sides == 20
    assert result.result == 7
    assert "Metade da vida atual" in result.explanation


def test_physical_damage_reduces_armor_before_health() -> None:
    result = apply_physical_damage(current_health=10, armor=5, damage=3)

    assert result.armor == 2
    assert result.current_health == 10


def test_physical_damage_discards_excess_armor_damage() -> None:
    result = apply_physical_damage(current_health=10, armor=5, damage=10)

    assert result.armor == 0
    assert result.current_health == 10
    assert "excedente foi perdido" in result.description


def test_physical_damage_hits_health_only_when_armor_is_zero() -> None:
    result = apply_physical_damage(current_health=10, armor=0, damage=4)

    assert result.armor == 0
    assert result.current_health == 6


def test_magical_damage_ignores_armor() -> None:
    result = apply_magical_damage(current_health=10, armor=5, damage=4)

    assert result.armor == 5
    assert result.current_health == 6
