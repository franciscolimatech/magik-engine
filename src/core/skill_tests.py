"""Official MAGIK 1d20 skill tests."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import random
from typing import Any, Protocol


class RandomLike(Protocol):
    def randint(self, a: int, b: int) -> int:
        """Return a random integer N such that a <= N <= b."""


@dataclass(frozen=True)
class SkillTestResult:
    test_type: str
    roll: int
    interpretation: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


TEST_TABLES: dict[str, tuple[str, tuple[str, str, str, str, str]]] = {
    "percepcao": (
        "Percepção",
        (
            "Nao percebe nada.",
            "Nota algo suspeito.",
            "Percebe o basico.",
            "Encontra detalhes importantes.",
            "Descobre algo que ninguem mais viu.",
        ),
    ),
    "furtividade": (
        "Furtividade",
        (
            "Faz barulho ou deixa rastros.",
            "Passa despercebido por pouco.",
            "Consegue se esconder.",
            "Fica praticamente invisivel.",
            "Ninguem sabe que voce esteve ali.",
        ),
    ),
    "forca": (
        "Força",
        (
            "Falha completamente.",
            "Move ou quebra algo pequeno.",
            "Consegue o esperado.",
            "Faz com facilidade.",
            "Demonstra forca extraordinaria.",
        ),
    ),
    "agilidade": (
        "Agilidade",
        (
            "Cai, tropeca ou e atingido.",
            "Consegue por pouco.",
            "Executa normalmente.",
            "Faz com grande precisao.",
            "Movimento quase sobre-humano.",
        ),
    ),
    "conhecimento": (
        "Conhecimento",
        (
            "Informacao errada.",
            "Lembra algo vago.",
            "Conhecimento comum.",
            "Conhecimento avancado.",
            "Descobre algo raro ou secreto.",
        ),
    ),
    "persuasao": (
        "Persuasao",
        (
            "Piora a situacao.",
            "A pessoa nao se convence.",
            "Consegue alguma cooperacao.",
            "Convence facilmente.",
            "A pessoa fica totalmente do seu lado.",
        ),
    ),
    "vontade": (
        "Vontade",
        (
            "Cede ao medo, dor ou influencia.",
            "Resiste parcialmente.",
            "Aguenta firme.",
            "Resiste sem dificuldade.",
            "Nem parece ter sido afetado.",
        ),
    ),
}


def list_test_types() -> list[str]:
    return [label for label, _table in TEST_TABLES.values()]


def interpret_skill_test(test_type: str, roll: int) -> str:
    if not 1 <= roll <= 20:
        raise ValueError("O resultado do teste deve estar entre 1 e 20.")

    _label, table = _get_test_table(test_type)
    if 1 <= roll <= 4:
        return table[0]
    if 5 <= roll <= 9:
        return table[1]
    if 10 <= roll <= 14:
        return table[2]
    if 15 <= roll <= 19:
        return table[3]
    return table[4]


def perform_skill_test(test_type: str, rng: RandomLike | None = None, forced_roll: int | None = None) -> SkillTestResult:
    label, _table = _get_test_table(test_type)
    roll = forced_roll if forced_roll is not None else (rng or random).randint(1, 20)
    return SkillTestResult(test_type=label, roll=roll, interpretation=interpret_skill_test(label, roll))


def _get_test_table(test_type: str) -> tuple[str, tuple[str, str, str, str, str]]:
    key = _normalize_test_type(test_type)
    try:
        return TEST_TABLES[key]
    except KeyError as exc:
        valid = ", ".join(list_test_types())
        raise ValueError(f"Tipo de teste invalido. Use um destes: {valid}.") from exc


def _normalize_test_type(test_type: str) -> str:
    normalized = test_type.strip().casefold()
    replacements = {"ç": "c", "ã": "a", "á": "a", "é": "e", "ê": "e", "í": "i"}
    for source, target in replacements.items():
        normalized = normalized.replace(source, target)
    return normalized
