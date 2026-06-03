import pytest

from src.core.currency import PedralumeMoney, convert_pedralume


def test_convert_pedralume_between_levels() -> None:
    assert convert_pedralume(10, "bruta", "refinada") == 1
    assert convert_pedralume(1, "primordial", "bruta") == 1000
    assert convert_pedralume(10, "pura", "primordial") == 1


def test_sum_pedralume_money() -> None:
    money = PedralumeMoney.from_units(bruta=5).add(PedralumeMoney.from_units(refinada=1))

    assert money.raw_amount == 15
    assert money.to_units() == {"primordial": 0, "pura": 0, "refinada": 1, "bruta": 5}


def test_subtract_pedralume_money() -> None:
    money = PedralumeMoney.from_units(pura=1).subtract(PedralumeMoney.from_units(refinada=3))

    assert money.raw_amount == 70


def test_subtract_pedralume_money_rejects_negative_balance() -> None:
    with pytest.raises(ValueError):
        PedralumeMoney.from_units(bruta=1).subtract(PedralumeMoney.from_units(bruta=2))


def test_display_pedralume_money_in_organized_form() -> None:
    money = PedralumeMoney.from_units(primordial=1, pura=2, refinada=3, bruta=4)

    assert money.display() == (
        "1 Pedralume Primordial, 2 Pedralume Pura, 3 Pedralume Refinada, 4 Pedralume Bruta"
    )
