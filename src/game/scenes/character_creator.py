"""Simple complete character creator for the 2D game."""

from __future__ import annotations

import json
from typing import Any, Callable

from src.ai.power_interpreter import interpret_power
from src.core.abilities import Ability
from src.core.character import Character, create_character, generate_character_id
from src.game.appearance import (
    DEFAULT_APPEARANCE,
    EYE_COLORS,
    HAIR_COLORS,
    HAIR_STYLES,
    OUTFIT_COLORS,
    OUTFIT_STYLES,
    appearance_summary,
    appearance_to_note,
    normalize_appearance,
)
from src.game.game_context import GameContext
from src.game.save import initialize_character_starting_save
from src.game.scenes.base import BaseScene
from src.storage.types import JsonStore


CLASS_OPTIONS: tuple[tuple[str, str], ...] = (
    ("Sombrio", "Manipula sombras, medo e presenca."),
    ("Guerreiro", "Usa forca, tecnica e resistencia."),
    ("Mago", "Estuda energia, simbolos e efeitos arcanos."),
    ("Cacador", "Rastreia, embosca e sobrevive em territorio hostil."),
    ("Curandeiro", "Protege, estabiliza e restaura aliados."),
    ("Inventor", "Cria ferramentas, mecanismos e solucoes improvisadas."),
)
EQUIPMENT_OPTIONS = (
    "Cajado",
    "Espada curta",
    "Adaga",
    "Arco simples",
    "Corrente de Ferro",
    "Escudo pequeno",
    "Amuleto estranho",
    "Bolsa de viagem",
)
ARMOR_OPTIONS: tuple[tuple[int, str], ...] = (
    (0, "Sem protecao"),
    (2, "Protecao leve"),
    (5, "Escudo/armadura simples"),
)
ORIGIN_OPTIONS: tuple[tuple[str, str], ...] = (
    ("cidade-de-pedralume", "Cidade de Pedralume"),
    ("floresta-viridian", "Floresta Viridian"),
    ("vale-vermilion", "Vale Vermilion"),
    ("floresta-do-avesso", "Floresta do Avesso"),
    ("montanhas-trippi", "Montanhas Trippi"),
    ("estrada-do-viajante", "Estrada do Viajante"),
)
ALLOWED_NAME_CHARS = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 -_")
TEXT_LIMITS = {"name": 32, "power": 140, "story": 140}
CREATOR_GOLD = (220, 177, 83)
CREATOR_TEXT = (232, 224, 207)
CREATOR_MUTED = (166, 156, 135)
CREATOR_BG = (8, 9, 14)
CREATOR_PANEL_BG = (8, 9, 14, 214)
CREATOR_PANEL_BORDER = (170, 138, 72, 126)
CREATOR_PANEL_MAGIC = (112, 84, 190, 80)
CREATOR_ERROR = (235, 118, 96)
CREATOR_SHADOW = (0, 0, 0)


PowerInterpreter = Callable[..., dict[str, Any]]


