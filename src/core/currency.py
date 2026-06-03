"""Official Pedralume currency helpers."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


UNIT_VALUES_IN_RAW = {
    "bruta": 1,
    "refinada": 10,
    "pura": 100,
    "primordial": 1000,
}

DISPLAY_NAMES = {
    "bruta": "Pedralume Bruta",
    "refinada": "Pedralume Refinada",
    "pura": "Pedralume Pura",
    "primordial": "Pedralume Primordial",
}


@dataclass(frozen=True)
class PedralumeMoney:
    raw_amount: int = 0

    @classmethod
    def from_units(
        cls,
        bruta: int = 0,
        refinada: int = 0,
        pura: int = 0,
        primordial: int = 0,
    ) -> "PedralumeMoney":
        values = {
            "bruta": bruta,
            "refinada": refinada,
            "pura": pura,
            "primordial": primordial,
        }
        if any(value < 0 for value in values.values()):
            raise ValueError("Valores de Pedralume nao podem ser negativos.")
        return cls(sum(value * UNIT_VALUES_IN_RAW[unit] for unit, value in values.items()))

    def add(self, other: "PedralumeMoney") -> "PedralumeMoney":
        return PedralumeMoney(self.raw_amount + other.raw_amount)

    def subtract(self, other: "PedralumeMoney") -> "PedralumeMoney":
        result = self.raw_amount - other.raw_amount
        if result < 0:
            raise ValueError("Saldo de Pedralume insuficiente.")
        return PedralumeMoney(result)

    def to_units(self) -> dict[str, int]:
        remaining = self.raw_amount
        primordial, remaining = divmod(remaining, UNIT_VALUES_IN_RAW["primordial"])
        pura, remaining = divmod(remaining, UNIT_VALUES_IN_RAW["pura"])
        refinada, bruta = divmod(remaining, UNIT_VALUES_IN_RAW["refinada"])
        return {
            "primordial": primordial,
            "pura": pura,
            "refinada": refinada,
            "bruta": bruta,
        }

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["organized"] = self.to_units()
        return data

    def display(self) -> str:
        units = self.to_units()
        parts = [
            f"{amount} {DISPLAY_NAMES[unit]}"
            for unit, amount in units.items()
            if amount > 0
        ]
        return ", ".join(parts) if parts else "0 Pedralume Bruta"


def convert_pedralume(amount: int, from_unit: str, to_unit: str) -> float:
    if amount < 0:
        raise ValueError("O valor a converter nao pode ser negativo.")

    source = _normalize_unit(from_unit)
    target = _normalize_unit(to_unit)
    raw_amount = amount * UNIT_VALUES_IN_RAW[source]
    return raw_amount / UNIT_VALUES_IN_RAW[target]


def _normalize_unit(unit: str) -> str:
    normalized = unit.strip().casefold().replace("pedralume", "").strip()
    if normalized.endswith("s"):
        normalized = normalized[:-1]
    try:
        UNIT_VALUES_IN_RAW[normalized]
    except KeyError as exc:
        valid = ", ".join(UNIT_VALUES_IN_RAW)
        raise ValueError(f"Unidade de Pedralume invalida. Use uma destas: {valid}.") from exc
    return normalized
