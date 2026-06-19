"""Simple paginated retro dialogue box."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from src.game.dialogue import DialogueChoice, DialogueOption, normalize_messages
from src.game.ui.panels import (
    PANEL_GOLD,
    TEXT_IVORY,
    TEXT_MUTED,
    draw_dark_fantasy_panel,
    draw_panel_separator,
)


@dataclass
class DialogueBox:
    speaker: str
    text: str | Iterable[str]
    choice: DialogueChoice | None = None
    visible: bool = True
    current_index: int = 0
    mode: str = "message"
    selected_option_index: int = 0
    chosen_option: DialogueOption | None = None
    response_text: str = ""
    messages: tuple[str, ...] = field(init=False)

    def __post_init__(self) -> None:
        self.messages = normalize_messages(self.text)

    @property
    def current_text(self) -> str:
        if self.mode == "choice" and self.choice is not None:
            return self.choice.question
        if self.mode == "response":
            return self.response_text
        return self.messages[self.current_index]

    def advance(self) -> bool:
        if self.mode == "response":
            self.close()
            return False
        if self.current_index < len(self.messages) - 1:
            self.current_index += 1
            return True
        if self.choice is not None:
            self.mode = "choice"
            return True
        self.close()
        return False

    def select_next(self) -> None:
        if self.mode == "choice" and self.choice is not None:
            self.selected_option_index = (self.selected_option_index + 1) % len(self.choice.options)

    def select_previous(self) -> None:
        if self.mode == "choice" and self.choice is not None:
            self.selected_option_index = (self.selected_option_index - 1) % len(self.choice.options)

    def confirm_choice(self) -> DialogueOption | None:
        if self.mode != "choice" or self.choice is None:
            return None
        option = self.choice.options[self.selected_option_index]
        self.chosen_option = option
        self.response_text = option.response or "..."
        self.mode = "response"
        return option

    def handle_key(self, pygame, key: int) -> DialogueOption | None:
        if self.mode == "choice":
            if key in {pygame.K_DOWN, pygame.K_s}:
                self.select_next()
            elif key in {pygame.K_UP, pygame.K_w}:
                self.select_previous()
            elif key in {pygame.K_SPACE, pygame.K_e, pygame.K_RETURN}:
                return self.confirm_choice()
            return None
        if key in {pygame.K_SPACE, pygame.K_e, pygame.K_RETURN}:
            self.advance()
        return None

    def close(self) -> None:
        self.visible = False

    def draw(self, pygame, surface, font) -> None:
        if not self.visible:
            return
        rect = dialogue_panel_rect(pygame, surface)
        draw_dark_fantasy_panel(pygame, surface, rect, alpha=236, border_radius=8)
        draw_panel_separator(pygame, surface, (rect.x + 20, rect.y + 38), (rect.right - 20, rect.y + 38))
        name_width = min(max(160, _text_width(font, self.speaker) + 34), rect.width - 48)
        name_plate = pygame.Rect(rect.x + 22, rect.y - 13, name_width, 28)
        draw_dark_fantasy_panel(pygame, surface, name_plate, alpha=244, border_radius=6)
        speaker_surface = font.render(self.speaker, False, PANEL_GOLD)
        surface.blit(speaker_surface, (name_plate.x + 12, name_plate.y + 6))

        if self.mode == "choice" and self.choice is not None:
            self._draw_choice(pygame, surface, font, rect)
            return

        max_lines = 4
        for index, line in enumerate(wrap_text(self.current_text, font, rect.width - 56)):
            if index >= max_lines:
                break
            line_surface = font.render(line, False, TEXT_IVORY)
            surface.blit(line_surface, (rect.x + 28, rect.y + 52 + index * 23))

        hint = "Espaco/Enter/E para avancar" if self.current_index < len(self.messages) - 1 else "Espaco/Enter/E para fechar"
        hint_surface = font.render(hint, False, TEXT_MUTED)
        surface.blit(hint_surface, (rect.x + 28, rect.bottom - 28))

    def _draw_choice(self, pygame, surface, font, rect) -> None:
        question_lines = wrap_text(self.current_text, font, rect.width - 56)
        question = question_lines[0] if question_lines else ""
        question_surface = font.render(question, False, TEXT_IVORY)
        surface.blit(question_surface, (rect.x + 28, rect.y + 52))

        for index, option in enumerate(self.choice.options[:3] if self.choice else ()):
            selected = index == self.selected_option_index
            item_rect = pygame.Rect(rect.x + 28, rect.y + 78 + index * 24, rect.width - 56, 22)
            if selected:
                highlight = pygame.Surface((item_rect.width, item_rect.height), pygame.SRCALPHA)
                highlight.fill((PANEL_GOLD[0], PANEL_GOLD[1], PANEL_GOLD[2], 28))
                surface.blit(highlight, item_rect.topleft)
                pygame.draw.rect(surface, PANEL_GOLD, pygame.Rect(item_rect.x, item_rect.y + 3, 3, item_rect.height - 6))
            text_color = TEXT_IVORY if selected else TEXT_MUTED
            option_surface = font.render(option.text, False, text_color)
            surface.blit(option_surface, (item_rect.x + 14, item_rect.y + 3))

        hint_surface = font.render("Cima/baixo escolhe | Enter/E confirma", False, TEXT_MUTED)
        surface.blit(hint_surface, (rect.x + 28, rect.bottom - 28))


def dialogue_panel_rect(pygame, surface):
    screen_width = surface.get_width()
    screen_height = surface.get_height()
    margin_x = max(28, min(96, screen_width // 16))
    width = min(960, screen_width - margin_x * 2)
    height = min(max(148, screen_height // 5), 184)
    bottom_margin = max(28, min(60, screen_height // 18))
    rect = pygame.Rect(0, 0, width, height)
    rect.midbottom = (screen_width // 2, screen_height - bottom_margin)
    return rect


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
