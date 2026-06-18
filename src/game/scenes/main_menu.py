"""Main menu and simple character start flow for the 2D game."""

from __future__ import annotations

from src.core.character import Character, list_characters
from src.game import assets, colors
from src.game.game_context import GameContext
from src.game.save import DEFAULT_SAVE_ID, sync_game_save_context
from src.game.scenes.base import BaseScene
from src.game.settings import (
    DISPLAY_MODES,
    choose_window_resolution,
    display_mode_label,
    get_game_display_mode,
    get_window_resolution,
    load_game_settings,
    normalize_display_mode,
    save_game_display_preferences,
)
from src.storage.types import JsonStore


SELECTED_OPTION_COLOR = (220, 177, 83)
OPTION_COLOR = (218, 210, 190)
OPTION_MUTED_COLOR = (156, 143, 116)
TEXT_SHADOW_COLOR = (0, 0, 0)
PANEL_BG_COLOR = (8, 9, 14, 198)
PANEL_BORDER_COLOR = (170, 138, 72, 120)
PANEL_DIVIDER_COLOR = (170, 138, 72, 64)
PANEL_LABEL_COLOR = (220, 177, 83)
PANEL_VALUE_COLOR = (232, 224, 207)
PANEL_FOOTER_COLOR = (166, 156, 135)
SELECT_FIELD_BG_COLOR = (13, 15, 22, 174)
SELECT_FIELD_HOVER_COLOR = (220, 177, 83, 28)
SELECT_FIELD_DISABLED_COLOR = (22, 23, 28, 120)
SELECT_FIELD_BORDER_COLOR = (170, 138, 72, 96)
SELECT_FIELD_DISABLED_BORDER_COLOR = (120, 112, 96, 54)
GLOBAL_BACKGROUND_OVERLAY_ALPHA = 38
MENU_BACKDROP_MAX_ALPHA = 165


