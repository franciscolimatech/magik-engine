"""Main menu and simple character start flow for the 2D game."""

from __future__ import annotations

from src.core.character import Character, list_characters
from src.game import assets, colors
from src.game.game_context import GameContext
from src.game.scenes.base import BaseScene
from src.storage.types import JsonStore


SELECTED_OPTION_COLOR = (220, 177, 83)
OPTION_COLOR = (218, 210, 190)
OPTION_MUTED_COLOR = (156, 143, 116)
TEXT_SHADOW_COLOR = (0, 0, 0)
GLOBAL_BACKGROUND_OVERLAY_ALPHA = 38
MENU_BACKDROP_MAX_ALPHA = 165


class MainMenuScene(BaseScene):
    OPTIONS = ("Continuar", "Novo Jogo", "Carregar Personagem", "Ver Contexto", "Controles", "Sair")

    def __init__(
        self,
        pygame,
        context: GameContext,
        storage: JsonStore | None = None,
        *,
        title_background=None,
        load_title_background: bool = True,
    ) -> None:
        self.pygame = pygame
        self.context = context
        self.storage = storage
        self.title_background = (
            title_background
            if title_background is not None or not load_title_background
            else assets.load_optional_image(pygame, assets.TITLE_BACKGROUND_PATH)
        )
        self.selected_index = 0
        self.character_index = 0
        self.mode = "main"
        self.error_message = ""
        self.requested_scene: str | None = None
        self.should_quit = False
        self._font = None
        self._menu_font = None
        self._font_key: tuple[int, int] | None = None

    @property
    def selected_option(self) -> str:
        if self.mode == "characters":
            characters = self.available_characters()
            return characters[self.character_index].name if characters else "Nenhum personagem"
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
        elif self.mode == "controls":
            self._handle_panel_key(event.key)
        elif self.mode == "characters":
            self._handle_characters_key(event.key)
        else:
            self._handle_main_key(event.key)

    def update(self) -> None:
        return

    def draw(self, surface) -> None:
        self._ensure_fonts(surface.get_height())
        self._draw_background(surface)
        if self.mode == "context":
            self._draw_panel(surface, "Contexto", self.context_lines())
        elif self.mode == "controls":
            self._draw_panel(surface, "Controles", self.controls_lines())
        elif self.mode == "characters":
            self._draw_panel(surface, "Carregar Personagem", self.character_lines())
        else:
            self._draw_options(surface)

    def available_characters(self) -> list[Character]:
        if self.storage is None:
            return []
        try:
            return list_characters(self.storage)
        except ValueError:
            return []

    def character_lines(self) -> list[str]:
        characters = self.available_characters()
        if not characters:
            return ["Nenhum personagem encontrado.", "", "ESC para voltar"]
        lines = []
        for index, character in enumerate(characters[:8]):
            marker = "> " if index == self.character_index else "  "
            lines.append(f"{marker}{character.name} - {character.character_class}")
        lines.append("")
        lines.append("Enter/Espaco para escolher | ESC para voltar")
        return lines

    def context_lines(self) -> list[str]:
        status = "Com campanha ativa" if self.context.has_campaign_session else "Sem campanha ativa"
        return [
            f"Personagem: {self.context.player_name}",
            f"Character ID: {self.context.character_id}",
            f"Campaign ID: {self.context.campaign_id or '-'}",
            f"Session ID: {self.context.campaign_session_id or '-'}",
            f"Location ID: {self.context.location_id}",
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
            "Batalha: cima/baixo escolhe, Enter/E confirma",
            "ESC: voltar/sair",
            "",
            "ESC, Enter ou Espaco para voltar",
        ]

    def select_character(self, index: int) -> bool:
        characters = self.available_characters()
        if not characters:
            return False
        self.character_index = max(0, min(index, len(characters) - 1))
        character = characters[self.character_index]
        self.context = self.context.with_character(character.id, self.storage)
        self.requested_scene = "overworld"
        return True

    def _handle_main_key(self, key: int) -> None:
        keys = self.pygame
        if key == keys.K_ESCAPE:
            self.should_quit = True
        elif key in {keys.K_DOWN, keys.K_s}:
            self.selected_index = (self.selected_index + 1) % len(self.OPTIONS)
        elif key in {keys.K_UP, keys.K_w}:
            self.selected_index = (self.selected_index - 1) % len(self.OPTIONS)
        elif key in {keys.K_RETURN, keys.K_SPACE}:
            self._confirm_main_selection()

    def _confirm_main_selection(self) -> None:
        option = self.selected_option
        self.error_message = ""
        if option == "Continuar":
            self.requested_scene = "overworld"
        elif option == "Novo Jogo":
            self.requested_scene = "character_creator"
        elif option == "Carregar Personagem":
            self.mode = "characters"
            self.character_index = 0
        elif option == "Ver Contexto":
            self.mode = "context"
        elif option == "Controles":
            self.mode = "controls"
        elif option == "Sair":
            self.should_quit = True

    def _handle_characters_key(self, key: int) -> None:
        keys = self.pygame
        characters = self.available_characters()
        if key == keys.K_ESCAPE:
            self.mode = "main"
        elif key in {keys.K_DOWN, keys.K_s} and characters:
            self.character_index = (self.character_index + 1) % len(characters)
        elif key in {keys.K_UP, keys.K_w} and characters:
            self.character_index = (self.character_index - 1) % len(characters)
        elif key in {keys.K_RETURN, keys.K_SPACE}:
            self.select_character(self.character_index)

    def _handle_panel_key(self, key: int) -> None:
        keys = self.pygame
        if key in {keys.K_ESCAPE, keys.K_RETURN, keys.K_SPACE, keys.K_e}:
            self.mode = "main"

    def _ensure_fonts(self, screen_height: int = 480) -> None:
        menu_font_size = self._menu_font_size(screen_height)
        key = (screen_height, menu_font_size)
        if self._font is not None and self._font_key == key:
            return
        self._font_key = key
        self._font = self._make_font(_clamp(int(screen_height * 0.036), 24, 34))
        self._menu_font = self._make_font(menu_font_size)

    def _make_font(self, size: int):
        if hasattr(self.pygame.font, "SysFont"):
            return self.pygame.font.SysFont("georgia", size)
        return self.pygame.font.Font(None, size)

    def _menu_font_size(self, screen_height: int) -> int:
        return _clamp(int(screen_height * 0.052), 32, 58)

    def _menu_layout(self, screen_width: int, screen_height: int) -> dict[str, int]:
        font_size = self._menu_font_size(screen_height)
        gap = max(int(font_size * 1.25), 38)
        menu_height = (len(self.OPTIONS) - 1) * gap + font_size
        x = max(int(screen_width * 0.09), 48)
        preferred_y = int(screen_height * 0.585)
        bottom_margin = max(int(screen_height * 0.04), 22)
        max_y = max(int(screen_height * 0.28), screen_height - menu_height - bottom_margin)
        y = min(preferred_y, max_y)
        return {"x": x, "y": y, "gap": gap, "font_size": font_size, "height": menu_height}

    def _draw_background(self, surface) -> None:
        if self.title_background is None:
            surface.fill(colors.BLACK)
            return
        assets.draw_cover_background(self.pygame, surface, self.title_background)
        overlay = self.pygame.Surface((surface.get_width(), surface.get_height()), self.pygame.SRCALPHA)
        overlay.fill((0, 0, 0, GLOBAL_BACKGROUND_OVERLAY_ALPHA))
        surface.blit(overlay, (0, 0))

    def _draw_options(self, surface) -> None:
        layout = self._menu_layout(surface.get_width(), surface.get_height())
        self._draw_menu_backdrop(surface, layout)
        for index, option in enumerate(self.OPTIONS):
            selected = index == self.selected_index
            marker = "> " if selected else "  "
            label = f"{marker}{option.upper()}"
            color = SELECTED_OPTION_COLOR if selected else OPTION_COLOR
            y = layout["y"] + index * layout["gap"]
            self._draw_text_shadow(surface, self._menu_font, label, (layout["x"], y), color)

    def _draw_menu_backdrop(self, surface, layout: dict[str, int]) -> None:
        width = min(int(surface.get_width() * 0.42), 680)
        height = layout["height"] + max(28, layout["gap"] // 2)
        x = max(0, layout["x"] - int(surface.get_width() * 0.035))
        y = max(0, layout["y"] - layout["gap"] // 3)
        panel = self.pygame.Surface((width, height), self.pygame.SRCALPHA)
        for column in range(width):
            alpha = max(0, int(MENU_BACKDROP_MAX_ALPHA * (1 - column / max(1, width))))
            self.pygame.draw.line(panel, (0, 0, 0, alpha), (column, 0), (column, height))
        surface.blit(panel, (x, y))

    def _draw_panel(self, surface, title: str, lines: list[str]) -> None:
        rect = self.pygame.Rect(64, 138, surface.get_width() - 128, 300)
        self.pygame.draw.rect(surface, colors.DIALOGUE_BG, rect)
        self.pygame.draw.rect(surface, colors.DIALOGUE_BORDER, rect, width=2)
        title_surface = self._font.render(title, False, colors.WHITE)
        surface.blit(title_surface, (rect.x + 18, rect.y + 16))
        y = rect.y + 54
        for line in lines[:10]:
            color = colors.WHITE if line.startswith("> ") else colors.TEXT_MUTED
            text = self._font.render(line, False, color)
            surface.blit(text, (rect.x + 18, y))
            y += 24

    def _draw_text_shadow(self, surface, font, text: str, position: tuple[int, int], color: tuple[int, int, int]) -> None:
        x, y = position
        shadow = font.render(text, True, TEXT_SHADOW_COLOR)
        surface.blit(shadow, (x + 3, y + 3))
        rendered = font.render(text, True, color)
        surface.blit(rendered, (x, y))


def _clamp(value: int, minimum: int, maximum: int) -> int:
    return max(minimum, min(value, maximum))
