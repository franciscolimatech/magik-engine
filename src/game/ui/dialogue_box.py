"""Simple paginated retro dialogue box."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from src.game import colors
from src.game.settings import SCREEN_HEIGHT, SCREEN_WIDTH


@dataclass
class DialogueBox:
    speaker: str
    text: str | Iterable[str]
    visible: bool = True
    current_index: int = 0
    messages: tuple[str, ...] = field(init=False)

    def __post_init__(self) -> None:
        if isinstance(self.text, str):
            self.messages = (self.text,)
        else:
            self.messages = tuple(self.text)
        if not self.messages:
            self.messages = ("...",)

    @property
    def current_text(self) -> str:
        return self.messages[self.current_index]

    def advance(self) -> bool:
        if self.current_index < len(self.messages) - 1:
            self.current_index += 1
            return True
        self.close()
        return False

    def close(self) -> None:
        self.visible = False

    def draw(self, pygame, surface, font) -> None:
        if not self.visible:
            return
        rect = pygame.Rect(24, SCREEN_HEIGHT - 132, SCREEN_WIDTH - 48, 108)
        inner = rect.inflate(-10, -10)
        pygame.draw.rect(surface, colors.DIALOGUE_BG, rect)
        pygame.draw.rect(surface, colors.DIALOGUE_BORDER, rect, width=3)
        pygame.draw.rect(surface, colors.WHITE, inner, width=1)
        name_plate = pygame.Rect(rect.x + 14, rect.y - 10, 150, 22)
        pygame.draw.rect(surface, colors.DIALOGUE_BG, name_plate)
        pygame.draw.rect(surface, colors.DIALOGUE_BORDER, name_plate, width=2)
        speaker_surface = font.render(self.speaker, False, colors.WHITE)
        surface.blit(speaker_surface, (name_plate.x + 8, name_plate.y + 3))

        for index, line in enumerate(wrap_text(self.current_text, font, rect.width - 40)):
            if index >= 3:
                break
            line_surface = font.render(line, False, colors.WHITE)
            surface.blit(line_surface, (rect.x + 18, rect.y + 30 + index * 22))

        hint = "Espaco/Enter/E para avancar" if self.current_index < len(self.messages) - 1 else "Espaco/Enter/E para fechar"
        hint_surface = font.render(hint, False, colors.TEXT_MUTED)
        surface.blit(hint_surface, (rect.x + 18, rect.y + 84))


def wrap_text(text: str, font, max_width: int) -> list[str]:
    words = text.split()
    if not words:
        return [""]
    lines: list[str] = []
    current = words[0]
    for word in words[1:]:
        candidate = f"{current} {word}"
        if _text_width(font, candidate) <= max_width:
            current = candidate
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def _text_width(font, text: str) -> int:
    if hasattr(font, "size"):
        return font.size(text)[0]
    return len(text) * 8
