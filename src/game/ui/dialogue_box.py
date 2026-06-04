"""Simple retro dialogue box."""

from __future__ import annotations

from dataclasses import dataclass

from src.game import colors
from src.game.settings import SCREEN_HEIGHT, SCREEN_WIDTH


@dataclass
class DialogueBox:
    speaker: str
    text: str
    visible: bool = True

    def close(self) -> None:
        self.visible = False

    def draw(self, pygame, surface, font) -> None:
        if not self.visible:
            return
        rect = pygame.Rect(24, SCREEN_HEIGHT - 128, SCREEN_WIDTH - 48, 104)
        inner = rect.inflate(-10, -10)
        pygame.draw.rect(surface, colors.DIALOGUE_BG, rect)
        pygame.draw.rect(surface, colors.DIALOGUE_BORDER, rect, width=3)
        pygame.draw.rect(surface, colors.WHITE, inner, width=1)
        name_plate = pygame.Rect(rect.x + 14, rect.y - 10, 130, 22)
        pygame.draw.rect(surface, colors.DIALOGUE_BG, name_plate)
        pygame.draw.rect(surface, colors.DIALOGUE_BORDER, name_plate, width=2)
        speaker_surface = font.render(self.speaker, False, colors.WHITE)
        text_surface = font.render(self.text, False, colors.WHITE)
        hint_surface = font.render("Espaco/Enter para fechar", False, colors.TEXT_MUTED)
        surface.blit(speaker_surface, (name_plate.x + 8, name_plate.y + 3))
        surface.blit(text_surface, (rect.x + 18, rect.y + 34))
        surface.blit(hint_surface, (rect.x + 18, rect.y + 72))
