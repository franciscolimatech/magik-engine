"""Initial visual battle scene for the 2D prototype."""

from __future__ import annotations

from src.core.character import Character
from src.core.combat import apply_physical_damage, roll_damage
from src.game import assets, colors
from src.game.entities.creature import Creature
from src.game.event_registry import register_battle_event
from src.game.game_context import GameContext
from src.game.scenes.base import BaseScene
from src.game.settings import SCREEN_HEIGHT, SCREEN_WIDTH
from src.storage.types import JsonStore


class BattleScene(BaseScene):
    OPTIONS = ("Atacar", "Observar", "Fugir")

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
        self.log: list[str] = [f"{character.name} encontrou {creature.name}."]
        self.requested_scene: str | None = None
        self.should_quit = False
        self.victory = False
        self._font = None
        self._title_font = None
        self._assets = None
        self._register_battle_event("inicio", f"Combate iniciado contra {creature.name}.")

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
        if self.victory:
            if event.key in {self.pygame.K_RETURN, self.pygame.K_SPACE, self.pygame.K_e}:
                self.requested_scene = "overworld"
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
        return

    def draw(self, surface) -> None:
        self._ensure_draw_resources()
        surface.fill((10, 12, 24))
        self._draw_title(surface)
        self._draw_combatants(surface)
        self._draw_log(surface)
        self._draw_menu(surface)

    def confirm_selection(self) -> None:
        option = self.selected_option
        if option == "Atacar":
            self.attack()
        elif option == "Observar":
            self.observe()
        elif option == "Fugir":
            self.flee()

    def attack(self) -> None:
        if self.victory or self.creature.current_health <= 0:
            return
        damage = roll_damage(max(self.creature.current_health, 1), self.rng).result
        result = apply_physical_damage(self.creature.current_health, self.creature.armor, damage)
        self.creature.current_health = result.current_health
        self.creature.armor = result.armor
        self._add_log(f"{self.character.name} atacou {self.creature.name} e causou {damage} de dano.")
        if self.creature.current_health <= 0:
            self._win()
            return
        self.creature_turn()

    def creature_turn(self) -> None:
        if self.creature.current_health <= 0 or self.character.current_health <= 0:
            return
        damage = roll_damage(max(self.character.current_health, 1), self.rng).result
        result = apply_physical_damage(self.character.current_health, self.character.armor, damage)
        self.character.current_health = result.current_health
        self.character.armor = result.armor
        self._add_log(f"{self.creature.name} atacou {self.character.name} e causou {damage} de dano.")
        if self.character.current_health <= 0:
            self._add_log(f"{self.character.name} caiu. O mestre decide a consequencia.")

    def observe(self) -> None:
        hostile = "hostil" if self.creature.hostile else "nao hostil"
        self._add_log(
            f"{self.creature.description} Vida: {self.creature.current_health}/{self.creature.max_health}. "
            f"Armadura: {self.creature.armor}. Estado: {hostile}."
        )

    def flee(self) -> None:
        self._add_log(f"{self.character.name} fugiu do encontro com {self.creature.name}.")
        self._register_battle_event("fuga", f"{self.character.name} fugiu de {self.creature.name}.")
        self.requested_scene = "overworld"

    def _win(self) -> None:
        self.victory = True
        self._add_log(f"Vitoria! {self.creature.name} foi derrotada.")
        self._add_log("Pressione Enter ou Espaco para voltar ao mapa.")
        self._register_battle_event("vitoria", f"{self.creature.name} foi derrotada.")

    def _add_log(self, text: str) -> None:
        self.log.append(text)
        if len(self.log) > 6:
            self.log = self.log[-6:]

    def _register_battle_event(self, event_name: str, detail: str) -> None:
        if self.storage is None:
            return
        register_battle_event(self.storage, self.context, self.creature, self.creature.position, event_name, detail)

    def _ensure_draw_resources(self) -> None:
        if self._font is not None:
            return
        self._font = self.pygame.font.Font(None, 24)
        self._title_font = self.pygame.font.Font(None, 34)
        self._assets = assets.create_assets(self.pygame)

    def _draw_title(self, surface) -> None:
        title = self._title_font.render("Combate Visual Inicial", False, colors.WHITE)
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
        self._draw_bar(surface, rect.x + 14, rect.y + 40, 130, health, max_health, (114, 207, 142))
        health_surface = self._font.render(f"Vida {health}/{max_health}", False, colors.TEXT_MUTED)
        armor_surface = self._font.render(f"Armadura {armor}", False, colors.TEXT_MUTED)
        surface.blit(health_surface, (rect.x + 14, rect.y + 62))
        surface.blit(armor_surface, (rect.x + 14, rect.y + 84))

    def _draw_log(self, surface) -> None:
        rect = self.pygame.Rect(24, 196, SCREEN_WIDTH - 48, 142)
        self._draw_panel(surface, rect)
        for index, line in enumerate(self.log[-5:]):
            text = self._font.render(line, False, colors.WHITE if index == len(self.log[-5:]) - 1 else colors.TEXT_MUTED)
            surface.blit(text, (rect.x + 14, rect.y + 14 + index * 24))

    def _draw_menu(self, surface) -> None:
        rect = self.pygame.Rect(24, SCREEN_HEIGHT - 116, SCREEN_WIDTH - 48, 92)
        self._draw_panel(surface, rect)
        for index, option in enumerate(self.OPTIONS):
            selected = index == self.selected_index and not self.victory
            prefix = "> " if selected else "  "
            color = colors.WHITE if selected else colors.TEXT_MUTED
            text = self._font.render(f"{prefix}{option}", False, color)
            surface.blit(text, (rect.x + 18 + index * 160, rect.y + 22))
        hint = "Cima/baixo escolhe | Enter/E confirma | ESC fugir"
        if self.victory:
            hint = "Enter/Espaco para voltar ao mapa"
        hint_surface = self._font.render(hint, False, colors.TEXT_MUTED)
        surface.blit(hint_surface, (rect.x + 18, rect.y + 58))

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
