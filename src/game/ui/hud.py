"""Simple HUD for the overworld prototype."""

from __future__ import annotations

from dataclasses import dataclass

from src.game import colors


@dataclass(frozen=True)
class HUD:
    player_name: str
    map_name: str = "Mapa de Teste"
    campaign_label: str = "Sem campanha ativa"
    session_label: str = ""
    controls_hint: str = "WASD/setas mover | E/espaco interagir | ESC sair"

    def draw(self, pygame, surface, font) -> None:
        panel = pygame.Rect(8, 8, 470, 86)
        inner = panel.inflate(-8, -8)
        pygame.draw.rect(surface, (12, 16, 28), panel)
        pygame.draw.rect(surface, colors.DIALOGUE_BORDER, panel, width=2)
        pygame.draw.rect(surface, (39, 48, 76), inner, width=1)
        name_surface = font.render(f"{self.player_name} - {self.map_name}", False, colors.WHITE)
        campaign_surface = font.render(self._campaign_text(), False, colors.TEXT_MUTED)
        hint_surface = font.render(self.controls_hint, False, colors.TEXT_MUTED)
        surface.blit(name_surface, (panel.x + 10, panel.y + 8))
        surface.blit(campaign_surface, (panel.x + 10, panel.y + 30))
        surface.blit(hint_surface, (panel.x + 10, panel.y + 56))

    def _campaign_text(self) -> str:
        if not self.session_label:
            return self.campaign_label
        return f"{self.campaign_label} | {self.session_label}"
