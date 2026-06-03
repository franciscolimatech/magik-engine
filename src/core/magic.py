"""Base mechanical support for official MAGIK magic."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from src.core.combat import DamageApplication, apply_magical_damage


@dataclass(frozen=True)
class HealingResult:
    current_health: int
    max_health: int
    amount_healed: int
    description: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class NarrativeMagicEffect:
    effect_text: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def apply_magic_damage(current_health: int, armor: int, damage: int) -> DamageApplication:
    return apply_magical_damage(current_health=current_health, armor=armor, damage=damage)


def apply_healing(current_health: int, max_health: int, amount: int) -> HealingResult:
    if current_health < 0:
        raise ValueError("A vida atual nao pode ser negativa.")
    if max_health <= 0:
        raise ValueError("A vida maxima deve ser maior que zero.")
    if current_health > max_health:
        raise ValueError("A vida atual nao pode ser maior que a vida maxima.")
    if amount < 0:
        raise ValueError("A cura nao pode ser negativa.")

    new_health = min(current_health + amount, max_health)
    return HealingResult(
        current_health=new_health,
        max_health=max_health,
        amount_healed=new_health - current_health,
        description=f"Cura aplicada: vida foi de {current_health} para {new_health}, sem ultrapassar {max_health}.",
    )


def record_narrative_effect(effect_text: str) -> NarrativeMagicEffect:
    cleaned = effect_text.strip()
    if not cleaned:
        raise ValueError("O efeito narrativo nao pode ser vazio.")
    return NarrativeMagicEffect(effect_text=cleaned)
