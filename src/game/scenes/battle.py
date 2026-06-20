"""Initial visual battle scene for the 2D prototype."""

from __future__ import annotations

from src.core.abilities import Ability, list_abilities, use_ability
from src.core.character import Character
from src.core.combat import apply_physical_damage, roll_damage
from src.game import assets
from src.game.dice import AttackResolution, resolve_basic_attack
from src.game.entities.creature import Creature
from src.game.event_registry import register_battle_event
from src.game.game_context import GameContext
from src.game.scenes.base import BaseScene
from src.game.save import DEFAULT_SAVE_ID, register_defeated_enemy
from src.game.ui import panels
from src.storage.types import JsonStore


class BattleScene(BaseScene):
    OPTIONS = ("Atacar", "Habilidade", "Observar", "Fugir")
    ATTACK_MODIFIER = 2
    ATTACK_DIFFICULTY = 13
    DICE_ANIMATION_FRAMES = 12

    def __init__(
        self,
        pygame,
        context: GameContext,
        character: Character,
        creature: Creature,
        return_scene: BaseScene | None = None,
        storage: JsonStore | None = None,
        rng=None,
    ) -> None:
        self.pygame = pygame
        self.context = context
        self.character = character
        self.creature = creature
        self.return_scene = return_scene
        self.storage = storage
        self.rng = rng
        self.selected_index = 0
        self.ability_index = 0
        self.mode = "actions"
        self.log: list[str] = [f"{character.name} encontrou {creature.name}."]
        self.requested_scene: str | None = None
        self.should_quit = False
        self.victory = False
        self.defeat = False
        self.fled = False
        self.turn_state = "jogador"
        self.pending_attack: AttackResolution | None = None
        self.last_attack_resolution: AttackResolution | None = None
        self.dice_frames_remaining = 0
        self.dice_display_value = 1
        self._font = None
        self._title_font = None
        self._assets = None
        self._register_battle_event("inicio", f"Combate iniciado contra {creature.name}.")

    @property
    def selected_option(self) -> str:
        if self.mode == "abilities":
            abilities = self.available_abilities()
            if not abilities:
                return "Habilidade"
            return abilities[self.ability_index].name
        if self.battle_ended:
            return "Voltar ao mapa"
        return self.OPTIONS[self.selected_index]

    @property
    def battle_ended(self) -> bool:
        return self.victory or self.defeat or self.fled

    def consume_requested_scene(self) -> str | None:
        requested = self.requested_scene
        self.requested_scene = None
        return requested

    def handle_event(self, event) -> None:
        if event.type != self.pygame.KEYDOWN:
            return
        if self.pending_attack is not None:
            return
        if self.battle_ended:
            if event.key in {self.pygame.K_RETURN, self.pygame.K_SPACE, self.pygame.K_e}:
                self.requested_scene = "overworld"
            return
        if self.mode == "abilities":
            self._handle_ability_key(event.key)
            return
        if event.key == self.pygame.K_ESCAPE:
            self.flee()
        elif event.key in {self.pygame.K_DOWN, self.pygame.K_s}:
            self.selected_index = (self.selected_index + 1) % len(self.OPTIONS)
        elif event.key in {self.pygame.K_UP, self.pygame.K_w}:
            self.selected_index = (self.selected_index - 1) % len(self.OPTIONS)
        elif event.key in {self.pygame.K_RETURN, self.pygame.K_SPACE, self.pygame.K_e}:
            self.confirm_selection()

    def update(self) -> None:
        if self.pending_attack is None:
            return
        if self.dice_frames_remaining > 0:
            self.dice_display_value = ((self.dice_display_value + 6) % 20) + 1
            self.dice_frames_remaining -= 1
            return
        self._resolve_pending_attack()

    def draw(self, surface) -> None:
        self._ensure_draw_resources()
        width, height = surface.get_width(), surface.get_height()
        layout = _battle_layout(width, height, self.pygame)
        surface.fill((7, 8, 15))
        self._draw_title(surface, layout["title"])
        self._draw_combatants(surface, layout["player"], layout["creature"])
        self._draw_roll_panel(surface, layout["roll"])
        self._draw_log(surface, layout["log"])
        self._draw_menu(surface, layout["menu"])
        self._draw_dice_overlay(surface)

    def confirm_selection(self) -> None:
        option = self.selected_option
        if option == "Atacar":
            self.attack()
        elif option == "Habilidade":
            self.open_abilities()
        elif option == "Observar":
            self.observe()
        elif option == "Fugir":
            self.flee()

    def available_abilities(self) -> list[Ability]:
        try:
            return list_abilities(self.character)
        except ValueError:
            return []

    def open_abilities(self) -> None:
        abilities = self.available_abilities()
        if not abilities:
            self._add_log("Nenhuma habilidade disponivel.")
            return
        self.mode = "abilities"
        self.ability_index = 0
        self._add_log("Escolha uma habilidade.")

    def use_selected_ability(self) -> None:
        abilities = self.available_abilities()
        if not abilities:
            self.mode = "actions"
            self._add_log("Nenhuma habilidade disponivel.")
            return
        ability = abilities[self.ability_index]
        try:
            result = use_ability(self.character, ability.id)
        except ValueError as exc:
            self._add_log(str(exc))
            self.mode = "actions"
            return
        self._add_log(f"{self.character.name} usou {result.ability.name}: {result.effect or 'efeito narrativo.'}")
        if result.cost:
            self._add_log(f"Custo: {result.cost}")
        if result.remaining_uses is not None:
            self._add_log(f"Usos restantes: {result.remaining_uses}")
        self._register_battle_event("habilidade", f"{self.character.name} usou {result.ability.name}.")
        self.mode = "actions"

    def attack(self) -> None:
        if self.battle_ended or self.creature.current_health <= 0 or self.pending_attack is not None:
            return
        self.turn_state = "jogador"
        self.pending_attack = resolve_basic_attack(
            modifier=self.ATTACK_MODIFIER,
            difficulty=self.ATTACK_DIFFICULTY,
            rng=self.rng,
        )
        self.last_attack_resolution = None
        self.dice_frames_remaining = self.DICE_ANIMATION_FRAMES
        self.dice_display_value = 1
        self.turn_state = "rolagem"
        self._add_log(f"{self.character.name} prepara um ataque. Rolando D20...")

    def _resolve_pending_attack(self) -> None:
        if self.pending_attack is None:
            return
        resolution = self.pending_attack
        self.pending_attack = None
        self.last_attack_resolution = resolution
        self.turn_state = "jogador"
        check = resolution.check
        self._add_log(f"D20: {check.natural} | Modificador: {check.modifier:+d} | Total: {check.total}")
        self._add_log(f"Dificuldade: {check.difficulty} | Resultado: {_check_outcome_label(check.outcome)}")
        if not check.is_success:
            self._add_log(f"{self.character.name} errou o ataque.")
            self.creature_turn()
            return
        damage = resolution.damage
        damage_text = _damage_roll_text(resolution)
        result = apply_physical_damage(self.creature.current_health, self.creature.armor, damage)
        self.creature.current_health = result.current_health
        self.creature.armor = result.armor
        self._add_log(f"{self.character.name} acertou {self.creature.name}. {damage_text}")
        if self.creature.current_health <= 0:
            self._win()
            return
        self.creature_turn()

    def creature_turn(self) -> None:
        if self.creature.current_health <= 0 or self.character.current_health <= 0:
            return
        self.turn_state = "criatura"
        damage = roll_damage(max(self.character.current_health, 1), self.rng).result
        result = apply_physical_damage(self.character.current_health, self.character.armor, damage)
        self.character.current_health = result.current_health
        self.character.armor = result.armor
        self._add_log(f"{self.creature.name} atacou {self.character.name} e causou {damage} de dano.")
        if self.character.current_health <= 0:
            self._defeat()
            return
        self.turn_state = "jogador"

    def observe(self) -> None:
        hostile = "hostil" if self.creature.hostile else "nao hostil"
        self._add_log(
            f"{self.creature.name}: {self.creature.description} Vida: {self.creature.current_health}/{self.creature.max_health}. "
            f"Armadura: {self.creature.armor}. Estado: {hostile}. Dica: observe a armadura antes de insistir."
        )

    def flee(self) -> None:
        self._add_log(f"{self.character.name} fugiu do encontro com {self.creature.name}.")
        self.fled = True
        self.turn_state = "fuga"
        self._register_battle_event("fuga", f"{self.character.name} fugiu de {self.creature.name}.")
        self.requested_scene = "overworld"

    def _win(self) -> None:
        self.victory = True
        self.turn_state = "vitoria"
        self._add_log(f"Vitoria! {self.creature.name} foi derrotada.")
        self._add_log("Pressione Enter ou Espaco para voltar ao mapa.")
        self._register_battle_event("vitoria", f"{self.creature.name} foi derrotada.")
        self._register_defeated_creature()

    def _defeat(self) -> None:
        self.defeat = True
        self.turn_state = "derrota"
        self._add_log(f"{self.character.name} caiu. O mestre decide a consequencia.")
        self._add_log("Pressione Enter ou Espaco para voltar ao mapa.")
        self._register_battle_event("derrota", f"{self.character.name} chegou a 0 de vida temporaria.")

    def _handle_ability_key(self, key: int) -> None:
        abilities = self.available_abilities()
        if key == self.pygame.K_ESCAPE:
            self.mode = "actions"
            return
        if key in {self.pygame.K_DOWN, self.pygame.K_s} and abilities:
            self.ability_index = (self.ability_index + 1) % len(abilities)
        elif key in {self.pygame.K_UP, self.pygame.K_w} and abilities:
            self.ability_index = (self.ability_index - 1) % len(abilities)
        elif key in {self.pygame.K_RETURN, self.pygame.K_SPACE, self.pygame.K_e}:
            self.use_selected_ability()

    def _add_log(self, text: str) -> None:
        self.log.append(text)
        if len(self.log) > 6:
            self.log = self.log[-6:]

    def _register_battle_event(self, event_name: str, detail: str) -> None:
        if self.storage is None:
            return
        register_battle_event(self.storage, self.context, self.creature, self.creature.position, event_name, detail)

    def _register_defeated_creature(self) -> None:
        marker = getattr(self.return_scene, "mark_creature_defeated", None)
        if callable(marker):
            marker(self.creature.id)
            return
        if self.storage is not None:
            register_defeated_enemy(self.storage, DEFAULT_SAVE_ID, self.creature.id)

    def _ensure_draw_resources(self) -> None:
        if self._font is not None:
            return
        self._font = self.pygame.font.Font(None, 24)
        self._title_font = self.pygame.font.Font(None, 34)
        self._assets = assets.create_assets(self.pygame)

    def _draw_title(self, surface, position: tuple[int, int]) -> None:
        title = self._title_font.render("Combate", False, panels.PANEL_GOLD)
        subtitle = self._font.render(f"Turno: {self.turn_state}", False, panels.TEXT_MUTED)
        surface.blit(title, position)
        surface.blit(subtitle, (position[0] + title.get_width() + 18, position[1] + 7))

    def _draw_combatants(self, surface, left, right) -> None:
        self._draw_panel(surface, left, alpha=220)
        self._draw_panel(surface, right, alpha=220)
        surface.blit(self._assets.player["right"][0], (left.x + 18, left.y + 44))
        surface.blit(self._assets.creature, (right.x + right.width - 58, right.y + 44))
        self._draw_stats(surface, left, self.character.name, self.character.current_health, self.character.max_health, self.character.armor)
        self._draw_stats(surface, right, self.creature.name, self.creature.current_health, self.creature.max_health, self.creature.armor)

    def _draw_stats(self, surface, rect, name: str, health: int, max_health: int, armor: int) -> None:
        name_surface = self._font.render(_truncate_text(name, self._font, rect.width - 28), False, panels.TEXT_IVORY)
        surface.blit(name_surface, (rect.x + 14, rect.y + 12))
        bar_width = min(150, rect.width - 86)
        self._draw_bar(surface, rect.x + 14, rect.y + 38, bar_width, health, max_health, (114, 207, 142))
        self._draw_bar(surface, rect.x + 14, rect.y + 52, bar_width, armor, 10, (139, 124, 246))
        health_surface = self._font.render(f"Vida {health}/{max_health}", False, panels.TEXT_MUTED)
        armor_surface = self._font.render(f"Armadura {armor}", False, panels.TEXT_MUTED)
        surface.blit(health_surface, (rect.x + 14, rect.y + 68))
        surface.blit(armor_surface, (rect.x + 14, rect.y + 90))

    def _draw_roll_panel(self, surface, rect) -> None:
        self._draw_panel(surface, rect, alpha=226)
        title = self._font.render("Rolagem de ataque", False, panels.PANEL_GOLD)
        surface.blit(title, (rect.x + 18, rect.y + 14))
        panels.draw_panel_separator(self.pygame, surface, (rect.x + 18, rect.y + 42), (rect.right - 18, rect.y + 42))
        if self.pending_attack is not None:
            self._draw_active_roll_details(surface, rect)
            return
        if self.last_attack_resolution is not None:
            self._draw_attack_result_details(surface, rect, self.last_attack_resolution)
            return
        hint = self._font.render("Escolha Atacar para rolar 1d20 + 2 contra DT 13.", False, panels.TEXT_MUTED)
        surface.blit(hint, (rect.x + 18, rect.y + 58))

    def _draw_active_roll_details(self, surface, rect) -> None:
        dice_rect = self.pygame.Rect(rect.x + 22, rect.y + 56, 76, 62)
        self.pygame.draw.rect(surface, (26, 22, 38), dice_rect, border_radius=6)
        self.pygame.draw.rect(surface, panels.PANEL_GOLD, dice_rect, width=2, border_radius=6)
        value = self._title_font.render(str(self.dice_display_value), False, panels.TEXT_IVORY)
        surface.blit(value, (dice_rect.centerx - value.get_width() // 2, dice_rect.centery - value.get_height() // 2))
        lines = ("D20 em movimento...", f"Modificador: {self.ATTACK_MODIFIER:+d}", f"DT: {self.ATTACK_DIFFICULTY}")
        for index, line in enumerate(lines):
            text = self._font.render(line, False, panels.TEXT_IVORY if index == 0 else panels.TEXT_MUTED)
            surface.blit(text, (dice_rect.right + 22, rect.y + 58 + index * 24))

    def _draw_attack_result_details(self, surface, rect, resolution: AttackResolution) -> None:
        check = resolution.check
        color = _outcome_color(check.outcome)
        badge = self.pygame.Rect(rect.x + 22, rect.y + 56, 104, 62)
        self.pygame.draw.rect(surface, (24, 20, 34), badge, border_radius=6)
        self.pygame.draw.rect(surface, color, badge, width=2, border_radius=6)
        d20_label = "D20"
        if check.natural in {1, 20}:
            d20_label = "natural"
        label = self._font.render(d20_label, False, panels.TEXT_MUTED)
        value = self._title_font.render(str(check.natural), False, color)
        surface.blit(label, (badge.centerx - label.get_width() // 2, badge.y + 8))
        surface.blit(value, (badge.centerx - value.get_width() // 2, badge.y + 28))
        for index, line in enumerate(_attack_detail_lines(resolution)):
            line_color = color if line.startswith("Resultado:") else panels.TEXT_IVORY
            text = self._font.render(_truncate_text(line, self._font, rect.width - 164), False, line_color)
            surface.blit(text, (badge.right + 22, rect.y + 55 + index * 22))

    def _draw_log(self, surface, rect) -> None:
        self._draw_panel(surface, rect, alpha=216)
        title = self._font.render("Registro", False, panels.PANEL_GOLD)
        surface.blit(title, (rect.x + 14, rect.y + 10))
        visible_lines = max(2, (rect.height - 42) // 22)
        for index, line in enumerate(self.log[-visible_lines:]):
            color = panels.TEXT_IVORY if index == len(self.log[-visible_lines:]) - 1 else panels.TEXT_MUTED
            text = self._font.render(_truncate_text(line, self._font, rect.width - 28), False, color)
            surface.blit(text, (rect.x + 14, rect.y + 36 + index * 22))

    def _draw_menu(self, surface, rect) -> None:
        self._draw_panel(surface, rect, alpha=224)
        options = tuple(ability.name for ability in self.available_abilities()) if self.mode == "abilities" else self.OPTIONS
        if self.battle_ended:
            options = ("Voltar ao mapa",)
        for index, option in enumerate(options):
            selected = (index == self.ability_index if self.mode == "abilities" else index == self.selected_index) and not self.battle_ended
            color = panels.PANEL_GOLD if selected else panels.TEXT_IVORY
            label = f"> {option}" if selected else option
            text = self._font.render(label, False, color)
            item_x = rect.x + 18 + index * max(130, rect.width // 5)
            surface.blit(text, (item_x, rect.y + 22))
        hint = "Cima/baixo escolhe | Enter/E confirma | ESC fugir"
        if self.pending_attack is not None:
            hint = "Rolando dados..."
        if self.mode == "abilities":
            hint = "Cima/baixo escolhe habilidade | ESC volta"
        if self.battle_ended:
            hint = "Enter/Espaco para voltar ao mapa"
        hint_surface = self._font.render(hint, False, panels.TEXT_MUTED)
        surface.blit(hint_surface, (rect.x + 18, rect.y + 58))

    def _draw_dice_overlay(self, surface) -> None:
        if self.pending_attack is None:
            return
        width, height = surface.get_width(), surface.get_height()
        rect = self.pygame.Rect(width // 2 - 96, height // 2 - 82, 192, 164)
        self._draw_panel(surface, rect, alpha=238)
        title = self._font.render("Rolando D20", False, panels.PANEL_GOLD)
        value = self._title_font.render(str(self.dice_display_value), False, panels.TEXT_IVORY)
        footer = self._font.render("O dado decide o ataque", False, panels.TEXT_MUTED)
        surface.blit(title, (rect.centerx - title.get_width() // 2, rect.y + 18))
        dice_rect = self.pygame.Rect(rect.centerx - 32, rect.y + 48, 64, 48)
        self.pygame.draw.rect(surface, (28, 24, 42), dice_rect)
        self.pygame.draw.rect(surface, panels.PANEL_GOLD, dice_rect, width=2)
        surface.blit(value, (dice_rect.centerx - value.get_width() // 2, dice_rect.centery - value.get_height() // 2))
        surface.blit(footer, (rect.centerx - footer.get_width() // 2, rect.y + 108))

    def _draw_panel(self, surface, rect, *, alpha: int = 232) -> None:
        panels.draw_dark_fantasy_panel(self.pygame, surface, rect, alpha=alpha, border_radius=8)

    def _draw_bar(
        self,
        surface,
        x: int,
        y: int,
        width: int,
        value: int,
        maximum: int,
        color: tuple[int, int, int],
    ) -> None:
        self.pygame.draw.rect(surface, (28, 32, 48), (x, y, width, 10))
        ratio = 0 if maximum <= 0 else max(0, min(value / maximum, 1))
        self.pygame.draw.rect(surface, color, (x, y, int(width * ratio), 10))


def _check_outcome_label(outcome: str) -> str:
    labels = {
        "critical_failure": "Falha critica",
        "failure": "Falha",
        "success": "Sucesso",
        "critical_success": "Critico",
    }
    return labels.get(outcome, outcome)


def _attack_detail_lines(resolution: AttackResolution) -> tuple[str, ...]:
    check = resolution.check
    lines = [
        f"D20: {check.natural}  {check.modifier:+d} = {check.total}",
        f"DT: {check.difficulty}",
        f"Resultado: {_check_outcome_label(check.outcome)}",
    ]
    if check.is_critical_failure:
        lines.append("Sua sombra se move antes de voce. O ataque falha.")
    elif resolution.damage_roll is not None:
        lines.append(_damage_roll_text(resolution).rstrip("."))
    else:
        lines.append("Dano: nenhum")
    return tuple(lines)


def _damage_roll_text(resolution: AttackResolution) -> str:
    if resolution.damage_roll is None:
        return "Dano: nenhum."
    rolls = "+".join(str(value) for value in resolution.damage_roll.rolls)
    return f"Dano: {resolution.damage_roll.expression} = {rolls} -> {resolution.damage_roll.total}."


def _outcome_color(outcome: str) -> tuple[int, int, int]:
    if outcome == "critical_success":
        return (228, 183, 83)
    if outcome == "critical_failure":
        return (170, 72, 92)
    if outcome == "failure":
        return (184, 118, 104)
    return (218, 209, 170)


def _battle_layout(width: int, height: int, pygame) -> dict[str, object]:
    margin = max(24, min(48, width // 28))
    title = (margin, max(16, height // 36))
    compact = height < 600
    card_width = min(360, max(250, (width - margin * 3) // 2))
    card_height = 110 if compact else 118
    top = max(58, height // 12)
    player = pygame.Rect(margin, top, card_width, card_height)
    creature = pygame.Rect(width - margin - card_width, top, card_width, card_height)
    menu_height = 88 if compact else 96
    menu = pygame.Rect(margin, height - menu_height - margin, width - margin * 2, menu_height)
    log_height = 72 if compact else max(88, min(132, height // 5))
    log = pygame.Rect(margin, menu.y - log_height - 14, width - margin * 2, log_height)
    roll_y = player.bottom + 16
    available_roll_height = log.y - roll_y - 14
    if available_roll_height >= 92:
        roll_height = min(154, available_roll_height)
    else:
        roll_height = max(54, available_roll_height)
    roll = pygame.Rect(margin, roll_y, width - margin * 2, roll_height)
    return {
        "title": title,
        "player": player,
        "creature": creature,
        "roll": roll,
        "log": log,
        "menu": menu,
    }


def _truncate_text(text: str, font, max_width: int) -> str:
    if max_width <= 0 or font.size(text)[0] <= max_width:
        return text
    suffix = "..."
    available = max_width - font.size(suffix)[0]
    if available <= 0:
        return suffix
    result = text
    while result and font.size(result)[0] > available:
        result = result[:-1]
    return result.rstrip() + suffix
