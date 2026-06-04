"""Simple in-memory map events for the 2D prototype."""

from __future__ import annotations

from dataclasses import dataclass


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

    def can_trigger(self, triggered_event_ids: set[str]) -> bool:
        return self.repeatable or self.id not in triggered_event_ids

    @property
    def text(self) -> str:
        return " ".join(self.messages)


TEST_EVENTS = [
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
