"""Overworld scene for the first playable prototype."""

from __future__ import annotations

from typing import Any

from src.ai.narrator import AIConfig
from src.core.character import get_character
from src.core.lore import get_lore_summary_for_location
from src.game import assets, colors
from src.game.appearance import appearance_from_notes
from src.game.ai_narration import (
    GameNarrationResult,
    GameNarrator,
    is_game_ai_narration_enabled,
    narrate_game_text,
)
from src.game.camera import Camera
from src.game.entities.creature import Creature, load_game_creature
from src.game.entities.npc import NPC
from src.game.entities.player import Player
from src.game.event_registry import register_creature_encounter, register_map_event
from src.game.game_context import GameContext
from src.game.maps.area_registry import (
    DEFAULT_AREA_ID,
    AreaTransition,
    GameArea,
    find_transition_at,
    get_spawn,
    resolve_area,
)
from src.game.maps.events import MapEvent, find_event_at
from src.game.maps.test_map import (
    find_creatures,
    find_npcs,
    find_player_start,
    is_walkable,
    map_height,
    map_width,
)
from src.game.narrative_conditions import apply_narrative_effects_to_storage, conditions_met
from src.game.npc_reactions import (
    apply_npc_interaction_effects_to_storage,
    get_npc_dialogue_for_state,
)
from src.game.settings import TILE_SIZE
from src.game.save import (
    DEFAULT_LOCATION_ID,
    DEFAULT_SAVE_ID,
    GameSave,
    get_game_save,
    load_or_create_default_game_save,
    register_current_location,
    register_triggered_event,
    sync_game_save_context,
    update_area_and_player_position,
    update_player_position,
)
from src.game.scenes.base import BaseScene
from src.game.ui.dialogue_box import DialogueBox
from src.game.ui.hud import HUD
from src.storage.types import JsonStore


SHADOW_OBSERVE_EVENT_ID = "evento-sombra-observa"


