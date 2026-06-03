"""Ikisaki's shadow roulette system."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import random
from typing import Any, Protocol

from src.core.character import Character
from src.systems.curses import chain_debt_generates_switch_risk


class RandomLike(Protocol):
    def randint(self, a: int, b: int) -> int:
        """Return a random integer N such that a <= N <= b."""


@dataclass(frozen=True)
class ChainLink:
    number: int
    name: str
    description: str


@dataclass(frozen=True)
class IkisakiResult:
    number: int
    link_name: str
    effect_description: str
    price_level: str
    repeated_number: bool
    chain_debt_generated: bool
    switch_risk: bool
    switch_risk_level: str | None
    consequence: str | None
    total_chain_debts: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


CHAIN_LINKS: dict[int, ChainLink] = {
    1: ChainLink(1, "Corrente da Vergonha", "A sombra prende o orgulho do alvo e o faz hesitar diante de todos."),
    2: ChainLink(2, "Corrente do Tornozelo Covarde", "Um elo rasteiro atrapalha fuga, corrida ou posicionamento do alvo."),
    3: ChainLink(3, "Corrente Cala-Boca", "A corrente abafa uma fala, comando ou provocacao no pior momento possivel."),
    4: ChainLink(4, "Corrente do Peso Morto", "O corpo do alvo fica pesado como se a propria sombra o puxasse para baixo."),
    5: ChainLink(5, "Corrente do Reflexo Torto", "A imagem do alvo se atrasa e confunde reacoes rapidas."),
    6: ChainLink(6, "Corrente da Promessa", "Ikisaki cobra uma promessa simples antes de liberar todo o efeito."),
    7: ChainLink(7, "Corrente Come-Medo", "A corrente devora medo ao redor e deixa Miko perigosamente faminto por mais sombra."),
    8: ChainLink(8, "Corrente Guarda-Costas", "Elos sombrios protegem Miko, mas se agarram a ele como cobradores irritados."),
    9: ChainLink(9, "Corrente Carrasco da Sombra", "A sombra golpeia com crueldade e deixa uma marca dificil de ignorar."),
    10: ChainLink(10, "Corrente do Ultimo Elo", "Ikisaki solta um elo proibido, forte demais para sair sem cobrar um preco grave."),
}

REPEATED_NUMBER_CONSEQUENCE = (
    "Numero repetido: Ikisaki fica dramatico, exige reconhecimento publico e complica a cena "
    "com uma inconveniencia sombria."
)


def get_price_level(number: int) -> str:
    if 1 <= number <= 3:
        return "leve"
    if 4 <= number <= 6:
        return "medio"
    if 7 <= number <= 9:
        return "alto"
    if number == 10:
        return "grave"
    raise ValueError("O numero da Ikisaki deve estar entre 1 e 10.")


def generates_chain_debt(number: int) -> bool:
    if not 1 <= number <= 10:
        raise ValueError("O numero da Ikisaki deve estar entre 1 e 10.")
    return number >= 7


def use_shadow_roulette(
    character: Character,
    rng: RandomLike | None = None,
    forced_roll: int | None = None,
) -> IkisakiResult:
    """Use Roleta Sombria: Dez Elos de Ikisaki and update the character sheet."""
    if not character.ikisaki_available:
        raise RuntimeError("Ikisaki esta indisponivel. Use o Cajado Sombrio.")

    number = forced_roll if forced_roll is not None else (rng or random).randint(1, 10)
    if number not in CHAIN_LINKS:
        raise ValueError("O numero da Ikisaki deve estar entre 1 e 10.")

    repeated = character.last_ikisaki_result == number
    debt_generated = generates_chain_debt(number)
    if debt_generated:
        character.chain_debts += 1

    character.last_ikisaki_result = number
    link = CHAIN_LINKS[number]
    price_level = get_price_level(number)
    switch_risk = number == 10 or chain_debt_generates_switch_risk(character.chain_debts)
    switch_risk_level = _switch_risk_level(number, character.chain_debts)

    return IkisakiResult(
        number=number,
        link_name=link.name,
        effect_description=link.description,
        price_level=price_level,
        repeated_number=repeated,
        chain_debt_generated=debt_generated,
        switch_risk=switch_risk,
        switch_risk_level=switch_risk_level,
        consequence=REPEATED_NUMBER_CONSEQUENCE if repeated else None,
        total_chain_debts=character.chain_debts,
    )


def _switch_risk_level(number: int, chain_debts: int) -> str | None:
    if number == 10:
        return "alto"
    if chain_debts >= 3:
        return "ativo"
    return None
