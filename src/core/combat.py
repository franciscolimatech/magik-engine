"""Official MAGIK combat mechanics."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import random
from typing import Any, Protocol


DAMAGE_DICE = (5, 10, 20, 30)


class RandomLike(Protocol):
    def randint(self, a: int, b: int) -> int:
        """Return a random integer N such that a <= N <= b."""


@dataclass(frozen=True)
class DamageRoll:
    target_current_health: int
    half_health: float
    die_sides: int
    result: int
    explanation: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DamageApplication:
    current_health: int
    armor: int
    description: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def choose_damage_die(current_health: int) -> int:
    if current_health <= 0:
        raise ValueError("A vida atual deve ser maior que zero para escolher o dado de dano.")

    half_health = current_health / 2
    return min(DAMAGE_DICE, key=lambda die: (abs(die - half_health), die))


def roll_damage(current_health: int, rng: RandomLike | None = None) -> DamageRoll:
    die_sides = choose_damage_die(current_health)
    roller = rng or random
    result = roller.randint(1, die_sides)
    half_health = current_health / 2
    explanation = (
        f"Metade da vida atual: {half_health:g}. "
        f"O dado oficial mais proximo e d{die_sides}; em empate, usa-se o menor dado."
    )
    return DamageRoll(
        target_current_health=current_health,
        half_health=half_health,
        die_sides=die_sides,
        result=result,
        explanation=explanation,
    )


def apply_physical_damage(current_health: int, armor: int, damage: int) -> DamageApplication:
    _validate_damage_state(current_health, armor, damage)

    if armor > 0:
        new_armor = max(armor - damage, 0)
        if new_armor == 0:
            description = (
                f"Dano fisico atingiu a armadura. Armadura foi de {armor} para 0; "
                "qualquer excedente foi perdido e a vida nao mudou."
            )
        else:
            description = f"Dano fisico atingiu a armadura. Armadura foi de {armor} para {new_armor}; vida nao mudou."
        return DamageApplication(current_health=current_health, armor=new_armor, description=description)

    new_health = max(current_health - damage, 0)
    return DamageApplication(
        current_health=new_health,
        armor=0,
        description=f"Sem armadura restante, o dano fisico atingiu a vida: {current_health} para {new_health}.",
    )


def apply_magical_damage(current_health: int, armor: int, damage: int) -> DamageApplication:
    _validate_damage_state(current_health, armor, damage)
    new_health = max(current_health - damage, 0)
    return DamageApplication(
        current_health=new_health,
        armor=armor,
        description=f"Magia ignorou armadura e atingiu diretamente a vida: {current_health} para {new_health}.",
    )


def _validate_damage_state(current_health: int, armor: int, damage: int) -> None:
    if current_health < 0:
        raise ValueError("A vida atual nao pode ser negativa.")
    if armor < 0:
        raise ValueError("A armadura nao pode ser negativa.")
    if damage < 0:
        raise ValueError("O dano nao pode ser negativo.")
