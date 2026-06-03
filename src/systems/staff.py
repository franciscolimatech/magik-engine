"""Cajado Sombrio fallback spells."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class StaffSpell:
    name: str
    description: str
    effect: str
    suggested_test: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


STAFF_SPELLS: dict[str, StaffSpell] = {
    "estalo sombrio": StaffSpell(
        name="Estalo Sombrio",
        description="Um disparo curto de sombra estala contra um alvo visivel.",
        effect="Causa impacto leve ou interrompe uma acao simples.",
        suggested_test="Teste de ataque ou precisao contra a defesa do alvo.",
    ),
    "nevoa de medo": StaffSpell(
        name="Nevoa de Medo",
        description="Uma nevoa baixa envolve a area e amplifica receios pequenos.",
        effect="Dificulta percepcao e pode impor hesitacao narrativa.",
        suggested_test="Teste de vontade dos afetados ou teste de ocultacao de Miko.",
    ),
    "toque frio": StaffSpell(
        name="Toque Frio",
        description="O cajado conduz frio sombrio pelo toque.",
        effect="Reduz vigor, firmeza ou velocidade do alvo por uma cena curta.",
        suggested_test="Teste corpo a corpo ou resistencia do alvo.",
    ),
    "marca da sombra": StaffSpell(
        name="Marca da Sombra",
        description="Uma marca discreta prende a sombra de alguem ao olhar de Miko.",
        effect="Ajuda a rastrear ou reconhecer o marcado enquanto a cena durar.",
        suggested_test="Teste de magia, foco ou percepcao.",
    ),
    "passo escuro": StaffSpell(
        name="Passo Escuro",
        description="Miko usa uma sombra proxima para reposicionar poucos passos.",
        effect="Permite deslocamento curto, furtivo ou dramaticamente conveniente.",
        suggested_test="Teste de furtividade ou agilidade.",
    ),
}


def list_staff_spells() -> list[StaffSpell]:
    return list(STAFF_SPELLS.values())


def get_staff_spell(name: str) -> StaffSpell:
    key = name.strip().casefold()
    try:
        return STAFF_SPELLS[key]
    except KeyError as exc:
        raise ValueError("Magia do Cajado Sombrio nao encontrada.") from exc
