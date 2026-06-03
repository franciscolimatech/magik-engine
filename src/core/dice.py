"""Dice rolling utilities."""

from __future__ import annotations

from dataclasses import dataclass
import random
import re
from typing import Protocol


_DICE_PATTERN = re.compile(r"^(?P<count>[1-9]\d*)d(?P<sides>[1-9]\d*)$", re.IGNORECASE)


class RandomLike(Protocol):
    def randint(self, a: int, b: int) -> int:
        """Return a random integer N such that a <= N <= b."""


@dataclass(frozen=True)
class DiceRoll:
    expression: str
    total: int
    rolls: list[int]


def parse_dice_expression(expression: str) -> tuple[int, int]:
    """Parse dice notation like 1d20 or 2d6."""
    match = _DICE_PATTERN.match(expression.strip())
    if not match:
        raise ValueError("Formato de dado invalido. Use algo como 1d20, 1d10 ou 2d6.")

    count = int(match.group("count"))
    sides = int(match.group("sides"))
    if count > 100:
        raise ValueError("Quantidade de dados muito alta. Use ate 100 dados.")
    if sides > 1000:
        raise ValueError("Quantidade de lados muito alta. Use ate 1000 lados.")
    return count, sides


def roll_dice(expression: str, rng: RandomLike | None = None) -> DiceRoll:
    """Roll dice using common RPG notation."""
    count, sides = parse_dice_expression(expression)
    roller = rng or random
    rolls = [roller.randint(1, sides) for _ in range(count)]
    return DiceRoll(expression=expression.strip().lower(), total=sum(rolls), rolls=rolls)
