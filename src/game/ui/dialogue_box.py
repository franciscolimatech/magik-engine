"""Simple paginated retro dialogue box."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from src.game import colors
from src.game.dialogue import DialogueChoice, DialogueOption, normalize_messages
from src.game.settings import SCREEN_HEIGHT, SCREEN_WIDTH


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

        if self.mode == "choice" and self.choice is not None:
            self._draw_choice(pygame, surface, font, rect)
            return

        for index, line in enumerate(wrap_text(self.current_text, font, rect.width - 40)):
            if index >= 3:
                break
            line_surface = font.render(line, False, colors.WHITE)
            surface.blit(line_surface, (rect.x + 18, rect.y + 30 + index * 22))

        hint = "Espaco/Enter/E para avancar" if self.current_index < len(self.messages) - 1 else "Espaco/Enter/E para fechar"
        hint_surface = font.render(hint, False, colors.TEXT_MUTED)
        surface.blit(hint_surface, (rect.x + 18, rect.y + 84))

    def _draw_choice(self, pygame, surface, font, rect) -> None:
        question_lines = wrap_text(self.current_text, font, rect.width - 40)
        question = question_lines[0] if question_lines else ""
        question_surface = font.render(question, False, colors.WHITE)
        surface.blit(question_surface, (rect.x + 18, rect.y + 24))

        for index, option in enumerate(self.choice.options[:3] if self.choice else ()):
            selected = index == self.selected_option_index
            prefix = "> " if selected else "  "
            text_color = colors.WHITE if selected else colors.TEXT_MUTED
            option_surface = font.render(f"{prefix}{option.text}", False, text_color)
            surface.blit(option_surface, (rect.x + 28, rect.y + 48 + index * 18))

        hint_surface = font.render("Cima/baixo escolhe | Enter/E confirma", False, colors.TEXT_MUTED)
        surface.blit(hint_surface, (rect.x + 18, rect.y + 88))


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
