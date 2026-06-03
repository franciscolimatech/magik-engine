import pytest

from src.core.character import create_miko_meu
from src.systems.ikisaki import get_price_level, use_shadow_roulette


@pytest.mark.parametrize(
    ("number", "price_level"),
    [
        (1, "leve"),
        (3, "leve"),
        (4, "medio"),
        (6, "medio"),
        (7, "alto"),
        (9, "alto"),
        (10, "grave"),
    ],
)
def test_ikisaki_price_levels(number: int, price_level: str) -> None:
    assert get_price_level(number) == price_level


def test_ikisaki_roll_returns_link_data() -> None:
    miko = create_miko_meu()

    result = use_shadow_roulette(miko, forced_roll=1)

    assert result.number == 1
    assert result.link_name == "Corrente da Vergonha"
    assert result.price_level == "leve"
    assert result.chain_debt_generated is False
    assert result.switch_risk is False
    assert miko.last_ikisaki_result == 1


def test_repeated_ikisaki_number_marks_consequence() -> None:
    miko = create_miko_meu()
    miko.last_ikisaki_result = 5

    result = use_shadow_roulette(miko, forced_roll=5)

    assert result.repeated_number is True
    assert result.consequence is not None
    assert "Numero repetido" in result.consequence


@pytest.mark.parametrize("number", [7, 8, 9, 10])
def test_high_ikisaki_numbers_generate_chain_debt(number: int) -> None:
    miko = create_miko_meu()

    result = use_shadow_roulette(miko, forced_roll=number)

    assert result.chain_debt_generated is True
    assert result.total_chain_debts == 1
    assert miko.chain_debts == 1


def test_ikisaki_ten_has_grave_price_and_high_switch_risk() -> None:
    miko = create_miko_meu()

    result = use_shadow_roulette(miko, forced_roll=10)

    assert result.price_level == "grave"
    assert result.chain_debt_generated is True
    assert result.switch_risk is True
    assert result.switch_risk_level == "alto"


def test_three_chain_debts_generate_switch_risk() -> None:
    miko = create_miko_meu()
    miko.chain_debts = 2

    result = use_shadow_roulette(miko, forced_roll=7)

    assert result.total_chain_debts == 3
    assert result.switch_risk is True
    assert result.switch_risk_level == "ativo"
