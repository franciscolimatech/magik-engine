"""Main menu and simple character start flow for the 2D game."""

from __future__ import annotations

from src.core.character import Character, create_character, list_characters
from src.game import colors
from src.game.game_context import GameContext
from src.game.scenes.base import BaseScene
from src.storage.types import JsonStore


CLASS_OPTIONS = ("Sombrio", "Guerreiro", "Mago", "Cacador", "Curandeiro", "Inventor")
NEW_CHARACTER_HEALTH = 25
NEW_CHARACTER_ARMOR = 0
ALLOWED_NAME_CHARS = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 -_")


class MainMenuScene(BaseScene):
    OPTIONS = ("Continuar", "Novo Jogo", "Carregar Personagem", "Ver Contexto", "Controles", "Sair")

    def __init__(self, pygame, context: GameContext, storage: JsonStore | None = None) -> None:
        self.pygame = pygame
        self.context = context
        self.storage = storage
        self.selected_index = 0
        self.character_index = 0
        self.class_index = 0
        self.confirm_index = 0
        self.mode = "main"
        self.new_character_name = ""
        self.error_message = ""
        self.requested_scene: str | None = None
        self.should_quit = False
        self._title_font = None
        self._subtitle_font = None
        self._font = None

    @property
    def selected_option(self) -> str:
        if self.mode == "characters":
            characters = self.available_characters()
            return characters[self.character_index].name if characters else "Nenhum personagem"
        if self.mode == "class":
            return CLASS_OPTIONS[self.class_index]
        if self.mode == "confirm":
            return ("Confirmar e comecar", "Voltar")[self.confirm_index]
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
        elif self.mode == "name":
            self._handle_name_key(event)
        elif self.mode == "class":
            self._handle_class_key(event.key)
        elif self.mode == "confirm":
            self._handle_confirm_key(event.key)
        else:
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
        elif self.mode == "characters":
            self._draw_panel(surface, "Carregar Personagem", self.character_lines())
        elif self.mode == "name":
            self._draw_panel(surface, "Novo Jogo", self.name_lines())
        elif self.mode == "class":
            self._draw_panel(surface, "Escolha a Classe", self.class_lines())
        elif self.mode == "confirm":
            self._draw_panel(surface, "Confirmar Personagem", self.confirm_lines())
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

    def name_lines(self) -> list[str]:
        lines = [
            "Digite o nome do personagem:",
            self.new_character_name or "_",
            "",
            "Letras, numeros, espaco, hifen e underline.",
            "Enter confirma | Backspace apaga | ESC volta",
        ]
        if self.error_message:
            lines.insert(3, self.error_message)
        return lines

    def class_lines(self) -> list[str]:
        lines = []
        for index, class_name in enumerate(CLASS_OPTIONS):
            marker = "> " if index == self.class_index else "  "
            lines.append(f"{marker}{class_name}")
        lines.append("")
        lines.append("Enter/Espaco confirma | ESC volta")
        return lines

    def confirm_lines(self) -> list[str]:
        tags = "player-created"
        lines = [
            f"Nome: {self.new_character_name}",
            f"Classe: {CLASS_OPTIONS[self.class_index]}",
            f"Vida: {NEW_CHARACTER_HEALTH}/{NEW_CHARACTER_HEALTH}",
            f"Armadura: {NEW_CHARACTER_ARMOR}",
            f"Tags: {tags}",
            "",
        ]
        for index, option in enumerate(("Confirmar e comecar", "Voltar")):
            marker = "> " if index == self.confirm_index else "  "
            lines.append(f"{marker}{option}")
        if self.error_message:
            lines.append(self.error_message)
        return lines

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

    def create_new_character(self) -> Character:
        if self.storage is None:
            raise ValueError("Armazenamento indisponivel para criar personagem.")
        name = self.new_character_name.strip()
        if not name:
            raise ValueError("Nome do personagem e obrigatorio.")
        character = create_character(
            self.storage,
            name=name,
            character_class=CLASS_OPTIONS[self.class_index],
            max_health=NEW_CHARACTER_HEALTH,
            armor=NEW_CHARACTER_ARMOR,
            equipment=[],
            notes=["Criado pelo jogo 2D"],
            tags=["player-created"],
        )
        self.context = self.context.with_character(character.id, self.storage)
        self.requested_scene = "overworld"
        return character

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
            self.mode = "name"
            self.new_character_name = ""
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

    def _handle_name_key(self, event) -> None:
        key = event.key
        keys = self.pygame
        self.error_message = ""
        if key == keys.K_ESCAPE:
            self.mode = "main"
            return
        if key == keys.K_BACKSPACE:
            self.new_character_name = self.new_character_name[:-1]
            return
        if key == keys.K_RETURN:
            if not self.new_character_name.strip():
                self.error_message = "Nome do personagem e obrigatorio."
                return
            self.mode = "class"
            return
        text = getattr(event, "unicode", "")
        if text and text in ALLOWED_NAME_CHARS and len(self.new_character_name) < 32:
            self.new_character_name += text

    def _handle_class_key(self, key: int) -> None:
        keys = self.pygame
        if key == keys.K_ESCAPE:
            self.mode = "name"
        elif key in {keys.K_DOWN, keys.K_s}:
            self.class_index = (self.class_index + 1) % len(CLASS_OPTIONS)
        elif key in {keys.K_UP, keys.K_w}:
            self.class_index = (self.class_index - 1) % len(CLASS_OPTIONS)
        elif key in {keys.K_RETURN, keys.K_SPACE}:
            self.mode = "confirm"
            self.confirm_index = 0

    def _handle_confirm_key(self, key: int) -> None:
        keys = self.pygame
        self.error_message = ""
        if key == keys.K_ESCAPE:
            self.mode = "class"
        elif key in {keys.K_DOWN, keys.K_s, keys.K_UP, keys.K_w}:
            self.confirm_index = 1 - self.confirm_index
        elif key in {keys.K_RETURN, keys.K_SPACE}:
            if self.confirm_index == 1:
                self.mode = "class"
                return
            try:
                self.create_new_character()
            except ValueError as exc:
                self.error_message = str(exc)

    def _handle_panel_key(self, key: int) -> None:
        keys = self.pygame
        if key in {keys.K_ESCAPE, keys.K_RETURN, keys.K_SPACE, keys.K_e}:
            self.mode = "main"

    def _ensure_fonts(self) -> None:
        if self._font is not None:
            return
        self._title_font = self.pygame.font.Font(None, 58)
        self._subtitle_font = self.pygame.font.Font(None, 30)
        self._font = self.pygame.font.Font(None, 28)

    def _draw_title(self, surface) -> None:
        self._draw_centered(surface, self._title_font, "MAGIK Engine", 60, colors.WHITE)
        self._draw_centered(surface, self._subtitle_font, "RPG 2D Experimental", 106, colors.TEXT_MUTED)

    def _draw_options(self, surface) -> None:
        box_width = 360
        box_height = 36
        start_y = 150
        screen_width = surface.get_width()
        for index, option in enumerate(self.OPTIONS):
            x = (screen_width - box_width) // 2
            y = start_y + index * 44
            rect = self.pygame.Rect(x, y, box_width, box_height)
            selected = index == self.selected_index
            bg = (39, 48, 76) if selected else colors.DIALOGUE_BG
            border = colors.DIALOGUE_BORDER if selected else (68, 78, 112)
            text_color = colors.WHITE if selected else colors.TEXT_MUTED
            self.pygame.draw.rect(surface, bg, rect)
            self.pygame.draw.rect(surface, border, rect, width=2)
            prefix = "> " if selected else "  "
            label = self._font.render(f"{prefix}{option}", False, text_color)
            surface.blit(label, (rect.x + 18, rect.y + 8))

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

    def _draw_centered(self, surface, font, text: str, y: int, color: tuple[int, int, int]) -> None:
        rendered = font.render(text, False, color)
        x = (surface.get_width() - rendered.get_width()) // 2
        surface.blit(rendered, (x, y))
