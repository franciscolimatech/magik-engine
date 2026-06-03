"""Narrative engine tables for MAGIK v0.3.1.

This module uses controlled random tables only. It does not integrate AI and
does not decide outcomes for the game master.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import random
import unicodedata
from typing import Any, Protocol, Sequence, TypeVar

from src.core.session import SessionEvent, register_event
from src.storage.types import JsonStore


T = TypeVar("T")

VALID_TONES = ("neutro", "sombrio", "engracado", "perigoso", "misterioso")


class ChoiceLike(Protocol):
    def choice(self, sequence: Sequence[T]) -> T:
        """Return one item from a non-empty sequence."""


@dataclass(frozen=True)
class NarrativeResult:
    tipo: str
    categoria: str
    tom: str
    texto: str
    teste_sugerido: str | None = None
    consequencia_possivel: str | None = None
    registrar_no_historico: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def type(self) -> str:
        return self.tipo

    @property
    def category(self) -> str:
        return self.categoria

    @property
    def tone(self) -> str:
        return self.tom

    @property
    def text(self) -> str:
        return self.texto

    @property
    def description(self) -> str:
        return self.texto

    @property
    def suggested_test(self) -> str | None:
        return self.teste_sugerido

    @property
    def possible_consequence(self) -> str | None:
        return self.consequencia_possivel

    @property
    def price_level(self) -> str:
        return str(self.metadata.get("price_level", self.categoria))

    @property
    def level(self) -> str:
        return str(self.metadata.get("level", self.categoria))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


IkisakiLine = NarrativeResult
NarrativeConsequence = NarrativeResult
RandomEvent = NarrativeResult
Rumor = NarrativeResult
CurseOmen = NarrativeResult


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
        tipo="evento aleatorio",
        categoria="encontro estranho",
        tom="neutro",
        texto="Alguem aparece em um momento inconveniente e parece saber mais do que deveria.",
        teste_sugerido="Percepcao ou Persuasao",
        consequencia_possivel="O mestre pode revelar uma pista, uma mentira ou uma complicacao social.",
    ),
    RandomEvent(
        tipo="evento aleatorio",
        categoria="mudanca climatica",
        tom="neutro",
        texto="O tempo muda de forma repentina.",
        teste_sugerido="Conhecimento ou Vontade",
        consequencia_possivel="O mestre pode dificultar deslocamento, percepcao ou descanso.",
    ),
    RandomEvent(
        tipo="evento aleatorio",
        categoria="ruido suspeito",
        tom="misterioso",
        texto="Um ruido curto surge perto o bastante para incomodar.",
        teste_sugerido="Percepcao ou Furtividade",
        consequencia_possivel="O mestre pode indicar presenca, armadilha ou apenas tensao.",
    ),
    RandomEvent(
        tipo="evento aleatorio",
        categoria="rastro",
        tom="misterioso",
        texto="Marcas recentes no chao indicam que alguem passou por aqui com pressa.",
        teste_sugerido="Percepcao ou Conhecimento",
        consequencia_possivel="O mestre pode apontar direcao, urgencia ou uma pista incompleta.",
    ),
    RandomEvent(
        tipo="evento aleatorio",
        categoria="comerciante",
        tom="neutro",
        texto="Uma pessoa oferecendo troca ou informacao cruza o caminho do grupo.",
        teste_sugerido="Persuasao ou Conhecimento",
        consequencia_possivel="O mestre pode oferecer negociacao, rumor ou custo inesperado.",
    ),
    RandomEvent(
        tipo="evento aleatorio",
        categoria="criatura distante",
        tom="sombrio",
        texto="Algo vivo se move longe demais para ser identificado com certeza.",
        teste_sugerido="Percepcao ou Vontade",
        consequencia_possivel="O mestre pode transformar isso em aviso, perseguicao ou falso alarme.",
    ),
    RandomEvent(
        tipo="evento aleatorio",
        categoria="pressagio magico",
        tom="sombrio",
        texto="Um sinal magico breve aparece e some antes de ser explicado.",
        teste_sugerido="Conhecimento ou Vontade",
        consequencia_possivel="O mestre pode conectar o pressagio a uma magia, maldicao ou evento futuro.",
    ),
    RandomEvent(
        tipo="evento aleatorio",
        categoria="problema social",
        tom="neutro",
        texto="Uma tensao entre pessoas exige cuidado antes que piore.",
        teste_sugerido="Persuasao ou Vontade",
        consequencia_possivel="O mestre pode criar aliancas, conflito ou uma escolha desconfortavel.",
    ),
    RandomEvent(
        tipo="evento aleatorio",
        categoria="oportunidade",
        tom="neutro",
        texto="Surge uma abertura para agir antes que alguem perceba.",
        teste_sugerido="Agilidade, Furtividade ou Persuasao",
        consequencia_possivel="O mestre pode conceder vantagem narrativa se o grupo agir rapido.",
    ),
    RandomEvent(
        tipo="evento aleatorio",
        categoria="perigo imediato",
        tom="perigoso",
        texto="Uma ameaca exige reacao agora.",
        teste_sugerido="Agilidade, Forca ou Vontade",
        consequencia_possivel="O mestre pode iniciar combate, fuga ou uma decisao de risco.",
    ),
)

RUMORS: tuple[Rumor, ...] = (
    Rumor(
        tipo="rumor",
        categoria="comum",
        tom="neutro",
        texto="Dizem que algumas Pedralumes brilham mais forte perto de mentirosos.",
        metadata={"level": "comum"},
    ),
    Rumor(
        tipo="rumor",
        categoria="estranho",
        tom="misterioso",
        texto="Ouvi falar que viajantes somem quando ignoram placas velhas na estrada.",
        metadata={"level": "estranho"},
    ),
    Rumor(
        tipo="rumor",
        categoria="perigoso",
        tom="perigoso",
        texto="Tem gente dizendo que a Floresta do Avesso responde quando alguem fala sozinho.",
        metadata={"level": "perigoso"},
    ),
    Rumor(
        tipo="rumor",
        categoria="possivelmente falso",
        tom="engracado",
        texto="Um mercador jurou que certa sombra comprou passagem antes do proprio dono.",
        metadata={"level": "possivelmente falso"},
    ),
)

CURSE_OMENS: tuple[CurseOmen, ...] = (
    CurseOmen(tipo="pressagio", categoria="maldicao de Ikisaki", tom="sombrio", texto="A sombra de Miko se mexe antes dele."),
    CurseOmen(tipo="pressagio", categoria="maldicao de Ikisaki", tom="misterioso", texto="Ikisaki fica em silencio por tempo demais."),
    CurseOmen(tipo="pressagio", categoria="maldicao de Ikisaki", tom="misterioso", texto="Um elo aparece onde nao deveria."),
    CurseOmen(tipo="pressagio", categoria="maldicao de Ikisaki", tom="sombrio", texto="Miko escuta correntes mesmo sem vento."),
    CurseOmen(tipo="pressagio", categoria="maldicao de Ikisaki", tom="perigoso", texto="A voz do Homem da Corrente surge em sonho."),
)

LOCATION_TYPE_EVENT_CATEGORIES: dict[str, tuple[str, ...]] = {
    "capital": ("comerciante", "problema social", "oportunidade", "encontro estranho"),
    "cidade": ("comerciante", "problema social", "oportunidade", "encontro estranho"),
    "vila": ("problema social", "comerciante", "rumor", "oportunidade"),
    "mini vilarejo": ("problema social", "encontro estranho", "oportunidade", "ruido suspeito"),
    "regiao": ("mudanca climatica", "rastro", "criatura distante", "oportunidade"),
    "floresta": ("rastro", "ruido suspeito", "criatura distante", "pressagio magico"),
    "montanha": ("mudanca climatica", "perigo imediato", "rastro", "criatura distante"),
    "lago": ("mudanca climatica", "ruido suspeito", "pressagio magico", "criatura distante"),
    "estrada": ("rastro", "comerciante", "encontro estranho", "perigo imediato"),
    "vale": ("mudanca climatica", "rastro", "oportunidade", "criatura distante"),
    "brejo": ("rastro", "ruido suspeito", "perigo imediato", "pressagio magico"),
    "penhasco": ("perigo imediato", "mudanca climatica", "rastro", "pressagio magico"),
}

TONE_EVENT_CATEGORIES: dict[str, tuple[str, ...]] = {
    "neutro": tuple(event.categoria for event in RANDOM_EVENTS),
    "sombrio": ("criatura distante", "pressagio magico", "ruido suspeito", "rastro"),
    "engracado": ("comerciante", "encontro estranho", "problema social", "oportunidade"),
    "perigoso": ("perigo imediato", "criatura distante", "rastro", "ruido suspeito"),
    "misterioso": ("pressagio magico", "ruido suspeito", "rastro", "encontro estranho"),
}

TONE_RUMOR_LEVELS: dict[str, tuple[str, ...]] = {
    "neutro": tuple(rumor.categoria for rumor in RUMORS),
    "sombrio": ("estranho", "perigoso"),
    "engracado": ("possivelmente falso", "comum"),
    "perigoso": ("perigoso", "estranho"),
    "misterioso": ("estranho", "comum", "possivelmente falso"),
}

_LAST_RESULTS: dict[str, str] = {}


def generate_ikisaki_line(category: str, rng: ChoiceLike | None = None) -> IkisakiLine:
    normalized = _normalize_key(category)
    try:
        options = IKISAKI_LINES[normalized]
    except KeyError as exc:
        valid = ", ".join(IKISAKI_LINES)
        raise ValueError(f"Categoria de fala da Ikisaki invalida. Use uma destas: {valid}.") from exc
    text = _choose_without_immediate_repeat(options, rng, memory_key=f"ikisaki:{normalized}")
    return NarrativeResult(tipo="fala da Ikisaki", categoria=normalized, tom="neutro", texto=text)


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


def generate_narrative_consequence(
    price_level: str,
    tone: str | None = None,
    rng: ChoiceLike | None = None,
) -> NarrativeConsequence:
    normalized_price = _normalize_key(price_level)
    normalized_tone = normalize_tone(tone)
    try:
        options = NARRATIVE_CONSEQUENCES[normalized_price]
    except KeyError as exc:
        valid = ", ".join(NARRATIVE_CONSEQUENCES)
        raise ValueError(f"Preco narrativo invalido. Use um destes: {valid}.") from exc
    text = _choose_without_immediate_repeat(
        options,
        rng,
        memory_key=f"consequence:{normalized_price}:{normalized_tone}",
    )
    return NarrativeResult(
        tipo="consequencia narrativa",
        categoria=normalized_price,
        tom=normalized_tone,
        texto=text,
        metadata={"price_level": normalized_price},
    )


def generate_random_event(
    tone: str | None = None,
    location_type: str | None = None,
    rng: ChoiceLike | None = None,
) -> RandomEvent:
    normalized_tone = normalize_tone(tone)
    options = _filter_events_by_context(normalized_tone, location_type)
    event = _choose_without_immediate_repeat(
        options,
        rng,
        memory_key=f"event:{normalized_tone}:{_normalize_optional(location_type)}",
    )
    return _copy_result(event, tom=normalized_tone)


def generate_rumor(tone: str | None = None, rng: ChoiceLike | None = None) -> Rumor:
    normalized_tone = normalize_tone(tone)
    allowed_levels = TONE_RUMOR_LEVELS[normalized_tone]
    options = tuple(rumor for rumor in RUMORS if rumor.categoria in allowed_levels)
    rumor = _choose_without_immediate_repeat(options, rng, memory_key=f"rumor:{normalized_tone}")
    return _copy_result(rumor, tom=normalized_tone)


def generate_curse_omen(rng: ChoiceLike | None = None) -> CurseOmen:
    return _choose_without_immediate_repeat(CURSE_OMENS, rng, memory_key="curse_omen")


def narrate_ikisaki_roulette(roulette_result: Any, tone: str | None = None) -> NarrativeResult:
    normalized_tone = normalize_tone(tone)
    number = int(roulette_result.number)
    link_name = str(roulette_result.link_name)
    price_level = str(roulette_result.price_level)

    fragments = [
        f"Ikisaki revela o numero {number}: {link_name}.",
        f"O preco marcado e {price_level}.",
    ]
    if getattr(roulette_result, "repeated_number", False):
        fragments.append("O numero repetido faz a corrente reagir como se reconhecesse uma piada interna cruel.")
    if getattr(roulette_result, "chain_debt_generated", False):
        fragments.append("Um elo novo parece pesar no ar: uma Divida de Corrente foi gerada.")
    if getattr(roulette_result, "switch_risk", False):
        fragments.append(
            "Ikisaki para de rir. Por um instante, Miko sente que nao esta segurando a corrente; "
            "e ela que esta segurando ele."
        )
    else:
        fragments.append("A sombra se acomoda, esperando a decisao do mestre sobre como a cena continua.")

    return NarrativeResult(
        tipo="narrativa da roleta",
        categoria=price_level,
        tom=normalized_tone,
        texto=" ".join(fragments),
        consequencia_possivel="Descricao narrativa apenas; nao altera as regras da roleta.",
        metadata={
            "number": number,
            "link_name": link_name,
            "price_level": price_level,
            "repeated_number": bool(getattr(roulette_result, "repeated_number", False)),
            "chain_debt_generated": bool(getattr(roulette_result, "chain_debt_generated", False)),
            "switch_risk": bool(getattr(roulette_result, "switch_risk", False)),
        },
    )


def maybe_record_narrative_result(
    storage: JsonStore,
    narrative_result: NarrativeResult,
    should_register: bool,
    character: str = "Narrador",
    action: str | None = None,
    notes: str = "",
) -> SessionEvent | None:
    if not should_register or not narrative_result.registrar_no_historico:
        return None
    return record_narrative_result(
        storage=storage,
        character=character,
        action=action or narrative_result.tipo,
        result=narrative_result.texto,
        notes=notes or _build_history_notes(narrative_result),
    )


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


def list_tones() -> list[str]:
    return list(VALID_TONES)


def list_location_types() -> list[str]:
    return list(LOCATION_TYPE_EVENT_CATEGORIES)


def normalize_tone(tone: str | None) -> str:
    if tone is None or not tone.strip():
        return "neutro"
    normalized = _normalize_key(tone)
    if normalized not in VALID_TONES:
        valid = ", ".join(VALID_TONES)
        raise ValueError(f"Tom narrativo invalido. Use um destes: {valid}.")
    return normalized


def reset_narrative_memory() -> None:
    _LAST_RESULTS.clear()


def _filter_events_by_context(tone: str, location_type: str | None) -> tuple[RandomEvent, ...]:
    tone_categories = set(TONE_EVENT_CATEGORIES[tone])
    options = tuple(event for event in RANDOM_EVENTS if event.categoria in tone_categories)

    normalized_location_type = _normalize_optional(location_type)
    if not normalized_location_type:
        return options
    if normalized_location_type not in LOCATION_TYPE_EVENT_CATEGORIES:
        valid = ", ".join(LOCATION_TYPE_EVENT_CATEGORIES)
        raise ValueError(f"Tipo de local invalido. Use um destes: {valid}.")

    location_categories = set(LOCATION_TYPE_EVENT_CATEGORIES[normalized_location_type])
    contextual_options = tuple(event for event in options if event.categoria in location_categories)
    if contextual_options:
        return contextual_options
    return tuple(event for event in RANDOM_EVENTS if event.categoria in location_categories)


def _choose_without_immediate_repeat(options: Sequence[T], rng: ChoiceLike | None, memory_key: str) -> T:
    if not options:
        raise ValueError("Tabela narrativa vazia.")

    last_identity = _LAST_RESULTS.get(memory_key)
    available = list(options)
    if len(available) > 1:
        filtered = [option for option in available if _result_identity(option) != last_identity]
        if filtered:
            available = filtered

    chooser = rng or random
    selected = chooser.choice(tuple(available))
    _LAST_RESULTS[memory_key] = _result_identity(selected)
    return selected


def _copy_result(result: NarrativeResult, tom: str | None = None) -> NarrativeResult:
    return NarrativeResult(
        tipo=result.tipo,
        categoria=result.categoria,
        tom=tom or result.tom,
        texto=result.texto,
        teste_sugerido=result.teste_sugerido,
        consequencia_possivel=result.consequencia_possivel,
        registrar_no_historico=result.registrar_no_historico,
        metadata=dict(result.metadata),
    )


def _build_history_notes(result: NarrativeResult) -> str:
    parts: list[str] = [f"Tom: {result.tom}"]
    if result.teste_sugerido:
        parts.append(f"Teste sugerido: {result.teste_sugerido}")
    if result.consequencia_possivel:
        parts.append(f"Possivel consequencia: {result.consequencia_possivel}")
    return ". ".join(parts)


def _result_identity(result: Any) -> str:
    if isinstance(result, NarrativeResult):
        return result.texto
    return str(result)


def _normalize_optional(value: str | None) -> str:
    if value is None:
        return ""
    return _normalize_key(value)


def _normalize_key(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.strip().casefold())
    ascii_only = "".join(character for character in normalized if not unicodedata.combining(character))
    return " ".join(ascii_only.split())
