"""Simple HUD for the overworld prototype."""

from __future__ import annotations

from dataclasses import dataclass

from src.game import colors


@dataclass(frozen=True)
class HUD:
    player_name: str
    map_name: str = "Mapa de Teste"
    controls_hint: str = "WASD/setas mover | E/espaco interagir | ESC sair"

    def draw(self, pygame, surface, font) -> None:
        panel = pygame.Rect(8, 8, 430, 54)
        pygame.draw.rect(surface, (12, 16, 28), panel)
        pygame.draw.rect(surface, colors.DIALOGUE_BORDER, panel, width=2)
        name_surface = font.render(f"{self.player_name} - {self.map_name}", False, colors.WHITE)
        hint_surface = font.render(self.controls_hint, False, colors.TEXT_MUTED)
        surface.blit(name_surface, (panel.x + 10, panel.y + 8))
        surface.blit(hint_surface, (panel.x + 10, panel.y + 30))
