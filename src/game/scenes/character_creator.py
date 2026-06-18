"""Simple complete character creator for the 2D game."""

from __future__ import annotations

import json
from typing import Any, Callable

from src.ai.power_interpreter import interpret_power
from src.core.abilities import Ability
from src.core.character import Character, create_character, generate_character_id
from src.game import colors
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
        self._ensure_fonts()
        surface.fill(colors.BLACK)
        self._draw_centered(surface, self._title_font, "Novo Jogo", 52, colors.WHITE)
        self._draw_panel(surface, self.step_title(), self.step_lines())

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
        self.context = self.context.with_character(character.id, self.storage)
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

    def _ensure_fonts(self) -> None:
        if self._font is not None:
            return
        self._title_font = self.pygame.font.Font(None, 48)
        self._font = self.pygame.font.Font(None, 24)

    def _draw_panel(self, surface, title: str, lines: list[str]) -> None:
        rect = self.pygame.Rect(48, 118, surface.get_width() - 96, 330)
        self.pygame.draw.rect(surface, colors.DIALOGUE_BG, rect)
        self.pygame.draw.rect(surface, colors.DIALOGUE_BORDER, rect, width=2)
        title_surface = self._font.render(title, False, colors.WHITE)
        surface.blit(title_surface, (rect.x + 18, rect.y + 14))
        y = rect.y + 46
        max_lines = 14 if self.step == "confirm" else 12
        line_gap = 20 if self.step == "confirm" else 22
        for line in lines[:max_lines]:
            color = colors.WHITE if line.startswith("> ") else colors.TEXT_MUTED
            text = self._font.render(line, False, color)
            surface.blit(text, (rect.x + 18, y))
            y += line_gap

    def _draw_centered(self, surface, font, text: str, y: int, color: tuple[int, int, int]) -> None:
        rendered = font.render(text, False, color)
        x = (surface.get_width() - rendered.get_width()) // 2
        surface.blit(rendered, (x, y))


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
