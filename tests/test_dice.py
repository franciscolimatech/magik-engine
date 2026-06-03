import pytest

from src.core.dice import parse_dice_expression, roll_dice


class FixedRng:
    def __init__(self, values: list[int]) -> None:
        self.values = values
        self.index = 0

    def randint(self, _start: int, _end: int) -> int:
        value = self.values[self.index]
        self.index += 1
        return value


def test_roll_dice_returns_total_and_individual_rolls() -> None:
    result = roll_dice("2d6", rng=FixedRng([2, 5]))

    assert result.total == 7
    assert result.rolls == [2, 5]
    assert result.expression == "2d6"


@pytest.mark.parametrize("expression", ["", "d20", "1d", "0d6", "2d0", "abc", "1d-6"])
def test_parse_dice_expression_rejects_invalid_formats(expression: str) -> None:
    with pytest.raises(ValueError):
        parse_dice_expression(expression)


def test_parse_dice_expression_accepts_valid_formats() -> None:
    assert parse_dice_expression("1d20") == (1, 20)
    assert parse_dice_expression("2D6") == (2, 6)
