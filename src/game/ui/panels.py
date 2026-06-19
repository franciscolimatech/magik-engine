"""Small drawing helpers for dark fantasy UI panels."""

from __future__ import annotations


PANEL_BG = (12, 13, 24, 232)
PANEL_BORDER = (164, 128, 63)
PANEL_VIOLET_BORDER = (82, 63, 115)
PANEL_GOLD = (210, 169, 87)
TEXT_IVORY = (236, 226, 204)
TEXT_MUTED = (177, 169, 151)


def draw_dark_fantasy_panel(pygame, surface, rect, *, alpha: int = 232, border_radius: int = 8) -> None:
    panel = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    panel.fill((PANEL_BG[0], PANEL_BG[1], PANEL_BG[2], alpha))
    surface.blit(panel, rect.topleft)
    pygame.draw.rect(surface, PANEL_BORDER, rect, width=2, border_radius=border_radius)
    pygame.draw.rect(surface, PANEL_VIOLET_BORDER, rect.inflate(-10, -10), width=1, border_radius=max(2, border_radius - 2))


def draw_panel_separator(pygame, surface, start: tuple[int, int], end: tuple[int, int]) -> None:
    pygame.draw.line(surface, PANEL_VIOLET_BORDER, start, end, width=1)
