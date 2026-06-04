"""Main menu scene for the experimental 2D game."""

from __future__ import annotations

from src.game import colors
from src.game.game_context import GameContext
from src.game.scenes.base import BaseScene


class MainMenuScene(BaseScene):
    OPTIONS = ("Iniciar jogo", "Ver contexto", "Controles", "Sair")

    def __init__(self, pygame, context: GameContext) -> None:
        self.pygame = pygame
        self.context = context
        self.selected_index = 0
        self.mode = "main"
        self.requested_scene: str | None = None
        self.should_quit = False
        self._title_font = None
        self._subtitle_font = None
        self._font = None

    @property
    def selected_option(self) -> str:
        return self.OPTIONS[self.selected_index]

    def consume_requested_scene(self) -> str | None:
        requested = self.requested_scene
        self.requested_scene = None
        return requested

    def handle_event(self, event) -> None:
        if event.type != self.pygame.KEYDOWN:
            return
        if self.mode == "context":
            self._handle_panel_key(event.key)
            return
        if self.mode == "controls":
            self._handle_panel_key(event.key)
            return
        self._handle_main_key(event.key)

    def update(self) -> None:
        return

    def draw(self, surface) -> None:
        self._ensure_fonts()
        surface.fill(colors.BLACK)
        self._draw_title(surface)
        if self.mode == "context":
            self._draw_panel(surface, "Contexto", self.context_lines())
        elif self.mode == "controls":
            self._draw_panel(surface, "Controles", self.controls_lines())
        else:
            self._draw_options(surface)

    def context_lines(self) -> list[str]:
        status = "Com campanha ativa" if self.context.has_campaign_session else "Sem campanha ativa"
        return [
            f"Personagem: {self.context.player_name}",
            f"Character ID: {self.context.character_id}",
            f"Campaign ID: {self.context.campaign_id or '-'}",
            f"Session ID: {self.context.campaign_session_id or '-'}",
            f"Mapa inicial: {self.context.map_name}",
            f"Status: {status}",
            "",
            "ESC, Enter ou Espaco para voltar",
        ]

    def controls_lines(self) -> list[str]:
        return [
            "WASD/setas: mover",
            "E/Espaco: interagir",
            "Enter/Espaco/E: avancar dialogo",
            "ESC: voltar/sair",
            "",
            "ESC, Enter ou Espaco para voltar",
        ]

    def _handle_main_key(self, key: int) -> None:
        keys = self.pygame
        if key in {keys.K_ESCAPE}:
            self.should_quit = True
        elif key in {keys.K_DOWN, keys.K_s}:
            self.selected_index = (self.selected_index + 1) % len(self.OPTIONS)
        elif key in {keys.K_UP, keys.K_w}:
            self.selected_index = (self.selected_index - 1) % len(self.OPTIONS)
        elif key in {keys.K_RETURN, keys.K_SPACE}:
            self._confirm_selection()

    def _handle_panel_key(self, key: int) -> None:
        keys = self.pygame
        if key in {keys.K_ESCAPE, keys.K_RETURN, keys.K_SPACE, keys.K_e}:
            self.mode = "main"

    def _confirm_selection(self) -> None:
        option = self.selected_option
        if option == "Iniciar jogo":
            self.requested_scene = "overworld"
        elif option == "Ver contexto":
            self.mode = "context"
        elif option == "Controles":
            self.mode = "controls"
        elif option == "Sair":
            self.should_quit = True

    def _ensure_fonts(self) -> None:
        if self._font is not None:
            return
        self._title_font = self.pygame.font.Font(None, 58)
        self._subtitle_font = self.pygame.font.Font(None, 30)
        self._font = self.pygame.font.Font(None, 28)

    def _draw_title(self, surface) -> None:
        self._draw_centered(surface, self._title_font, "MAGIK Engine", 70, colors.WHITE)
        self._draw_centered(surface, self._subtitle_font, "RPG 2D Experimental", 118, colors.TEXT_MUTED)

    def _draw_options(self, surface) -> None:
        box_width = 320
        box_height = 42
        start_y = 178
        screen_width = surface.get_width()
        for index, option in enumerate(self.OPTIONS):
            x = (screen_width - box_width) // 2
            y = start_y + index * 54
            rect = self.pygame.Rect(x, y, box_width, box_height)
            selected = index == self.selected_index
            bg = (39, 48, 76) if selected else colors.DIALOGUE_BG
            border = colors.DIALOGUE_BORDER if selected else (68, 78, 112)
            text_color = colors.WHITE if selected else colors.TEXT_MUTED
            self.pygame.draw.rect(surface, bg, rect)
            self.pygame.draw.rect(surface, border, rect, width=2)
            prefix = "> " if selected else "  "
            label = self._font.render(f"{prefix}{option}", False, text_color)
            surface.blit(label, (rect.x + 18, rect.y + 10))

    def _draw_panel(self, surface, title: str, lines: list[str]) -> None:
        rect = self.pygame.Rect(82, 160, surface.get_width() - 164, 250)
        self.pygame.draw.rect(surface, colors.DIALOGUE_BG, rect)
        self.pygame.draw.rect(surface, colors.DIALOGUE_BORDER, rect, width=2)
        title_surface = self._font.render(title, False, colors.WHITE)
        surface.blit(title_surface, (rect.x + 18, rect.y + 16))
        y = rect.y + 54
        for line in lines:
            text = self._font.render(line, False, colors.TEXT_MUTED)
            surface.blit(text, (rect.x + 18, y))
            y += 26

    def _draw_centered(self, surface, font, text: str, y: int, color: tuple[int, int, int]) -> None:
        rendered = font.render(text, False, color)
        x = (surface.get_width() - rendered.get_width()) // 2
        surface.blit(rendered, (x, y))
