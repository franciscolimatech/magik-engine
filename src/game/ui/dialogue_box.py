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
        pygame.draw.rect(surface, colors.DIALOGUE_BG, rect)
        pygame.draw.rect(surface, colors.DIALOGUE_BORDER, rect, width=3)
        speaker_surface = font.render(self.speaker, False, colors.WHITE)
        text_surface = font.render(self.text, False, colors.WHITE)
        hint_surface = font.render("Espaco/E/Enter: fechar", False, colors.TEXT_MUTED)
        surface.blit(speaker_surface, (rect.x + 16, rect.y + 14))
        surface.blit(text_surface, (rect.x + 16, rect.y + 44))
        surface.blit(hint_surface, (rect.x + 16, rect.y + 74))
