"""Dialogue data structures for the 2D prototype."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class DialogueOption:
    text: str
    response: str
    tags: tuple[str, ...] = ()
    event: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "tags", tuple(self.tags))


@dataclass(frozen=True)
class DialogueChoice:
    question: str
    options: tuple[DialogueOption, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "options", tuple(self.options))
        if not self.options:
            raise ValueError("Escolha de dialogo precisa ter pelo menos uma opcao.")


@dataclass(frozen=True)
class DialogueContent:
    speaker: str
    messages: tuple[str, ...]
    choice: DialogueChoice | None = None


def normalize_messages(text: str | Iterable[str]) -> tuple[str, ...]:
    if isinstance(text, str):
        messages = (text,)
    else:
        messages = tuple(text)
    return messages or ("...",)
