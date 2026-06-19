import pytest

from src.game.dice import (
    resolve_basic_attack,
    resolve_d20_check,
    roll_die,
    roll_expression,
)


class FakeRng:
    def __init__(self, values: list[int]) -> None:
        self.values = list(values)

    def randint(self, a: int, b: int) -> int:
        value = self.values.pop(0)
        return max(a, min(value, b))


def test_roll_d20_returns_value_between_1_and_20() -> None:
    assert roll_die(20, FakeRng([14])) == 14


def test_roll_d6_returns_value_between_1_and_6() -> None:
    assert roll_die(6, FakeRng([4])) == 4


def test_roll_expression_1d6_works() -> None:
    roll = roll_expression("1d6", FakeRng([5]))

    assert roll.expression == "1d6"
    assert roll.rolls == (5,)
    assert roll.total == 5


def test_roll_expression_2d6_works() -> None:
    roll = roll_expression("2d6", FakeRng([2, 6]))

    assert roll.expression == "2d6"
    assert roll.rolls == (2, 6)
    assert roll.total == 8


def test_roll_expression_rejects_invalid_format() -> None:
    with pytest.raises(ValueError):
        roll_expression("d20", FakeRng([1]))


def test_d20_check_succeeds_when_total_reaches_difficulty() -> None:
    check = resolve_d20_check(modifier=2, difficulty=13, rng=FakeRng([11]))

    assert check.total == 13
    assert check.outcome == "success"
    assert check.is_success is True


def test_d20_check_fails_below_difficulty() -> None:
    check = resolve_d20_check(modifier=2, difficulty=13, rng=FakeRng([10]))

    assert check.total == 12
    assert check.outcome == "failure"
    assert check.is_success is False


def test_d20_natural_20_is_critical() -> None:
    check = resolve_d20_check(modifier=0, difficulty=30, rng=FakeRng([20]))

    assert check.outcome == "critical_success"
    assert check.is_critical is True


def test_d20_natural_1_is_critical_failure() -> None:
    check = resolve_d20_check(modifier=20, difficulty=10, rng=FakeRng([1]))

    assert check.outcome == "critical_failure"
    assert check.is_critical_failure is True
    assert check.is_success is False


def test_basic_attack_rolls_1d6_on_normal_success() -> None:
    result = resolve_basic_attack(modifier=2, difficulty=13, rng=FakeRng([12, 4]))

    assert result.check.outcome == "success"
    assert result.damage_roll is not None
    assert result.damage_roll.expression == "1d6"
    assert result.damage == 4


def test_basic_attack_rolls_2d6_on_critical() -> None:
    result = resolve_basic_attack(modifier=2, difficulty=13, rng=FakeRng([20, 3, 5]))

    assert result.check.outcome == "critical_success"
    assert result.damage_roll is not None
    assert result.damage_roll.expression == "2d6"
    assert result.damage == 8


def test_basic_attack_deals_no_damage_on_failure() -> None:
    result = resolve_basic_attack(modifier=2, difficulty=13, rng=FakeRng([4]))

    assert result.check.outcome == "failure"
    assert result.damage_roll is None
    assert result.damage == 0