class MainMenuScene(BaseScene):
    OPTIONS = ("Continuar", "Novo Jogo", "Carregar Personagem", "Controles", "Opcoes", "Sair")

    def __init__(
        self,
        pygame,
        context: GameContext,
        storage: JsonStore | None = None,
        *,
        title_background=None,
        load_title_background: bool = True,
        display_mode: str | None = None,
        window_resolution: tuple[int, int] | None = None,
        available_resolutions: list[tuple[int, int]] | None = None,
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
        self.display_mode = normalize_display_mode(display_mode or get_game_display_mode(storage=storage))
        self.display_mode_index = DISPLAY_MODES.index(self.display_mode)
        self.available_resolutions = list(available_resolutions or [(1280, 720)])
        self.window_resolution = choose_window_resolution(
            window_resolution or get_window_resolution(storage=storage),
            self.available_resolutions,
        )
        self.resolution_index = self.available_resolutions.index(self.window_resolution)
        self.settings_row_index = 0
        self.settings_dropdown_open: str | None = None
        self.resolution_dropdown_open = False
        self.error_message = ""
        self.requested_scene: str | None = None
        self.requested_display_mode: str | None = None
        self.requested_window_resolution: tuple[int, int] | None = None
        self.should_quit = False
        self._font = None
        self._menu_font = None
        self._small_font = None
        self._panel_title_font = None
        self._font_key: tuple[int, int] | None = None
        self._option_hitboxes = []
        self._panel_footer_hitbox = None
        self._character_hitboxes = []
        self._settings_hitboxes = []
        self._resolution_option_hitboxes = []
        self._mode_option_hitboxes = []

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

    def consume_requested_display_mode(self) -> str | None:
        requested = self.requested_display_mode
        self.requested_display_mode = None
        return requested

    def consume_requested_window_resolution(self) -> tuple[int, int] | None:
        requested = self.requested_window_resolution
        self.requested_window_resolution = None
        return requested

    def handle_event(self, event) -> None:
        if event.type == getattr(self.pygame, "MOUSEMOTION", None):
            if self.mode == "main":
                self._select_main_option_at(event.pos)
            elif self.mode == "characters":
                self._select_character_at(event.pos)
            elif self.mode == "settings":
                if not self._select_settings_dropdown_item_at(event.pos):
                    self._select_settings_item_at(event.pos)
            return
        if event.type == getattr(self.pygame, "MOUSEBUTTONDOWN", None):
            if self.mode == "main" and getattr(event, "button", None) == 1 and self._select_main_option_at(event.pos):
                self._confirm_main_selection()
            elif self.mode == "controls" and getattr(event, "button", None) == 1:
                self._click_panel_at(event.pos)
            elif self.mode == "characters" and getattr(event, "button", None) == 1:
                self._click_characters_at(event.pos)
            elif self.mode == "settings" and getattr(event, "button", None) == 1:
                self._click_settings_at(event.pos)
            return
        if event.type != self.pygame.KEYDOWN:
            return
        if self.mode == "controls":
            self._handle_panel_key(event.key)
        elif self.mode == "characters":
            self._handle_characters_key(event.key)
        elif self.mode == "settings":
            self._handle_settings_key(event.key)
        else:
            self._handle_main_key(event.key)

    def update(self) -> None:
        return

    def draw(self, surface) -> None:
        self._ensure_fonts(surface.get_height())
        self._draw_background(surface)
        if self.mode == "controls":
            self._draw_controls_panel(surface)
        elif self.mode == "characters":
            self._draw_characters_panel(surface)
        elif self.mode == "settings":
            self._draw_settings_panel(surface)
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

    def controls_items(self) -> list[tuple[str, str]]:
        return [
            ("Movimento", "WASD / Setas"),
            ("Interagir", "E / Espaco"),
            ("Avancar dialogo", "Enter / Espaco / E"),
            ("Escolher opcao", "Cima / Baixo"),
            ("Voltar ou sair", "ESC"),
        ]

    def display_settings_items(self, surface) -> list[tuple[str, str]]:
        selected_mode = DISPLAY_MODES[self.display_mode_index]
        selected_resolution = self.available_resolutions[self.resolution_index]
        saved = load_game_settings(self.storage) if self.storage is not None else None
        saved_resolution = (
            f"{saved['window_width']}x{saved['window_height']}" if saved is not None else self._resolution_label(self.window_resolution)
        )
        return [
            ("Modo de tela", display_mode_label(selected_mode)),
            ("Resolucao", self._resolution_label(selected_resolution)),
            ("Resolucao atual", f"{surface.get_width()}x{surface.get_height()}"),
            ("Preferencia salva", f"{display_mode_label(self.display_mode)} / {saved_resolution}"),
        ]

    def select_character(self, index: int) -> bool:
        characters = self.available_characters()
        if not characters:
            return False
        self.character_index = max(0, min(index, len(characters) - 1))
        character = characters[self.character_index]
        self.context = self.context.with_character(character.id, self.storage)
        self._sync_selected_character_save(character.id)
        self.requested_scene = "overworld"
        return True

    def _sync_selected_character_save(self, character_id: str) -> None:
        if self.storage is None:
            return
        try:
            sync_game_save_context(
                self.storage,
                save_id=DEFAULT_SAVE_ID,
                character_id=character_id,
                campaign_id=self.context.campaign_id,
                session_id=self.context.campaign_session_id,
                location_id=self.context.location_id,
            )
        except Exception as exc:  # noqa: BLE001 - menu selection must not crash if local save is unavailable.
            print(f"[MAGIK Game] Nao foi possivel atualizar o save do personagem selecionado: {exc}")

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
        elif option == "Controles":
            self.mode = "controls"
        elif option == "Opcoes":
            self.mode = "settings"
            self.display_mode_index = DISPLAY_MODES.index(self.display_mode)
        elif option == "Sair":
            self.should_quit = True

    def _select_main_option_at(self, position: tuple[int, int]) -> bool:
        for index, rect in self._option_hitboxes:
            if rect.collidepoint(position):
                self.selected_index = index
                return True
        return False

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

    def _handle_settings_key(self, key: int) -> None:
        keys = self.pygame
        if key == keys.K_ESCAPE:
            if self.settings_dropdown_open is not None:
                self._close_settings_dropdown()
                return
            self._reset_pending_display_preferences()
            self.mode = "main"
        elif self.settings_dropdown_open is not None:
            self._handle_settings_dropdown_key(key)
        elif key in {keys.K_UP, keys.K_w}:
            self.settings_row_index = (self.settings_row_index - 1) % 4
            self._close_settings_dropdown()
        elif key in {keys.K_DOWN, keys.K_s}:
            self.settings_row_index = (self.settings_row_index + 1) % 4
            self._close_settings_dropdown()
        elif key in {keys.K_LEFT, keys.K_a}:
            self._change_selected_settings_value(-1)
        elif key in {keys.K_RIGHT, keys.K_d}:
            self._change_selected_settings_value(1)
        elif key in {keys.K_RETURN, keys.K_SPACE, keys.K_e}:
            self._confirm_settings_row()

    def _handle_settings_dropdown_key(self, key: int) -> None:
        keys = self.pygame
        if key in {keys.K_UP, keys.K_w, keys.K_LEFT, keys.K_a}:
            self._move_settings_dropdown_selection(-1)
        elif key in {keys.K_DOWN, keys.K_s, keys.K_RIGHT, keys.K_d}:
            self._move_settings_dropdown_selection(1)
        elif key in {keys.K_RETURN, keys.K_SPACE, keys.K_e}:
            self._close_settings_dropdown()

    def _change_selected_settings_value(self, delta: int) -> None:
        if self.settings_row_index == 0:
            self.display_mode_index = (self.display_mode_index - 1) % len(DISPLAY_MODES)
            if delta > 0:
                self.display_mode_index = (self.display_mode_index + 2) % len(DISPLAY_MODES)
        elif self.settings_row_index == 1 and self._resolution_select_enabled():
            self.resolution_index = (self.resolution_index + delta) % len(self.available_resolutions)

    def _confirm_settings_row(self) -> None:
        if self.settings_row_index == 0:
            self._toggle_settings_dropdown("mode")
        elif self.settings_row_index == 1 and self._resolution_select_enabled():
            self._toggle_settings_dropdown("resolution")
        elif self.settings_row_index == 2:
            self.apply_display_mode_selection()
        elif self.settings_row_index == 3:
            self._reset_pending_display_preferences()
            self.mode = "main"

    def apply_display_mode_selection(self) -> str:
        selected_mode = DISPLAY_MODES[self.display_mode_index]
        selected_resolution = self.available_resolutions[self.resolution_index]
        self.display_mode = selected_mode
        self.window_resolution = selected_resolution
        if self.storage is not None:
            try:
                settings = save_game_display_preferences(self.storage, selected_mode, selected_resolution)
                self.display_mode = settings["display_mode"]
                self.window_resolution = (settings["window_width"], settings["window_height"])
            except Exception as exc:  # noqa: BLE001 - display preference must not crash the menu.
                print(f"[MAGIK Game] Nao foi possivel salvar configuracao de tela: {exc}")
        self.display_mode_index = DISPLAY_MODES.index(self.display_mode)
        self.resolution_index = self.available_resolutions.index(
            choose_window_resolution(self.window_resolution, self.available_resolutions)
        )
        self.requested_display_mode = self.display_mode
        self.requested_window_resolution = self.window_resolution
        self._close_settings_dropdown()
        return self.display_mode

    def _reset_pending_display_preferences(self) -> None:
        self.display_mode_index = DISPLAY_MODES.index(self.display_mode)
        self.resolution_index = self.available_resolutions.index(
            choose_window_resolution(self.window_resolution, self.available_resolutions)
        )
        self._close_settings_dropdown()

    def _ensure_fonts(self, screen_height: int = 480) -> None:
        menu_font_size = self._menu_font_size(screen_height)
        key = (screen_height, menu_font_size)
        if self._font is not None and self._font_key == key:
            return
        self._font_key = key
        self._font = self._make_font(_clamp(int(screen_height * 0.036), 24, 34))
        self._menu_font = self._make_font(menu_font_size)
        self._small_font = self._make_font(_clamp(int(screen_height * 0.028), 18, 24))
        self._panel_title_font = self._make_font(_clamp(int(screen_height * 0.052), 30, 46))

    def _make_font(self, size: int):
        if hasattr(self.pygame.font, "SysFont"):
            return self.pygame.font.SysFont("georgia", size)
        return self.pygame.font.Font(None, size)

    def _menu_font_size(self, screen_height: int) -> int:
        return _clamp(int(screen_height * 0.052), 32, 58)

    def _menu_layout(self, screen_width: int, screen_height: int) -> dict[str, int]:
        font_size = self._menu_font_size(screen_height)
        gap = max(int(font_size * 1.0), 38)
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
        self._option_hitboxes = []
        for index, option in enumerate(self.OPTIONS):
            selected = index == self.selected_index
            marker = "> " if selected else "  "
            label = f"{marker}{option.upper()}"
            color = SELECTED_OPTION_COLOR if selected else OPTION_COLOR
            y = layout["y"] + index * layout["gap"]
            rect = self._draw_text_shadow(surface, self._menu_font, label, (layout["x"], y), color)
            self._option_hitboxes.append((index, rect.inflate(18, 12)))

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

    def _secondary_panel_rect(self, surface):
        width = _clamp(int(surface.get_width() * 0.52), 520, 780)
        height = _clamp(int(surface.get_height() * 0.58), 330, 470)
        x = max(42, int(surface.get_width() * 0.08))
        y = max(54, (surface.get_height() - height) // 2)
        return self.pygame.Rect(x, y, width, height)

    def _draw_panel_frame(self, surface, title: str):
        rect = self._secondary_panel_rect(surface)
        panel = self.pygame.Surface((rect.width, rect.height), self.pygame.SRCALPHA)
        panel.fill(PANEL_BG_COLOR)
        surface.blit(panel, (rect.x, rect.y))
        self.pygame.draw.rect(surface, PANEL_BORDER_COLOR, rect, width=1)
        self.pygame.draw.line(
            surface,
            PANEL_DIVIDER_COLOR,
            (rect.x + 28, rect.y + 74),
            (rect.right - 28, rect.y + 74),
            width=1,
        )
        title_surface = self._panel_title_font.render(title, True, PANEL_VALUE_COLOR)
        surface.blit(title_surface, (rect.x + 28, rect.y + 24))
        return rect

    def _draw_panel_footer(self, surface, rect, text: str = "ESC, Enter ou Espaco para voltar") -> None:
        rendered = self._small_font.render(text, True, PANEL_FOOTER_COLOR)
        position = (rect.x + 28, rect.bottom - 38)
        surface.blit(rendered, position)
        self._panel_footer_hitbox = rendered.get_rect(topleft=position).inflate(18, 14)

    def _draw_labeled_rows(self, surface, rect, rows: list[tuple[str, str]], start_y: int | None = None) -> None:
        y = start_y if start_y is not None else rect.y + 104
        label_x = rect.x + 34
        value_x = rect.x + max(210, int(rect.width * 0.35))
        row_gap = max(34, int(rect.height * 0.084))
        for label, value in rows:
            label_surface = self._small_font.render(label.upper(), True, PANEL_LABEL_COLOR)
            value_surface = self._font.render(value, True, PANEL_VALUE_COLOR)
            surface.blit(label_surface, (label_x, y + 4))
            surface.blit(value_surface, (value_x, y))
            y += row_gap

    def _draw_controls_panel(self, surface) -> None:
        rect = self._draw_panel_frame(surface, "Controles")
        self._draw_labeled_rows(surface, rect, self.controls_items())
        self._draw_panel_footer(surface, rect)

    def _draw_settings_panel(self, surface) -> None:
        rect = self._draw_panel_frame(surface, "Opcoes")
        self._settings_hitboxes = []
        self._resolution_option_hitboxes = []
        self._mode_option_hitboxes = []
        row_gap = 54
        rows = self._settings_rows()
        y = rect.y + 100
        for index, row in enumerate(rows):
            selected = index == self.settings_row_index
            enabled = bool(row["enabled"])
            row_rect = self.pygame.Rect(rect.x + 28, y - 8, rect.width - 56, 44)
            self._settings_hitboxes.append((index, row_rect))
            if selected:
                self.pygame.draw.rect(surface, SELECT_FIELD_HOVER_COLOR, row_rect)
            label_color = SELECTED_OPTION_COLOR if selected and enabled else (PANEL_LABEL_COLOR if enabled else OPTION_MUTED_COLOR)
            label_surface = self._small_font.render(str(row["label"]).upper(), True, label_color)
            surface.blit(label_surface, (rect.x + 34, y + 7))
            if row["kind"] in {"mode", "resolution"}:
                self._draw_select_field(
                    surface,
                    self.pygame.Rect(rect.x + 252, y - 4, rect.width - 312, 38),
                    str(row["value"]),
                    enabled=enabled,
                    open=self.settings_dropdown_open == row["kind"],
                )
            else:
                button_color = SELECTED_OPTION_COLOR if selected else PANEL_VALUE_COLOR
                button_surface = self._font.render(str(row["value"]), True, button_color)
                surface.blit(button_surface, (rect.x + 260, y + 2))
            y += row_gap
        self._draw_active_settings_dropdown(surface, rect)
        self._draw_panel_footer(surface, rect, "Setas/WASD navegam | Enter abre/seleciona | ESC volta | Mouse seleciona")

    def _draw_characters_panel(self, surface) -> None:
        rect = self._draw_panel_frame(surface, "Carregar Personagem")
        characters = self.available_characters()
        if not characters:
            message = self._font.render("Nenhum personagem encontrado.", True, PANEL_VALUE_COLOR)
            surface.blit(message, (rect.x + 34, rect.y + 112))
            self._draw_panel_footer(surface, rect, "ESC para voltar")
            return

        list_x = rect.x + 34
        list_y = rect.y + 104
        list_gap = max(32, int(rect.height * 0.078))
        self._character_hitboxes = []
        for index, character in enumerate(characters[:8]):
            selected = index == self.character_index
            name = character.name.upper() if selected else character.name
            marker = "> " if selected else "  "
            color = SELECTED_OPTION_COLOR if selected else OPTION_COLOR
            rendered = self._font.render(f"{marker}{name}", True, color)
            position = (list_x, list_y + index * list_gap)
            surface.blit(rendered, position)
            self._character_hitboxes.append((index, rendered.get_rect(topleft=position).inflate(18, 10)))

        selected = characters[max(0, min(self.character_index, len(characters) - 1))]
        summary_x = rect.x + int(rect.width * 0.53)
        summary_y = rect.y + 106
        self.pygame.draw.line(
            surface,
            PANEL_DIVIDER_COLOR,
            (summary_x - 24, rect.y + 96),
            (summary_x - 24, rect.bottom - 64),
            width=1,
        )
        summary_rows = [
            ("Nome", selected.name),
            ("ID", selected.id),
            ("Classe", selected.character_class),
            ("Origem", selected.origin_location_id or "-"),
        ]
        self._draw_labeled_rows(surface, self.pygame.Rect(summary_x, summary_y, rect.right - summary_x - 28, 180), summary_rows, summary_y)
        self._draw_panel_footer(surface, rect, "Enter/Espaco para escolher | ESC para voltar")

    def _draw_select_field(self, surface, field_rect, value: str, *, enabled: bool, open: bool) -> None:
        fill = SELECT_FIELD_BG_COLOR if enabled else SELECT_FIELD_DISABLED_COLOR
        border = SELECTED_OPTION_COLOR if open and enabled else (SELECT_FIELD_BORDER_COLOR if enabled else SELECT_FIELD_DISABLED_BORDER_COLOR)
        self.pygame.draw.rect(surface, fill, field_rect)
        self.pygame.draw.rect(surface, border, field_rect, width=1)
        value_color = PANEL_VALUE_COLOR if enabled else OPTION_MUTED_COLOR
        rendered = self._font.render(value, True, value_color)
        surface.blit(rendered, (field_rect.x + 14, field_rect.y + 7))
        indicator = "v" if not open else "^"
        indicator_surface = self._small_font.render(indicator if enabled else "-", True, SELECTED_OPTION_COLOR if enabled else OPTION_MUTED_COLOR)
        surface.blit(indicator_surface, (field_rect.right - 24, field_rect.y + 10))

    def _draw_active_settings_dropdown(self, surface, rect) -> None:
        if self.settings_dropdown_open == "mode":
            self._draw_settings_dropdown(
                surface,
                rect,
                row_index=0,
                items=[(index, self._display_mode_menu_label(mode)) for index, mode in enumerate(DISPLAY_MODES)],
                selected_index=self.display_mode_index,
                target="mode",
            )
        elif self.settings_dropdown_open == "resolution" and self._resolution_select_enabled():
            self._draw_settings_dropdown(
                surface,
                rect,
                row_index=1,
                items=[(index, self._resolution_label(self.available_resolutions[index])) for index in self._resolution_dropdown_indices()],
                selected_index=self.resolution_index,
                target="resolution",
            )

    def _draw_settings_dropdown(
        self,
        surface,
        rect,
        *,
        row_index: int,
        items: list[tuple[int, str]],
        selected_index: int,
        target: str,
    ) -> None:
        if not items:
            return
        width = max(260, rect.width - 312)
        x = rect.x + 252
        y = rect.y + 100 + row_index * 54 + 38
        visible = items[:8]
        dropdown = self.pygame.Rect(x, y, width, 32 * len(visible) + 12)
        panel = self.pygame.Surface((dropdown.width, dropdown.height), self.pygame.SRCALPHA)
        panel.fill((8, 9, 14, 232))
        surface.blit(panel, (dropdown.x, dropdown.y))
        self.pygame.draw.rect(surface, PANEL_BORDER_COLOR, dropdown, width=1)
        for position, (item_index, label) in enumerate(visible):
            option_y = dropdown.y + 8 + position * 32
            option_rect = self.pygame.Rect(dropdown.x + 8, option_y - 3, dropdown.width - 16, 28)
            if target == "mode":
                self._mode_option_hitboxes.append((item_index, option_rect))
            else:
                self._resolution_option_hitboxes.append((item_index, option_rect))
            selected = item_index == selected_index
            if selected:
                self.pygame.draw.rect(surface, (220, 177, 83, 34), option_rect)
            color = SELECTED_OPTION_COLOR if selected else PANEL_VALUE_COLOR
            rendered = self._small_font.render(label, True, color)
            surface.blit(rendered, (option_rect.x + 8, option_rect.y + 4))

    def _click_panel_at(self, position: tuple[int, int]) -> bool:
        if self._panel_footer_hitbox is not None and self._panel_footer_hitbox.collidepoint(position):
            self.mode = "main"
            return True
        return False

    def _select_character_at(self, position: tuple[int, int]) -> bool:
        for index, rect in self._character_hitboxes:
            if rect.collidepoint(position):
                self.character_index = index
                return True
        return False

    def _click_characters_at(self, position: tuple[int, int]) -> bool:
        if self._select_character_at(position):
            self.select_character(self.character_index)
            return True
        return self._click_panel_at(position)

    def _select_settings_item_at(self, position: tuple[int, int]) -> bool:
        for index, rect in self._settings_hitboxes:
            if rect.collidepoint(position):
                self.settings_row_index = index
                return True
        return False

    def _click_settings_at(self, position: tuple[int, int]) -> bool:
        if self.settings_dropdown_open is not None:
            if self._select_settings_dropdown_item_at(position):
                self._close_settings_dropdown()
                return True
            self._close_settings_dropdown()
            return True
        if self._select_settings_item_at(position):
            if self.settings_row_index == 0:
                self._toggle_settings_dropdown("mode")
            elif self.settings_row_index == 1:
                if self._resolution_select_enabled():
                    self._toggle_settings_dropdown("resolution")
            elif self.settings_row_index == 2:
                self.apply_display_mode_selection()
            elif self.settings_row_index == 3:
                self._reset_pending_display_preferences()
                self.mode = "main"
            return True
        return self._click_panel_at(position)

    def _select_settings_dropdown_item_at(self, position: tuple[int, int]) -> bool:
        if self.settings_dropdown_open == "mode":
            for index, rect in self._mode_option_hitboxes:
                if rect.collidepoint(position):
                    self.display_mode_index = index
                    self.settings_row_index = 0
                    return True
        if self.settings_dropdown_open == "resolution":
            for index, rect in self._resolution_option_hitboxes:
                if rect.collidepoint(position):
                    self.resolution_index = index
                    self.settings_row_index = 1
                    return True
        return False

    def _toggle_settings_dropdown(self, dropdown: str) -> None:
        if dropdown == "resolution" and not self._resolution_select_enabled():
            self._close_settings_dropdown()
            return
        if self.settings_dropdown_open == dropdown:
            self._close_settings_dropdown()
            return
        self.settings_dropdown_open = dropdown
        self.resolution_dropdown_open = dropdown == "resolution"

    def _close_settings_dropdown(self) -> None:
        self.settings_dropdown_open = None
        self.resolution_dropdown_open = False

    def _move_settings_dropdown_selection(self, delta: int) -> None:
        if self.settings_dropdown_open == "mode":
            self.display_mode_index = (self.display_mode_index + delta) % len(DISPLAY_MODES)
        elif self.settings_dropdown_open == "resolution" and self._resolution_select_enabled():
            indices = self._resolution_dropdown_indices()
            current_position = indices.index(self.resolution_index) if self.resolution_index in indices else 0
            self.resolution_index = indices[(current_position + delta) % len(indices)]

    def _settings_rows(self) -> list[dict[str, object]]:
        resolution_enabled = self._resolution_select_enabled()
        resolution_value = (
            self._resolution_label(self.available_resolutions[self.resolution_index])
            if resolution_enabled
            else "Usa resolucao nativa do monitor"
        )
        return [
            {
                "kind": "mode",
                "label": "Modo de tela",
                "value": self._display_mode_menu_label(DISPLAY_MODES[self.display_mode_index]),
                "enabled": True,
            },
            {"kind": "resolution", "label": "Resolucao", "value": resolution_value, "enabled": resolution_enabled},
            {"kind": "apply", "label": "Aplicar", "value": "Aplicar alteracoes", "enabled": True},
            {"kind": "back", "label": "Voltar", "value": "Voltar ao menu", "enabled": True},
        ]

    def _display_mode_menu_label(self, display_mode: str) -> str:
        normalized = DISPLAY_MODES[DISPLAY_MODES.index(display_mode)] if display_mode in DISPLAY_MODES else DISPLAY_MODES[0]
        if normalized == "borderless":
            return "Sem borda"
        return display_mode_label(normalized)

    def _resolution_select_enabled(self) -> bool:
        return DISPLAY_MODES[self.display_mode_index] != "borderless"

    def _resolution_dropdown_indices(self) -> list[int]:
        return sorted(range(len(self.available_resolutions)), key=lambda index: self.available_resolutions[index][0] * self.available_resolutions[index][1], reverse=True)

    def _resolution_label(self, resolution: tuple[int, int]) -> str:
        return f"{resolution[0]}x{resolution[1]}"

    def _draw_text_shadow(self, surface, font, text: str, position: tuple[int, int], color: tuple[int, int, int]):
        x, y = position
        shadow = font.render(text, True, TEXT_SHADOW_COLOR)
        surface.blit(shadow, (x + 3, y + 3))
        rendered = font.render(text, True, color)
        surface.blit(rendered, (x, y))
        return rendered.get_rect(topleft=(x, y))


def _clamp(value: int, minimum: int, maximum: int) -> int:
    return max(minimum, min(value, maximum))