class CharacterCreatorScene(BaseScene):
    STEPS = ("name", "class", "origin", "equipment", "armor", "power", "story", "appearance", "confirm")

    def __init__(
        self,
        pygame,
        context: GameContext,
        storage: JsonStore,
        power_interpreter: PowerInterpreter = interpret_power,
    ) -> None:
        self.pygame = pygame
        self.context = context
        self.storage = storage
        self.power_interpreter = power_interpreter
        self.step = "name"
        self.name = ""
        self.class_index = 0
        self.origin_index = 0
        self.equipment_index = 0
        self.selected_equipment: set[int] = set()
        self.armor_index = 0
        self.power_text = ""
        self.story_text = ""
        self.appearance = dict(DEFAULT_APPEARANCE)
        self.appearance_category_index = 0
        self.confirm_index = 0
        self.error_message = ""
        self.power_interpretation: dict[str, Any] | None = None
        self.requested_scene: str | None = None
        self.should_quit = False
        self._title_font = None
        self._font = None
        self._small_font = None
        self._step_font = None
        self._font_key: tuple[int, int] | None = None

    @property
    def selected_class(self) -> str:
        return CLASS_OPTIONS[self.class_index][0]

    @property
    def selected_armor(self) -> int:
        return ARMOR_OPTIONS[self.armor_index][0]

    @property
    def selected_origin_id(self) -> str:
        return ORIGIN_OPTIONS[self.origin_index][0]

    @property
    def selected_origin_name(self) -> str:
        return ORIGIN_OPTIONS[self.origin_index][1]

    @property
    def selected_equipment_names(self) -> list[str]:
        return [EQUIPMENT_OPTIONS[index] for index in sorted(self.selected_equipment)]

    @property
    def selected_option(self) -> str:
        if self.step == "class":
            return self.selected_class
        if self.step == "origin":
            return self.selected_origin_name
        if self.step == "equipment":
            return EQUIPMENT_OPTIONS[self.equipment_index]
        if self.step == "armor":
            value, label = ARMOR_OPTIONS[self.armor_index]
            return f"{value} - {label}"
        if self.step == "confirm":
            return ("Confirmar e comecar", "Voltar")[self.confirm_index]
        return self.step

    def consume_requested_scene(self) -> str | None:
        requested = self.requested_scene
        self.requested_scene = None
        return requested

    def handle_event(self, event) -> None:
        if event.type != self.pygame.KEYDOWN:
            return
        if self.step == "name":
            self._handle_name_key(event)
        elif self.step == "class":
            self._handle_class_key(event.key)
        elif self.step == "origin":
            self._handle_origin_key(event.key)
        elif self.step == "equipment":
            self._handle_equipment_key(event.key)
        elif self.step == "armor":
            self._handle_armor_key(event.key)
        elif self.step == "power":
            self._handle_text_key(event, "power")
        elif self.step == "story":
            self._handle_text_key(event, "story")
        elif self.step == "appearance":
            self._handle_appearance_key(event.key)
        elif self.step == "confirm":
            self._handle_confirm_key(event.key)

    def update(self) -> None:
        return

    def draw(self, surface) -> None:
        self._ensure_fonts(surface.get_height())
        self._draw_background(surface)
        self._draw_header(surface)
        self._draw_panel(surface, self.step_title(), self.step_lines())
        if surface.get_width() >= 980:
            self._draw_summary_panel(surface)

    def step_title(self) -> str:
        return {
            "name": "1. Nome",
            "class": "2. Classe",
            "origin": "3. Origem",
            "equipment": "4. Equipamentos",
            "armor": "5. Armadura/Escudo",
            "power": "6. Poder Especial",
            "story": "7. Personalidade/Historia",
            "appearance": "8. Aparencia Basica",
            "confirm": "9. Confirmacao",
        }[self.step]

    def step_lines(self) -> list[str]:
        lines_by_step = {
            "name": self.name_lines,
            "class": self.class_lines,
            "origin": self.origin_lines,
            "equipment": self.equipment_lines,
            "armor": self.armor_lines,
            "power": self.power_lines,
            "story": self.story_lines,
            "appearance": self.appearance_lines,
            "confirm": self.confirm_lines,
        }
        lines = lines_by_step[self.step]()
        if self.error_message:
            lines.append(self.error_message)
        return lines

    def name_lines(self) -> list[str]:
        return [
            "Digite o nome do personagem:",
            self.name or "_",
            "Minimo 2, maximo 32 caracteres.",
            "Enter confirma | Backspace apaga | ESC volta",
        ]

    def class_description(self) -> str:
        return CLASS_OPTIONS[self.class_index][1]

    def class_lines(self) -> list[str]:
        lines = []
        for index, (name, _) in enumerate(CLASS_OPTIONS):
            marker = "> " if index == self.class_index else "  "
            lines.append(f"{marker}{name}")
        lines.extend(["", self.class_description(), "Enter/Espaco confirma | ESC volta"])
        return lines

    def origin_lines(self) -> list[str]:
        lines = []
        for index, (_, name) in enumerate(ORIGIN_OPTIONS):
            marker = "> " if index == self.origin_index else "  "
            lines.append(f"{marker}{name}")
        lines.extend(
            [
                "",
                "Origem e identidade narrativa; nao concede bonus mecanico.",
                "Enter/Espaco confirma | ESC volta",
            ]
        )
        return lines

    def equipment_lines(self) -> list[str]:
        lines = []
        for index, name in enumerate(EQUIPMENT_OPTIONS):
            marker = "> " if index == self.equipment_index else "  "
            checked = "[x]" if index in self.selected_equipment else "[ ]"
            lines.append(f"{marker}{checked} {name}")
        selected = ", ".join(self.selected_equipment_names) or "Nenhum equipamento inicial"
        lines.extend(["", f"Selecionados: {selected}", "Enter/Espaco marca | E confirma | ESC volta"])
        return lines

    def armor_lines(self) -> list[str]:
        lines = []
        for index, (value, label) in enumerate(ARMOR_OPTIONS):
            marker = "> " if index == self.armor_index else "  "
            lines.append(f"{marker}{value} - {label}")
        lines.append("Enter/Espaco confirma | ESC volta")
        return lines

    def power_lines(self) -> list[str]:
        return [
            "Descreva seu poder especial bruto:",
            self.power_text or "_",
            "Nao sera interpretado por IA nesta versao.",
            "Enter confirma | Backspace apaga | ESC volta",
        ]

    def story_lines(self) -> list[str]:
        return [
            "Conte uma frase sobre quem seu personagem e:",
            self.story_text or "_",
            "Enter confirma | Backspace apaga | ESC volta",
        ]

    def appearance_lines(self) -> list[str]:
        categories = self._appearance_categories()
        lines = []
        for index, (label, key, _) in enumerate(categories):
            marker = "> " if index == self.appearance_category_index else "  "
            lines.append(f"{marker}{label}: {self.appearance[key]}")
        lines.extend(
            [
                "",
                appearance_summary(self.appearance),
                "Cima/baixo categoria | Esquerda/direita muda",
                "Enter/Espaco/E confirma | ESC volta",
            ]
        )
        return lines

    def confirm_lines(self) -> list[str]:
        equipment = ", ".join(self.selected_equipment_names) or "Nenhum equipamento inicial"
        power = self.power_text.strip() or "Nao informado"
        story = self.story_text.strip() or "Nao informado"
        interpretation = self.ensure_power_interpretation()
        interpreted_name = interpretation.get("nome", "Poder Especial") if interpretation else "Nao informado"
        interpreted_source = interpretation.get("source", "fallback") if interpretation else "fallback"
        lines = [
            f"Nome: {self.name.strip()}",
            f"Classe: {self.selected_class}",
            f"Origem: {self.selected_origin_name}",
            "Vida: 25/25",
            f"Armadura: {self.selected_armor}",
            f"Equipamentos: {equipment}",
            f"Poder: {power}",
            f"Interpretacao: {interpreted_name} ({interpreted_source})",
            f"Historia: {story}",
            f"Aparencia: {appearance_summary(self.appearance)}",
            "Tags: player-created, game-created",
            "Sugestao nao oficial. O mestre deve aprovar.",
            "Visual basico e experimental.",
            "",
        ]
        for index, option in enumerate(("Confirmar e comecar", "Voltar")):
            marker = "> " if index == self.confirm_index else "  "
            lines.append(f"{marker}{option}")
        return lines

    def toggle_equipment(self) -> bool:
        if self.equipment_index in self.selected_equipment:
            self.selected_equipment.remove(self.equipment_index)
            self.error_message = ""
            return True
        if len(self.selected_equipment) >= 2:
            self.error_message = "Escolha no maximo 2 equipamentos principais."
            return False
        self.selected_equipment.add(self.equipment_index)
        self.error_message = ""
        return True

    def validate_name(self) -> bool:
        cleaned = self.name.strip()
        if not cleaned:
            self.error_message = "Nome do personagem e obrigatorio."
            return False
        if len(cleaned) < 2:
            self.error_message = "Nome precisa ter pelo menos 2 caracteres."
            return False
        if len(cleaned) > TEXT_LIMITS["name"]:
            self.error_message = "Nome pode ter no maximo 32 caracteres."
            return False
        self.error_message = ""
        return True

    def create_character_from_selection(self) -> Character:
        if not self.validate_name():
            raise ValueError(self.error_message)
        interpretation = self.ensure_power_interpretation()
        notes = ["Criado pelo jogo 2D"]
        if self.power_text.strip():
            notes.append(f"poder_especial_bruto: {self.power_text.strip()}")
        if interpretation:
            notes.append(f"poder_especial_interpretado: {json.dumps(interpretation, ensure_ascii=False)}")
        notes.append(f"origem_personagem: {self.selected_origin_name} ({self.selected_origin_id})")
        if self.story_text.strip():
            notes.append(f"personalidade_historia: {self.story_text.strip()}")
        notes.append(appearance_to_note(self.appearance))
        special_systems = []
        if self.power_text.strip():
            special_systems.append("poder_especial_bruto")
        if interpretation:
            special_systems.append("poder_especial_interpretado")
        special_systems.append("appearance")
        character = create_character(
            self.storage,
            name=self.name.strip(),
            character_class=self.selected_class,
            max_health=25,
            armor=self.selected_armor,
            equipment=self.selected_equipment_names,
            abilities=[_ability_from_interpretation(interpretation)] if interpretation else [],
            notes=notes,
            tags=["player-created", "game-created"],
            special_systems=special_systems,
            origin_location_id=self.selected_origin_id,
            background_summary=self.story_text.strip(),
            personal_goal="",
        )
        save = initialize_character_starting_save(
            self.storage,
            character,
            campaign_id=self.context.campaign_id,
            session_id=self.context.campaign_session_id,
            fallback_location_id=self.context.location_id,
        )
        self.context = self.context.with_character(character.id, self.storage).with_location(save.location_id)
        self.requested_scene = "overworld"
        return character

    def ensure_power_interpretation(self) -> dict[str, Any] | None:
        if not self.power_text.strip():
            return None
        if self.power_interpretation is not None:
            return self.power_interpretation
        try:
            self.power_interpretation = self.power_interpreter(
                character_name=self.name.strip() or "Aventureiro",
                character_class=self.selected_class,
                equipment=self.selected_equipment_names,
                raw_power=self.power_text.strip(),
                story=self.story_text.strip(),
            )
        except Exception:
            self.power_interpretation = interpret_power(
                character_name=self.name.strip() or "Aventureiro",
                character_class=self.selected_class,
                equipment=self.selected_equipment_names,
                raw_power=self.power_text.strip(),
                story=self.story_text.strip(),
                config=_disabled_ai_config(),
            )
        return self.power_interpretation

    def selected_appearance(self) -> dict[str, str]:
        return normalize_appearance(self.appearance)

    def _handle_name_key(self, event) -> None:
        self.error_message = ""
        key = event.key
        keys = self.pygame
        if key == keys.K_ESCAPE:
            self.requested_scene = "main_menu"
        elif key == keys.K_BACKSPACE:
            self.name = self.name[:-1]
        elif key == keys.K_RETURN:
            if self.validate_name():
                self.step = "class"
        else:
            text = getattr(event, "unicode", "")
            if text and text in ALLOWED_NAME_CHARS and len(self.name) < TEXT_LIMITS["name"]:
                self.name += text

    def _handle_class_key(self, key: int) -> None:
        keys = self.pygame
        if key == keys.K_ESCAPE:
            self.step = "name"
        elif key in {keys.K_DOWN, keys.K_s}:
            self.class_index = (self.class_index + 1) % len(CLASS_OPTIONS)
        elif key in {keys.K_UP, keys.K_w}:
            self.class_index = (self.class_index - 1) % len(CLASS_OPTIONS)
        elif key in {keys.K_RETURN, keys.K_SPACE}:
            self.step = "origin"

    def _handle_origin_key(self, key: int) -> None:
        keys = self.pygame
        if key == keys.K_ESCAPE:
            self.step = "class"
        elif key in {keys.K_DOWN, keys.K_s}:
            self.origin_index = (self.origin_index + 1) % len(ORIGIN_OPTIONS)
        elif key in {keys.K_UP, keys.K_w}:
            self.origin_index = (self.origin_index - 1) % len(ORIGIN_OPTIONS)
        elif key in {keys.K_RETURN, keys.K_SPACE}:
            self.step = "equipment"

    def _handle_equipment_key(self, key: int) -> None:
        keys = self.pygame
        if key == keys.K_ESCAPE:
            self.step = "origin"
        elif key in {keys.K_DOWN, keys.K_s}:
            self.equipment_index = (self.equipment_index + 1) % len(EQUIPMENT_OPTIONS)
        elif key in {keys.K_UP, keys.K_w}:
            self.equipment_index = (self.equipment_index - 1) % len(EQUIPMENT_OPTIONS)
        elif key in {keys.K_RETURN, keys.K_SPACE}:
            self.toggle_equipment()
        elif key == keys.K_e:
            self.step = "armor"
            self.error_message = ""

    def _handle_armor_key(self, key: int) -> None:
        keys = self.pygame
        if key == keys.K_ESCAPE:
            self.step = "equipment"
        elif key in {keys.K_DOWN, keys.K_s}:
            self.armor_index = (self.armor_index + 1) % len(ARMOR_OPTIONS)
        elif key in {keys.K_UP, keys.K_w}:
            self.armor_index = (self.armor_index - 1) % len(ARMOR_OPTIONS)
        elif key in {keys.K_RETURN, keys.K_SPACE}:
            self.step = "power"

    def _handle_text_key(self, event, field: str) -> None:
        key = event.key
        keys = self.pygame
        value = self.power_text if field == "power" else self.story_text
        if key == keys.K_ESCAPE:
            self.step = "armor" if field == "power" else "power"
            return
        if key == keys.K_BACKSPACE:
            value = value[:-1]
        elif key == keys.K_RETURN:
            if field == "power":
                self.power_interpretation = None
                self.step = "story"
            else:
                self.power_interpretation = None
                self.step = "appearance"
            return
        else:
            text = getattr(event, "unicode", "")
            if text and text.isprintable() and len(value) < TEXT_LIMITS[field]:
                value += text
        if field == "power":
            self.power_text = value
        else:
            self.story_text = value

    def _handle_confirm_key(self, key: int) -> None:
        keys = self.pygame
        if key == keys.K_ESCAPE:
            self.step = "appearance"
        elif key in {keys.K_DOWN, keys.K_s, keys.K_UP, keys.K_w}:
            self.confirm_index = 1 - self.confirm_index
        elif key in {keys.K_RETURN, keys.K_SPACE}:
            if self.confirm_index == 1:
                self.step = "appearance"
                return
            try:
                self.create_character_from_selection()
            except ValueError as exc:
                self.error_message = str(exc)

    def _handle_appearance_key(self, key: int) -> None:
        keys = self.pygame
        categories = self._appearance_categories()
        if key == keys.K_ESCAPE:
            self.step = "story"
        elif key in {keys.K_DOWN, keys.K_s}:
            self.appearance_category_index = (self.appearance_category_index + 1) % len(categories)
        elif key in {keys.K_UP, keys.K_w}:
            self.appearance_category_index = (self.appearance_category_index - 1) % len(categories)
        elif key in {keys.K_RIGHT, keys.K_d}:
            self._change_appearance_option(1)
        elif key in {keys.K_LEFT, keys.K_a}:
            self._change_appearance_option(-1)
        elif key in {keys.K_RETURN, keys.K_SPACE, keys.K_e}:
            self.step = "confirm"

    def _change_appearance_option(self, delta: int) -> None:
        _, key, options = self._appearance_categories()[self.appearance_category_index]
        current = self.appearance[key]
        index = options.index(current) if current in options else 0
        self.appearance[key] = options[(index + delta) % len(options)]

    def _appearance_categories(self) -> tuple[tuple[str, str, tuple[str, ...]], ...]:
        return (
            ("Tipo de cabelo", "hair_style", HAIR_STYLES),
            ("Cor do cabelo", "hair_color", tuple(HAIR_COLORS)),
            ("Cor dos olhos", "eye_color", tuple(EYE_COLORS)),
            ("Estilo de roupa", "outfit_style", OUTFIT_STYLES),
            ("Cor da roupa", "outfit_color", tuple(OUTFIT_COLORS)),
        )

    def _ensure_fonts(self, screen_height: int = 480) -> None:
        key = (screen_height, _clamp(int(screen_height * 0.033), 22, 30))
        if self._font is not None and self._font_key == key:
            return
        self._font_key = key
        self._title_font = self.pygame.font.Font(None, _clamp(int(screen_height * 0.07), 42, 66))
        self._step_font = self.pygame.font.Font(None, _clamp(int(screen_height * 0.038), 26, 36))
        self._font = self.pygame.font.Font(None, key[1])
        self._small_font = self.pygame.font.Font(None, _clamp(int(screen_height * 0.026), 18, 23))

    def _draw_background(self, surface) -> None:
        surface.fill(CREATOR_BG)
        width = surface.get_width()
        height = surface.get_height()
        for row in range(0, height, 32):
            alpha = max(18, 54 - row // 18)
            line = self.pygame.Surface((width, 1), self.pygame.SRCALPHA)
            line.fill((112, 84, 190, alpha))
            surface.blit(line, (0, row))
        vignette = self.pygame.Surface((width, height), self.pygame.SRCALPHA)
        vignette.fill((0, 0, 0, 46))
        surface.blit(vignette, (0, 0))

    def _draw_header(self, surface) -> None:
        title = self._title_font.render("Criacao de Personagem", True, CREATOR_TEXT)
        shadow = self._title_font.render("Criacao de Personagem", True, CREATOR_SHADOW)
        x = max(46, int(surface.get_width() * 0.07))
        y = max(28, int(surface.get_height() * 0.045))
        surface.blit(shadow, (x + 3, y + 3))
        surface.blit(title, (x, y))
        subtitle = self._small_font.render("Um ritual para dar forma ao seu aventureiro", True, CREATOR_MUTED)
        surface.blit(subtitle, (x + 2, y + title.get_height() + 4))

    def _main_panel_rect(self, surface):
        has_summary = surface.get_width() >= 980
        x = max(44, int(surface.get_width() * 0.07))
        y = max(116, int(surface.get_height() * 0.19))
        width_ratio = 0.58 if has_summary else 0.86
        width = _clamp(int(surface.get_width() * width_ratio), 520, 820)
        height = _clamp(int(surface.get_height() * 0.66), 330, 520)
        return self.pygame.Rect(x, y, width, height)

    def _summary_panel_rect(self, surface, main_rect):
        gap = max(24, int(surface.get_width() * 0.025))
        x = main_rect.right + gap
        y = main_rect.y + 28
        width = max(260, surface.get_width() - x - max(42, int(surface.get_width() * 0.06)))
        height = min(main_rect.height - 56, 360)
        return self.pygame.Rect(x, y, width, height)

    def _draw_panel(self, surface, title: str, lines: list[str]) -> None:
        rect = self._main_panel_rect(surface)
        self._draw_panel_frame(surface, rect)
        step_label = f"Etapa {self._step_number()} de {len(self.STEPS)}"
        step_surface = self._small_font.render(step_label.upper(), True, CREATOR_GOLD)
        title_surface = self._step_font.render(self._clean_step_title(title), True, CREATOR_TEXT)
        surface.blit(step_surface, (rect.x + 28, rect.y + 22))
        surface.blit(title_surface, (rect.x + 28, rect.y + 48))
        self._draw_progress_bar(surface, rect)

        y = rect.y + 108
        content_bottom = rect.bottom - 58
        line_gap = _clamp(int(rect.height * (0.052 if self.step == "confirm" else 0.062)), 21, 30)
        for line in lines:
            if not line:
                y += line_gap // 2
                continue
            if y > content_bottom:
                break
            color = self._line_color(line)
            font = self._small_font if self._is_instruction_line(line) else self._font
            text = font.render(line, True, color)
            x = rect.x + 34
            if line.startswith("> "):
                self._draw_selection_mark(surface, rect.x + 24, y + 5)
                x = rect.x + 52
                text = font.render(line[2:], True, color)
            surface.blit(text, (x, y))
            y += line_gap
        self._draw_footer(surface, rect)

    def _draw_panel_frame(self, surface, rect) -> None:
        panel = self.pygame.Surface((rect.width, rect.height), self.pygame.SRCALPHA)
        panel.fill(CREATOR_PANEL_BG)
        surface.blit(panel, (rect.x, rect.y))
        self.pygame.draw.rect(surface, CREATOR_PANEL_BORDER, rect, width=1)
        self.pygame.draw.rect(surface, CREATOR_PANEL_MAGIC, rect.inflate(-10, -10), width=1)

    def _draw_summary_panel(self, surface) -> None:
        main_rect = self._main_panel_rect(surface)
        rect = self._summary_panel_rect(surface, main_rect)
        self._draw_panel_frame(surface, rect)
        title = self._small_font.render("RESUMO DO PERSONAGEM", True, CREATOR_GOLD)
        surface.blit(title, (rect.x + 22, rect.y + 20))
        rows = [
            ("Nome", self.name.strip() or "-"),
            ("Classe", self.selected_class),
            ("Origem", self.selected_origin_name),
            ("Armadura", str(self.selected_armor)),
            ("Equip.", ", ".join(self.selected_equipment_names) or "-"),
            ("Historia", self.story_text.strip() or "-"),
        ]
        y = rect.y + 62
        for label, value in rows:
            if y > rect.bottom - 34:
                break
            label_surface = self._small_font.render(label.upper(), True, CREATOR_GOLD)
            value_surface = self._small_font.render(_clip_text(value, 34), True, CREATOR_TEXT)
            surface.blit(label_surface, (rect.x + 22, y))
            surface.blit(value_surface, (rect.x + 118, y))
            y += 34

    def _draw_progress_bar(self, surface, rect) -> None:
        bar_rect = self.pygame.Rect(rect.x + 28, rect.y + 88, rect.width - 56, 5)
        self.pygame.draw.rect(surface, (36, 31, 42), bar_rect)
        filled_width = max(8, int(bar_rect.width * self._step_number() / len(self.STEPS)))
        self.pygame.draw.rect(surface, CREATOR_GOLD, self.pygame.Rect(bar_rect.x, bar_rect.y, filled_width, bar_rect.height))

    def _draw_selection_mark(self, surface, x: int, y: int) -> None:
        points = [(x, y + 5), (x + 10, y), (x + 10, y + 10)]
        self.pygame.draw.polygon(surface, CREATOR_GOLD, points)

    def _draw_footer(self, surface, rect) -> None:
        footer = self._footer_text()
        rendered = self._small_font.render(footer, True, CREATOR_MUTED)
        surface.blit(rendered, (rect.x + 28, rect.bottom - 36))

    def _footer_text(self) -> str:
        if self.step in {"name", "power", "story"}:
            return "Enter confirma | Backspace apaga | ESC volta"
        if self.step in {"class", "origin", "armor", "confirm"}:
            return "Setas/WASD escolhem | Enter/Espaco confirma | ESC volta"
        if self.step == "appearance":
            return "Cima/baixo categoria | Esquerda/direita muda | Enter confirma"
        return "Setas/WASD escolhem | Enter/Espaco marca | E confirma | ESC volta"

    def _line_color(self, line: str) -> tuple[int, int, int]:
        if line == self.error_message:
            return CREATOR_ERROR
        if line.startswith("> "):
            return CREATOR_GOLD
        if self._is_instruction_line(line):
            return CREATOR_MUTED
        return CREATOR_TEXT

    def _is_instruction_line(self, line: str) -> bool:
        markers = ("Enter", "ESC", "Cima/baixo", "Setas", "Minimo", "Nao sera", "Origem e", "Visual basico", "Sugestao")
        return line.startswith(markers) or " confirma" in line or " volta" in line

    def _step_number(self) -> int:
        return self.STEPS.index(self.step) + 1

    def _clean_step_title(self, title: str) -> str:
        return title.split(". ", 1)[1] if ". " in title else title


def _clamp(value: int, minimum: int, maximum: int) -> int:
    return max(minimum, min(value, maximum))


def _clip_text(value: str, limit: int) -> str:
    if len(value) <= limit:
        return value
    return value[: max(0, limit - 3)].rstrip() + "..."


def _ability_from_interpretation(interpretation: dict[str, Any]) -> dict[str, Any]:
    name = str(interpretation.get("nome") or "Poder Especial")
    ability_type = str(interpretation.get("tipo") or "utilidade").strip().casefold()
    if ability_type not in {
        "ataque",
        "defesa",
        "suporte",
        "cura",
        "magia",
        "controle",
        "utilidade",
        "transformacao",
        "passiva",
        "unica",
    }:
        ability_type = "utilidade"
    notes = "Precisa de aprovacao do mestre. Nao cria dano automatico nem altera regras oficiais."
    if interpretation.get("observacao_do_mestre"):
        notes = f"{notes} {interpretation['observacao_do_mestre']}"
    return Ability(
        id=f"poder-{generate_character_id(name)}",
        name=name,
        description=str(interpretation.get("descricao") or ""),
        type=ability_type,
        use="livre",
        effect=str(interpretation.get("efeito_narrativo") or ""),
        cost=str(interpretation.get("custo_ou_preco") or interpretation.get("limitacao") or ""),
        requires_test=bool(interpretation.get("teste_sugerido")),
        suggested_test=str(interpretation.get("teste_sugerido") or "") or None,
        notes=notes,
    ).to_dict()


def _disabled_ai_config():
    from src.ai.narrator import AIConfig

    return AIConfig(enabled=False, api_key=None)
