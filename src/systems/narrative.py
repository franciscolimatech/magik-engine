"""Narrative engine tables for MAGIK v0.3.

This module uses controlled random tables only. It does not integrate AI and
does not decide outcomes for the game master.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import random
import unicodedata
from typing import Any, Protocol, Sequence, TypeVar

from src.core.session import SessionEvent, register_event
from src.storage.types import JsonStore


T = TypeVar("T")


class ChoiceLike(Protocol):
    def choice(self, sequence: Sequence[T]) -> T:
        """Return one item from a non-empty sequence."""


@dataclass(frozen=True)
class IkisakiLine:
    category: str
    text: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class NarrativeConsequence:
    price_level: str
    description: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RandomEvent:
    category: str
    description: str
    suggested_test: str | None
    possible_consequence: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Rumor:
    level: str
    text: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CurseOmen:
    description: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


IKISAKI_LINES: dict[str, tuple[str, ...]] = {
    "debochada": (
        "Miko, voce tem um plano ou so uma expressao confiante?",
        "Eu sou uma arma amaldicoada, nao uma corda de varal.",
    ),
    "combate": (
        "Corre. Eu gosto quando eles tentam.",
        "Braco, voz, sombra ou medo? Escolhe rapido, Miko.",
    ),
    "numero ruim na roleta": (
        "Numero 1? Parabens, Miko. Ate o azar ficou com vergonha.",
        "Isso foi baixo ate para uma corrente presa no escuro.",
    ),
    "numero alto na roleta": (
        "Agora ficou serio.",
        "Ultimo Elo? Miko... segura a respiracao.",
    ),
    "recusa em ajudar": (
        "Resolva com o graveto. Voce chama aquilo de cajado, ne?",
        "Hoje eu vou assistir. Me surpreenda, se conseguir.",
    ),
    "switch sombrio": (
        "Sai do caminho, Miko. Agora eu seguro as correntes.",
        "Chega. A sombra ja esperou demais.",
    ),
    "fala seria": (
        "Voce nao me carrega, Miko. Nos estamos presos um ao outro.",
        "Toda corrente tem dois lados. Lembre disso.",
    ),
    "cajado usado no lugar dela": (
        "Vai mesmo usar esse graveto?",
        "Que bonito. O cajado tentando parecer perigoso.",
    ),
}

NARRATIVE_CONSEQUENCES: dict[str, tuple[str, ...]] = {
    "leve": (
        "voz rouca por alguns segundos",
        "sombra mexe sozinha",
        "Ikisaki tira sarro",
        "pequeno arrepio",
    ),
    "medio": (
        "braco pesado",
        "penalidade leve narrativa",
        "Miko fica preso a propria palavra",
        "marca escura temporaria",
    ),
    "alto": (
        "Miko sente parte do medo do alvo",
        "fica exausto",
        "perde parte do proximo turno",
        "ganha uma Divida de Corrente narrativa",
        "tem uma visao curta da Floresta do Avesso",
    ),
    "grave": (
        "risco de Switch Sombrio",
        "perde proximo turno",
        "Ikisaki fica indisponivel por uma cena",
        "Miko esquece alguns segundos",
        "ouve a voz do Homem da Corrente",
    ),
}

RANDOM_EVENTS: tuple[RandomEvent, ...] = (
    RandomEvent(
        category="encontro estranho",
        description="Alguem aparece em um momento inconveniente e parece saber mais do que deveria.",
        suggested_test="Percepcao ou Persuasao",
        possible_consequence="O mestre pode revelar uma pista, uma mentira ou uma complicacao social.",
    ),
    RandomEvent(
        category="mudanca climatica",
        description="O tempo muda de forma repentina.",
        suggested_test="Conhecimento ou Vontade",
        possible_consequence="O mestre pode dificultar deslocamento, percepcao ou descanso.",
    ),
    RandomEvent(
        category="ruido suspeito",
        description="Um ruido curto surge perto o bastante para incomodar.",
        suggested_test="Percepcao ou Furtividade",
        possible_consequence="O mestre pode indicar presenca, armadilha ou apenas tensao.",
    ),
    RandomEvent(
        category="rastro",
        description="Marcas recentes no chao indicam que alguem passou por aqui com pressa.",
        suggested_test="Percepcao ou Conhecimento",
        possible_consequence="O mestre pode apontar direcao, urgencia ou uma pista incompleta.",
    ),
    RandomEvent(
        category="comerciante",
        description="Uma pessoa oferecendo troca ou informacao cruza o caminho do grupo.",
        suggested_test="Persuasao ou Conhecimento",
        possible_consequence="O mestre pode oferecer negociacao, rumor ou custo inesperado.",
    ),
    RandomEvent(
        category="criatura distante",
        description="Algo vivo se move longe demais para ser identificado com certeza.",
        suggested_test="Percepcao ou Vontade",
        possible_consequence="O mestre pode transformar isso em aviso, perseguicao ou falso alarme.",
    ),
    RandomEvent(
        category="pressagio magico",
        description="Um sinal magico breve aparece e some antes de ser explicado.",
        suggested_test="Conhecimento ou Vontade",
        possible_consequence="O mestre pode conectar o pressagio a uma magia, maldicao ou evento futuro.",
    ),
    RandomEvent(
        category="problema social",
        description="Uma tensao entre pessoas exige cuidado antes que piore.",
        suggested_test="Persuasao ou Vontade",
        possible_consequence="O mestre pode criar aliancas, conflito ou uma escolha desconfortavel.",
    ),
    RandomEvent(
        category="oportunidade",
        description="Surge uma abertura para agir antes que alguem perceba.",
        suggested_test="Agilidade, Furtividade ou Persuasao",
        possible_consequence="O mestre pode conceder vantagem narrativa se o grupo agir rapido.",
    ),
    RandomEvent(
        category="perigo imediato",
        description="Uma ameaca exige reacao agora.",
        suggested_test="Agilidade, Forca ou Vontade",
        possible_consequence="O mestre pode iniciar combate, fuga ou uma decisao de risco.",
    ),
)

RUMORS: tuple[Rumor, ...] = (
    Rumor("comum", "Dizem que algumas Pedralumes brilham mais forte perto de mentirosos."),
    Rumor("estranho", "Ouvi falar que viajantes somem quando ignoram placas velhas na estrada."),
    Rumor("perigoso", "Tem gente dizendo que a Floresta do Avesso responde quando alguem fala sozinho."),
    Rumor("possivelmente falso", "Um mercador jurou que certa sombra comprou passagem antes do proprio dono."),
)

CURSE_OMENS: tuple[CurseOmen, ...] = (
    CurseOmen("A sombra de Miko se mexe antes dele."),
    CurseOmen("Ikisaki fica em silencio por tempo demais."),
    CurseOmen("Um elo aparece onde nao deveria."),
    CurseOmen("Miko escuta correntes mesmo sem vento."),
    CurseOmen("A voz do Homem da Corrente surge em sonho."),
)


def generate_ikisaki_line(category: str, rng: ChoiceLike | None = None) -> IkisakiLine:
    normalized = _normalize_key(category)
    try:
        options = IKISAKI_LINES[normalized]
    except KeyError as exc:
        valid = ", ".join(IKISAKI_LINES)
        raise ValueError(f"Categoria de fala da Ikisaki invalida. Use uma destas: {valid}.") from exc
    return IkisakiLine(category=normalized, text=_choose(options, rng))


def ikisaki_debochada(rng: ChoiceLike | None = None) -> IkisakiLine:
    return generate_ikisaki_line("debochada", rng)


def ikisaki_combate(rng: ChoiceLike | None = None) -> IkisakiLine:
    return generate_ikisaki_line("combate", rng)


def ikisaki_numero_ruim(rng: ChoiceLike | None = None) -> IkisakiLine:
    return generate_ikisaki_line("numero ruim na roleta", rng)


def ikisaki_numero_alto(rng: ChoiceLike | None = None) -> IkisakiLine:
    return generate_ikisaki_line("numero alto na roleta", rng)


def ikisaki_recusa(rng: ChoiceLike | None = None) -> IkisakiLine:
    return generate_ikisaki_line("recusa em ajudar", rng)


def ikisaki_switch_sombrio(rng: ChoiceLike | None = None) -> IkisakiLine:
    return generate_ikisaki_line("switch sombrio", rng)


def ikisaki_fala_seria(rng: ChoiceLike | None = None) -> IkisakiLine:
    return generate_ikisaki_line("fala seria", rng)


def ikisaki_cajado(rng: ChoiceLike | None = None) -> IkisakiLine:
    return generate_ikisaki_line("cajado usado no lugar dela", rng)


def generate_narrative_consequence(price_level: str, rng: ChoiceLike | None = None) -> NarrativeConsequence:
    normalized = _normalize_key(price_level)
    try:
        options = NARRATIVE_CONSEQUENCES[normalized]
    except KeyError as exc:
        valid = ", ".join(NARRATIVE_CONSEQUENCES)
        raise ValueError(f"Preco narrativo invalido. Use um destes: {valid}.") from exc
    return NarrativeConsequence(price_level=normalized, description=_choose(options, rng))


def generate_random_event(rng: ChoiceLike | None = None) -> RandomEvent:
    return _choose(RANDOM_EVENTS, rng)


def generate_rumor(rng: ChoiceLike | None = None) -> Rumor:
    return _choose(RUMORS, rng)


def generate_curse_omen(rng: ChoiceLike | None = None) -> CurseOmen:
    return _choose(CURSE_OMENS, rng)


def record_narrative_result(
    storage: JsonStore,
    action: str,
    result: str,
    character: str = "Narrador",
    notes: str = "",
) -> SessionEvent:
    return register_event(storage=storage, character=character, action=action, result=result, notes=notes)


def list_ikisaki_line_categories() -> list[str]:
    return list(IKISAKI_LINES)


def list_consequence_price_levels() -> list[str]:
    return list(NARRATIVE_CONSEQUENCES)


def _choose(options: Sequence[T], rng: ChoiceLike | None) -> T:
    if not options:
        raise ValueError("Tabela narrativa vazia.")
    chooser = rng or random
    return chooser.choice(options)


def _normalize_key(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.strip().casefold())
    ascii_only = "".join(character for character in normalized if not unicodedata.combining(character))
    return " ".join(ascii_only.split())
