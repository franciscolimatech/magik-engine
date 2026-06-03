import pytest

from src.core.skill_tests import interpret_skill_test, perform_skill_test


@pytest.mark.parametrize(
    ("roll", "interpretation"),
    [
        (1, "Nao percebe nada."),
        (5, "Nota algo suspeito."),
        (10, "Percebe o basico."),
        (15, "Encontra detalhes importantes."),
        (20, "Descobre algo que ninguem mais viu."),
    ],
)
def test_interpret_skill_test_uses_official_ranges(roll: int, interpretation: str) -> None:
    assert interpret_skill_test("Percepcao", roll) == interpretation


def test_perform_skill_test_returns_roll_and_interpretation() -> None:
    result = perform_skill_test("Força", forced_roll=20)

    assert result.test_type == "Força"
    assert result.roll == 20
    assert result.interpretation == "Demonstra forca extraordinaria."


def test_invalid_skill_test_type_raises_error() -> None:
    with pytest.raises(ValueError):
        perform_skill_test("Culinaria", forced_roll=10)
