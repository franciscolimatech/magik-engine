"""Simple in-memory map events for the 2D prototype."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.game.dialogue import DialogueChoice, DialogueOption


@dataclass(frozen=True)
class MapEvent:
    id: str
    x: int
    y: int
    event_type: str
    messages: tuple[str, ...]
    speaker: str = "Evento"
    repeatable: bool = False
    registrar_no_historico: bool = True
    tags: tuple[str, ...] = ()
    choice: DialogueChoice | None = None
    location_id: str | None = None
    narrative_conditions: dict[str, Any] = field(default_factory=dict)
    narrative_effects: dict[str, Any] = field(default_factory=dict)

    def can_trigger(self, triggered_event_ids: set[str]) -> bool:
        return self.repeatable or self.id not in triggered_event_ids

    @property
    def text(self) -> str:
        return " ".join(self.messages)


TEST_EVENTS = [
    MapEvent(
        id="evento-sombra-observa",
        x=9,
        y=4,
        event_type="pressagio",
        speaker="Sombra entre arvores",
        messages=(
            "Entre as arvores retorcidas, uma sombra se move antes do seu proprio corpo.",
            "Ela nao ataca. Apenas observa.",
        ),
        repeatable=False,
        registrar_no_historico=True,
        tags=("floresta-do-avesso", "sombra", "prova-de-conceito"),
        location_id="floresta-do-avesso",
        narrative_conditions={
            "blocked_story_flags": ["viu_sombra_na_floresta_do_avesso"],
        },
        narrative_effects={
            "add_story_flags": ["viu_sombra_na_floresta_do_avesso"],
            "add_world_flags": ["floresta_do_avesso_inquieta"],
            "important_choice": {
                "id": "evento-sombra-observa-escolha",
                "location_id": "floresta-do-avesso",
                "choice": "O jogador encontrou a sombra da Floresta do Avesso.",
            },
            "narrative_consequence": {
                "id": "evento-sombra-observa-consequencia",
                "location_id": "floresta-do-avesso",
                "text": "A Floresta do Avesso pareceu notar que o personagem tambem observa de volta.",
            },
        },
        choice=DialogueChoice(
            question="O que voce faz diante da sombra?",
            options=(
                DialogueOption(
                    text="Observar em silencio.",
                    response="A sombra inclina a cabeca sem ter cabeca. O silencio fica pesado, mas nao hostil.",
                    tags=("silencio", "observacao"),
                    event="observar_sombra",
                ),
                DialogueOption(
                    text="Chamar pela sombra.",
                    response="O chamado volta baixo demais, como se a propria floresta repetisse seu nome.",
                    tags=("chamar", "sombra"),
                    event="chamar_sombra",
                ),
                DialogueOption(
                    text="Ignorar e seguir.",
                    response="Voce segue, mas por alguns passos sua sombra parece atrasada.",
                    tags=("ignorar", "cautela"),
                    event="ignorar_sombra",
                ),
            ),
        ),
    ),
    MapEvent(
        id="ikisaki-stir",
        x=14,
        y=4,
        event_type="pressagio",
        speaker="Pressagio",
        messages=(
            "Voce sente Ikisaki se mexer sozinha.",
            "Os elos fazem um som baixo, como se rissem por dentro.",
        ),
        repeatable=False,
        registrar_no_historico=True,
        tags=("ikisaki", "pressagio"),
        choice=DialogueChoice(
            question="Ikisaki se mexe sozinha. Voce toca a corrente?",
            options=(
                DialogueOption(
                    text="Tocar",
                    response="A corrente esta fria demais para metal. Por um segundo, ela aperta de volta.",
                    tags=("toque", "ikisaki"),
                ),
                DialogueOption(
                    text="Ignorar",
                    response="Ikisaki fica quieta, mas o silencio dela parece uma risada guardada.",
                    tags=("ignorar",),
                ),
                DialogueOption(
                    text="Falar com ela",
                    response="Os elos tilintam uma vez, como se aprovassem a falta de bom senso.",
                    tags=("conversa", "ikisaki"),
                ),
            ),
        ),
    ),
    MapEvent(
        id="old-sign",
        x=22,
        y=9,
        event_type="mensagem",
        speaker="Placa antiga",
        messages=("A madeira diz: volte antes que o brejo aprenda seu nome.",),
        repeatable=True,
        registrar_no_historico=False,
        tags=("placa", "mensagem"),
    ),
]


def load_test_events() -> list[MapEvent]:
    return list(TEST_EVENTS)


def find_event_at(events: list[MapEvent], x: int, y: int) -> MapEvent | None:
    return next((event for event in events if event.x == x and event.y == y), None)
