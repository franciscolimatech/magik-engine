"""Initial visual battle scene for the 2D prototype."""

from __future__ import annotations

from src.core.abilities import Ability, list_abilities, use_ability
from src.core.character import Character
from src.core.combat import apply_physical_damage, roll_damage
from src.game import assets, colors
from src.game.dice import AttackResolution, resolve_basic_attack
from src.game.entities.creature import Creature
from src.game.event_registry import register_battle_event
from src.game.game_context import GameContext
from src.game.scenes.base import BaseScene
from src.game.save import DEFAULT_SAVE_ID, register_defeated_enemy
from src.game.settings import SCREEN_HEIGHT, SCREEN_WIDTH
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
        surface.fill((10, 12, 24))
        self._draw_title(surface)
        self._draw_combatants(surface)
        self._draw_log(surface)
        self._draw_menu(surface)
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
        self.dice_frames_remaining = self.DICE_ANIMATION_FRAMES
        self.dice_display_value = 1
        self.turn_state = "rolagem"
        self._add_log(f"{self.character.name} prepara um ataque. Rolando D20...")

    def _resolve_pending_attack(self) -> None:
        if self.pending_attack is None:
            return
        resolution = self.pending_attack
        self.pending_attack = None
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

    def _draw_title(self, surface) -> None:
        title = self._title_font.render(f"Combate Visual - Turno: {self.turn_state}", False, colors.WHITE)
        surface.blit(title, (24, 18))

    def _draw_combatants(self, surface) -> None:
        left = self.pygame.Rect(24, 62, 250, 118)
        right = self.pygame.Rect(SCREEN_WIDTH - 274, 62, 250, 118)
        self._draw_panel(surface, left)
        self._draw_panel(surface, right)
        surface.blit(self._assets.player["right"][0], (left.x + 18, left.y + 44))
        surface.blit(self._assets.creature, (right.x + right.width - 58, right.y + 44))
        self._draw_stats(surface, left, self.character.name, self.character.current_health, self.character.max_health, self.character.armor)
        self._draw_stats(surface, right, self.creature.name, self.creature.current_health, self.creature.max_health, self.creature.armor)

    def _draw_stats(self, surface, rect, name: str, health: int, max_health: int, armor: int) -> None:
        name_surface = self._font.render(name, False, colors.WHITE)
        surface.blit(name_surface, (rect.x + 14, rect.y + 12))
        self._draw_bar(surface, rect.x + 14, rect.y + 38, 130, health, max_health, (114, 207, 142))
        self._draw_bar(surface, rect.x + 14, rect.y + 52, 130, armor, 10, (139, 124, 246))
        health_surface = self._font.render(f"Vida {health}/{max_health}", False, colors.TEXT_MUTED)
        armor_surface = self._font.render(f"Armadura {armor}", False, colors.TEXT_MUTED)
        surface.blit(health_surface, (rect.x + 14, rect.y + 68))
        surface.blit(armor_surface, (rect.x + 14, rect.y + 90))

    def _draw_log(self, surface) -> None:
        rect = self.pygame.Rect(24, 196, SCREEN_WIDTH - 48, 142)
        self._draw_panel(surface, rect)
        for index, line in enumerate(self.log[-5:]):
            text = self._font.render(line, False, colors.WHITE if index == len(self.log[-5:]) - 1 else colors.TEXT_MUTED)
            surface.blit(text, (rect.x + 14, rect.y + 14 + index * 24))

    def _draw_menu(self, surface) -> None:
        rect = self.pygame.Rect(24, SCREEN_HEIGHT - 116, SCREEN_WIDTH - 48, 92)
        self._draw_panel(surface, rect)
        options = tuple(ability.name for ability in self.available_abilities()) if self.mode == "abilities" else self.OPTIONS
        if self.battle_ended:
            options = ("Voltar ao mapa",)
        for index, option in enumerate(options):
            selected = (index == self.ability_index if self.mode == "abilities" else index == self.selected_index) and not self.battle_ended
            prefix = "> " if selected else "  "
            color = colors.WHITE if selected else colors.TEXT_MUTED
            text = self._font.render(f"{prefix}{option}", False, color)
            surface.blit(text, (rect.x + 18 + index * 138, rect.y + 22))
        hint = "Cima/baixo escolhe | Enter/E confirma | ESC fugir"
        if self.pending_attack is not None:
            hint = "Rolando dados..."
        if self.mode == "abilities":
            hint = "Cima/baixo escolhe habilidade | ESC volta"
        if self.battle_ended:
            hint = "Enter/Espaco para voltar ao mapa"
        hint_surface = self._font.render(hint, False, colors.TEXT_MUTED)
        surface.blit(hint_surface, (rect.x + 18, rect.y + 58))

    def _draw_dice_overlay(self, surface) -> None:
        if self.pending_attack is None:
            return
        rect = self.pygame.Rect(SCREEN_WIDTH // 2 - 88, SCREEN_HEIGHT // 2 - 74, 176, 148)
        self._draw_panel(surface, rect)
        title = self._font.render("Rolando D20", False, colors.TEXT_MUTED)
        value = self._title_font.render(str(self.dice_display_value), False, colors.WHITE)
        footer = self._font.render("O dado decide o ataque", False, colors.TEXT_MUTED)
        surface.blit(title, (rect.centerx - title.get_width() // 2, rect.y + 18))
        dice_rect = self.pygame.Rect(rect.centerx - 32, rect.y + 48, 64, 48)
        self.pygame.draw.rect(surface, (28, 24, 42), dice_rect)
        self.pygame.draw.rect(surface, colors.DIALOGUE_BORDER, dice_rect, width=2)
        surface.blit(value, (dice_rect.centerx - value.get_width() // 2, dice_rect.centery - value.get_height() // 2))
        surface.blit(footer, (rect.centerx - footer.get_width() // 2, rect.y + 108))

    def _draw_panel(self, surface, rect) -> None:
        self.pygame.draw.rect(surface, colors.DIALOGUE_BG, rect)
        self.pygame.draw.rect(surface, colors.DIALOGUE_BORDER, rect, width=2)

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


def _damage_roll_text(resolution: AttackResolution) -> str:
    if resolution.damage_roll is None:
        return "Dano: nenhum."
    rolls = "+".join(str(value) for value in resolution.damage_roll.rolls)
    return f"Dano: {resolution.damage_roll.expression} = {rolls} -> {resolution.damage_roll.total}."