class OverworldScene(BaseScene):
    def __init__(
        self,
        pygame,
        context: GameContext | str,
        storage: JsonStore | None = None,
        *,
        ai_narrator: GameNarrator | None = None,
        ai_config: AIConfig | None = None,
        ai_narration_enabled: bool | None = None,
    ) -> None:
        self.pygame = pygame
        self.context = context if isinstance(context, GameContext) else GameContext(player_name=context)
        self.storage = storage
        self.ai_narrator = ai_narrator
        self.ai_config = ai_config
        self.ai_narration_enabled = (
            is_game_ai_narration_enabled() if ai_narration_enabled is None else ai_narration_enabled
        )
        self.last_ai_narration_result: GameNarrationResult | None = None
        self.should_quit = False
        self.requested_scene: str | None = None
        self.requested_creature: Creature | None = None
        self.location_id = self._resolve_location_id()
        self.game_save = self._load_game_save()
        self.area = self._resolve_area()
        self.area_id = self.area.id
        self.lore_summary = self._load_lore_summary(self.location_id)
        self.location_display_name = self._location_display_name()
        self._load_area_content(self.area)
        start_x, start_y = self._starting_position()
        self.player = Player(start_x, start_y, name=self.context.player_name)
        self.triggered_event_ids: set[str] = set(self.game_save.triggered_events if self.game_save else [])
        self.dialogue: DialogueBox | None = None
        self.pending_event: MapEvent | None = None
        self.pending_creature: Creature | None = None
        self.font = pygame.font.Font(None, 24)
        self.camera = Camera()
        self.hud = HUD(
            player_name=self.context.player_name,
            map_name=self.location_display_name,
            campaign_label=self.context.campaign_label,
            session_label=self.context.session_label,
        )
        self.player_appearance = load_player_appearance(storage, self.context)
        self.assets = assets.create_assets(pygame, player_appearance=self.player_appearance)
        self.camera.follow(self.player.x, self.player.y, map_width(self.map_data), map_height(self.map_data))
        self.persist_state()

    def handle_event(self, event) -> None:
        if event.type != self.pygame.KEYDOWN:
            return
        if event.key == self.pygame.K_ESCAPE:
            self.persist_state()
            self.should_quit = True
            return
        if self.dialogue and self.dialogue.visible:
            selected_option = self.dialogue.handle_key(self.pygame, event.key)
            if selected_option is not None:
                self._handle_dialogue_option(selected_option)
            return
        movement = self._movement_for_key(event.key)
        if movement is not None:
            self.try_move_player(movement[0], movement[1])
            return
        if event.key in {self.pygame.K_SPACE, self.pygame.K_e}:
            self.interact()

    def update(self) -> None:
        if self.dialogue and not self.dialogue.visible:
            self.dialogue = None
            self.pending_event = None
            self.pending_creature = None
        self.camera.follow(self.player.x, self.player.y, map_width(self.map_data), map_height(self.map_data))

    def consume_requested_scene(self) -> str | None:
        requested = self.requested_scene
        self.requested_scene = None
        return requested

    def consume_requested_creature(self) -> Creature | None:
        creature = self.requested_creature
        self.requested_creature = None
        return creature

    def draw(self, surface) -> None:
        self._sync_camera_to_surface(surface)
        surface.fill(colors.BLACK)
        for y, row in enumerate(self.map_data):
            for x, tile in enumerate(row):
                screen_x, screen_y = self.camera.tile_to_screen(x, y)
                assets.draw_tile(self.pygame, surface, tile, screen_x, screen_y, self.assets, size=self.camera.tile_size)
        self._draw_area_transitions(surface)
        highlighted_npc = self.facing_npc()
        highlighted_creature = self.facing_creature()
        for npc in self.npcs:
            npc.draw(self.pygame, surface, self.camera, self.assets, highlighted=npc == highlighted_npc)
        for creature in self.creatures:
            creature.draw(self.pygame, surface, self.camera, self.assets, highlighted=creature == highlighted_creature)
        self.player.draw(self.pygame, surface, self.camera, self.assets)
        self._refresh_hud()
        self.hud.draw(self.pygame, surface, self.font)
        if self.dialogue:
            self.dialogue.draw(self.pygame, surface, self.font)

    def try_move_player(self, dx: int, dy: int) -> bool:
        if self.dialogue and self.dialogue.visible:
            return False
        moved = self.player.move(dx, dy, self.map_data)
        if moved:
            self.persist_state()
            self.trigger_event_at(self.player.x, self.player.y)
        return moved

    def interact(self) -> bool:
        creature = self.facing_creature()
        if creature is not None:
            self.open_creature_encounter(creature)
            return True
        npc = self.facing_npc()
        if npc is None:
            return self._try_area_transition()
        self.dialogue = DialogueBox(npc.name, self._dialogues_for_npc(npc), choice=npc.choice)
        self._apply_npc_interaction_effects(npc)
        return True

    def facing_npc(self) -> NPC | None:
        return next((npc for npc in self.npcs if npc.can_interact(self.player)), None)

    def facing_creature(self) -> Creature | None:
        return next((creature for creature in self.creatures if creature.can_interact(self.player)), None)

    def current_transition(self) -> AreaTransition | None:
        return find_transition_at(self.area, self.player.x, self.player.y)

    def open_creature_encounter(self, creature: Creature) -> None:
        self.pending_creature = creature
        self.dialogue = DialogueBox(creature.name, creature.encounter_messages(), choice=creature.encounter_choice())

    def trigger_event_at(self, x: int, y: int) -> MapEvent | None:
        event = find_event_at(self.events, x, y)
        if event is None or not self._event_can_run_here(event) or not event.can_trigger(self.triggered_event_ids):
            return None
        if not event.repeatable:
            self.triggered_event_ids.add(event.id)
        self._persist_triggered_event(event.id)
        self.dialogue = DialogueBox(event.speaker, self._messages_for_event(event), choice=event.choice)
        if event.choice is not None:
            self.pending_event = event
        elif self.storage is not None:
            self._apply_narrative_event_effects(event)
            register_map_event(self.storage, self.context, event, (x, y))
        return event

    def _handle_dialogue_option(self, selected_option) -> None:
        if self.pending_event is not None and self.storage is not None:
            self._apply_narrative_event_effects(self.pending_event, selected_option)
            register_map_event(
                self.storage,
                self.context,
                self.pending_event,
                (self.player.x, self.player.y),
                selected_option=selected_option,
            )
            self.pending_event = None
        if self.pending_creature is not None:
            creature = self.pending_creature
            if self.storage is not None:
                register_creature_encounter(
                    self.storage,
                    self.context,
                    creature,
                    creature.position,
                    selected_option=selected_option,
                )
            if selected_option.event == "retreat" and self.dialogue is not None:
                self.dialogue.close()
            elif selected_option.event == "start_combat":
                self.requested_scene = "battle"
                self.requested_creature = creature
                if self.dialogue is not None:
                    self.dialogue.close()
            self.pending_creature = None

    def _movement_for_key(self, key: int) -> tuple[int, int] | None:
        keys = self.pygame
        if key in {keys.K_LEFT, keys.K_a}:
            return (-1, 0)
        if key in {keys.K_RIGHT, keys.K_d}:
            return (1, 0)
        if key in {keys.K_UP, keys.K_w}:
            return (0, -1)
        if key in {keys.K_DOWN, keys.K_s}:
            return (0, 1)
        return None

    def _event_can_run_here(self, event: MapEvent) -> bool:
        if event.location_id is not None and event.location_id != self.location_id:
            return False
        if not event.narrative_conditions:
            return True
        save = self._current_game_save()
        if save is None:
            return False
        return conditions_met(save, event.narrative_conditions)

    def _apply_narrative_event_effects(self, event: MapEvent, selected_option=None) -> None:
        if self.storage is None or not event.narrative_effects:
            return
        effects = _effects_for_selected_option(event.narrative_effects, selected_option)
        try:
            self.game_save = apply_narrative_effects_to_storage(self.storage, DEFAULT_SAVE_ID, effects)
        except Exception as exc:  # noqa: BLE001 - narrative state must not crash exploration.
            print(f"[MAGIK Game] Nao foi possivel aplicar efeito narrativo: {exc}")

    def _messages_for_event(self, event: MapEvent) -> tuple[str, ...]:
        if event.id != SHADOW_OBSERVE_EVENT_ID:
            return event.messages
        if not self.ai_narration_enabled:
            self.last_ai_narration_result = GameNarrationResult(
                text=event.text,
                source="disabled",
                used_ai=False,
                diagnostic="game_ai_narration_disabled",
            )
            return event.messages
        result = narrate_game_text(
            fallback_text=event.text,
            context=self._safe_ai_context_for_event(event),
            config=self.ai_config,
            narrator=self.ai_narrator,
        )
        self.last_ai_narration_result = result
        if result.used_ai:
            return (result.text,)
        return event.messages

    def _safe_ai_context_for_event(self, event: MapEvent) -> dict[str, Any]:
        save = self._current_game_save()
        return {
            "location_id": self.location_id,
            "location_name": self.location_display_name,
            "event_id": event.id,
            "story_flags": list(save.story_flags if save else []),
            "world_flags": list(save.world_flags if save else []),
            "decided_consequence": _event_decided_consequence(event),
            "tone": "sombrio, misterioso, curto",
        }

    def _current_game_save(self) -> GameSave | None:
        if self.storage is None:
            return self.game_save
        try:
            self.game_save = get_game_save(self.storage, DEFAULT_SAVE_ID)
            return self.game_save
        except Exception:
            return self.game_save

    def _dialogues_for_npc(self, npc: NPC) -> tuple[str, ...]:
        return get_npc_dialogue_for_state(npc, self._current_game_save(), self.context.with_location(self.location_id))

    def _apply_npc_interaction_effects(self, npc: NPC) -> None:
        if self.storage is None:
            return
        try:
            self.game_save = apply_npc_interaction_effects_to_storage(
                self.storage,
                npc,
                self.context.with_location(self.location_id),
            )
        except Exception as exc:  # noqa: BLE001 - NPC memory must not crash interaction.
            print(f"[MAGIK Game] Nao foi possivel salvar memoria do NPC: {exc}")

    def persist_state(self) -> None:
        if self.storage is None:
            return
        try:
            update_player_position(self.storage, DEFAULT_SAVE_ID, self.player.x, self.player.y)
            register_current_location(self.storage, DEFAULT_SAVE_ID, self.location_id)
            self.game_save = update_area_and_player_position(
                self.storage,
                DEFAULT_SAVE_ID,
                self.area_id,
                self.player.x,
                self.player.y,
                location_id=self.location_id,
            )
        except Exception as exc:  # noqa: BLE001 - save failures must not crash the prototype.
            print(f"[MAGIK Game] Nao foi possivel salvar progresso do jogo: {exc}")

    def _load_game_save(self) -> GameSave | None:
        if self.storage is None:
            return None
        try:
            save = load_or_create_default_game_save(
                self.storage,
                character_id=self.context.character_id,
                campaign_id=self.context.campaign_id,
                session_id=self.context.campaign_session_id,
                location_id=self.location_id,
                area_id=self.context.area_id,
            )
            return sync_game_save_context(
                self.storage,
                DEFAULT_SAVE_ID,
                self.context.character_id,
                self.context.campaign_id,
                self.context.campaign_session_id,
                self.location_id,
                area_id=save.area_id,
            )
        except Exception as exc:  # noqa: BLE001 - save failures must not block the game.
            print(f"[MAGIK Game] Nao foi possivel carregar save do jogo: {exc}")
            return None

    def _starting_position(self) -> tuple[int, int]:
        default_position = find_player_start(self.map_data)
        if self.game_save is None:
            return default_position
        x, y = self.game_save.position
        if is_walkable(self.map_data, x, y):
            return x, y
        return default_position

    def _persist_triggered_event(self, event_id: str) -> None:
        if self.storage is None:
            return
        try:
            register_triggered_event(self.storage, DEFAULT_SAVE_ID, event_id)
        except Exception as exc:  # noqa: BLE001 - save failures must not block event display.
            print(f"[MAGIK Game] Nao foi possivel salvar evento disparado: {exc}")

    def _resolve_location_id(self) -> str:
        location_id = self.context.location_id.strip() or DEFAULT_LOCATION_ID
        if self.storage is None:
            return location_id if location_id == DEFAULT_LOCATION_ID else DEFAULT_LOCATION_ID
        if self._load_lore_summary(location_id) is not None:
            return location_id
        return DEFAULT_LOCATION_ID

    def _resolve_area(self) -> GameArea:
        if self.game_save is not None:
            return resolve_area(self.game_save.area_id)
        return resolve_area(self.context.area_id)

    def _load_area_content(self, area: GameArea) -> None:
        self.map_data = list(area.map_data)
        self.npcs = [
            NPC(
                item.x,
                item.y,
                item.name,
                item.dialogues,
                choice=item.choice,
                npc_id=item.npc_id,
                location_id=item.location_id,
            )
            for item in find_npcs(self.map_data)
        ]
        self.creatures = [load_game_creature(self.storage, item.x, item.y) for item in find_creatures(self.map_data)]
        self.events = list(area.events)

    def _try_area_transition(self) -> bool:
        transition = self.current_transition()
        if transition is None:
            return False
        self._apply_area_transition(transition)
        return True

    def _apply_area_transition(self, transition: AreaTransition) -> None:
        target_area = resolve_area(transition.target_area_id)
        spawn = get_spawn(target_area, transition.target_spawn_id)
        self.area = target_area
        self.area_id = target_area.id
        self.location_id = transition.target_location_id or self.location_id
        self.lore_summary = self._load_lore_summary(self.location_id)
        self.location_display_name = self._location_display_name()
        self._load_area_content(target_area)
        self.player.x, self.player.y = spawn.position
        self.context = self.context.with_location(self.location_id).with_area(self.area_id)
        self.hud = HUD(
            player_name=self.context.player_name,
            map_name=self.location_display_name,
            campaign_label=self.context.campaign_label,
            session_label=self.context.session_label,
        )
        self.dialogue = None
        self.pending_event = None
        self.pending_creature = None
        self.persist_state()

    def _draw_area_transitions(self, surface) -> None:
        current_transition = self.current_transition()
        for transition in self.area.transitions:
            self._draw_transition_marker(surface, self.transition_marker_rect(transition), highlighted=transition == current_transition)

    def transition_marker_rect(self, transition: AreaTransition):
        screen_x, screen_y = self.camera.tile_to_screen(transition.x, transition.y)
        size = self.camera.tile_size
        pad = max(3, size // 8)
        return self.pygame.Rect(screen_x + pad, screen_y + pad, size - pad * 2, size - pad * 2)

    def _draw_transition_marker(self, surface, rect, *, highlighted: bool = False) -> None:
        pad = max(3, self.camera.tile_size // 8)
        arch_color = (148, 120, 68) if not highlighted else (220, 177, 83)
        glow_color = (84, 62, 128) if not highlighted else (118, 91, 168)
        inner_color = (20, 18, 34)
        self.pygame.draw.rect(surface, glow_color, rect, width=max(1, self.camera.tile_size // 16), border_radius=max(2, self.camera.tile_size // 10))
        self.pygame.draw.arc(surface, arch_color, rect, 0, 3.14, max(2, self.camera.tile_size // 14))
        door = self.pygame.Rect(rect.x + rect.width // 3, rect.y + rect.height // 3, max(2, rect.width // 3), max(2, rect.height // 2))
        self.pygame.draw.rect(surface, inner_color, door)
        self.pygame.draw.line(surface, arch_color, (rect.centerx, rect.y + rect.height // 4), (rect.centerx, rect.bottom - pad), width=max(1, self.camera.tile_size // 18))

    def _refresh_hud(self) -> None:
        self.hud = HUD(
            player_name=self.context.player_name,
            map_name=self.location_display_name,
            campaign_label=self.context.campaign_label,
            session_label=self.context.session_label,
            controls_hint=self._current_controls_hint(),
        )

    def _current_controls_hint(self) -> str:
        transition = self.current_transition()
        if transition is None:
            return "WASD/setas mover | E/espaco interagir | ESC sair"
        target_area = resolve_area(transition.target_area_id)
        return f"E atravessar para {target_area.name} | ESC sair"

    def _load_lore_summary(self, location_id: str) -> dict[str, Any] | None:
        if self.storage is None:
            return None
        try:
            return get_lore_summary_for_location(self.storage, location_id)
        except ValueError:
            return None

    def _location_display_name(self) -> str:
        if not self.lore_summary:
            return self.context.map_name
        location = self.lore_summary.get("location")
        if isinstance(location, dict):
            return str(location.get("name") or self.context.map_name)
        return self.context.map_name

    def _sync_camera_to_surface(self, surface) -> None:
        visual_tile_size = calculate_overworld_tile_size(
            surface.get_width(),
            surface.get_height(),
            map_width(self.map_data),
            map_height(self.map_data),
        )
        self.camera.resize(surface.get_width(), surface.get_height(), visual_tile_size)
        self.camera.follow(self.player.x, self.player.y, map_width(self.map_data), map_height(self.map_data))


def load_player_appearance(storage: JsonStore | None, context: GameContext) -> dict[str, str] | None:
    if storage is None:
        return None
    try:
        character = get_character(storage, context.character_id)
    except ValueError:
        return None
    return appearance_from_notes(character.notes)


def calculate_overworld_tile_size(
    screen_width: int,
    screen_height: int,
    map_tiles_width: int,
    map_tiles_height: int,
    base_tile_size: int = TILE_SIZE,
) -> int:
    if screen_width <= 0 or screen_height <= 0 or map_tiles_width <= 0 or map_tiles_height <= 0:
        return base_tile_size
    width_fit = screen_width // map_tiles_width
    height_fit = screen_height // map_tiles_height
    fitted_tile_size = min(width_fit, height_fit)
    return max(base_tile_size, fitted_tile_size)


def _effects_for_selected_option(effects: dict[str, Any], selected_option=None) -> dict[str, Any]:
    if selected_option is None:
        return dict(effects)
    resolved_effects = dict(effects)
    important_choice = resolved_effects.get("important_choice")
    if isinstance(important_choice, dict):
        choice_payload = dict(important_choice)
        choice_payload["choice"] = selected_option.text
        resolved_effects["important_choice"] = choice_payload
    return resolved_effects


def _event_decided_consequence(event: MapEvent) -> str:
    consequence = event.narrative_effects.get("narrative_consequence")
    if isinstance(consequence, dict):
        return str(consequence.get("text") or "")
    return ""
