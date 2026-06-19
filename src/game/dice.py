"""Small dice helpers for the PyGame battle prototype.

This layer is intentionally narrow: it resolves dice checks and damage rolls,
but it does not apply combat damage or change game state.
"""

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
    rolls: tuple[int, ...]
    total: int


@dataclass(frozen=True)
class D20Check:
    natural: int
    modifier: int
    total: int
    difficulty: int
    outcome: str

    @property
    def is_success(self) -> bool:
        return self.outcome in {"success", "critical_success"}

    @property
    def is_critical(self) -> bool:
        return self.outcome == "critical_success"

    @property
    def is_critical_failure(self) -> bool:
        return self.outcome == "critical_failure"


@dataclass(frozen=True)
class AttackResolution:
    check: D20Check
    damage_roll: DiceRoll | None

    @property
    def damage(self) -> int:
        return 0 if self.damage_roll is None else self.damage_roll.total


def roll_die(sides: int, rng: RandomLike | None = None) -> int:
    if sides <= 0:
        raise ValueError("O dado precisa ter pelo menos 1 lado.")
    roller = rng or random
    return roller.randint(1, sides)


def roll_expression(expression: str, rng: RandomLike | None = None) -> DiceRoll:
    count, sides = parse_expression(expression)
    rolls = tuple(roll_die(sides, rng) for _ in range(count))
    return DiceRoll(expression=expression.strip().lower(), rolls=rolls, total=sum(rolls))


def parse_expression(expression: str) -> tuple[int, int]:
    match = _DICE_PATTERN.match(expression.strip())
    if not match:
        raise ValueError("Formato de dado invalido. Use algo como 1d20, 1d6 ou 2d6.")
    count = int(match.group("count"))
    sides = int(match.group("sides"))
    if count > 20:
        raise ValueError("Quantidade de dados muito alta para o combate visual.")
    if sides > 100:
        raise ValueError("Quantidade de lados muito alta para o combate visual.")
    return count, sides


def resolve_d20_check(
    modifier: int = 0,
    difficulty: int = 10,
    rng: RandomLike | None = None,
) -> D20Check:
    natural = roll_die(20, rng)
    total = natural + modifier
    if natural == 1:
        outcome = "critical_failure"
    elif natural == 20:
        outcome = "critical_success"
    elif total >= difficulty:
        outcome = "success"
    else:
        outcome = "failure"
    return D20Check(
        natural=natural,
        modifier=modifier,
        total=total,
        difficulty=difficulty,
        outcome=outcome,
    )


def resolve_basic_attack(
    modifier: int = 2,
    difficulty: int = 13,
    rng: RandomLike | None = None,
) -> AttackResolution:
    check = resolve_d20_check(modifier=modifier, difficulty=difficulty, rng=rng)
    if not check.is_success:
        return AttackResolution(check=check, damage_roll=None)
    damage_expression = "2d6" if check.is_critical else "1d6"
    return AttackResolution(check=check, damage_roll=roll_expression(damage_expression, rng))
