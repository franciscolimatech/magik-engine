"""Overworld scene for the first playable prototype."""

from __future__ import annotations

from src.core.character import get_character
from src.game import assets, colors
from src.game.appearance import appearance_from_notes
from src.game.camera import Camera
from src.game.entities.creature import Creature, load_game_creature
from src.game.entities.npc import NPC
from src.game.entities.player import Player
from src.game.event_registry import register_creature_encounter, register_map_event
from src.game.game_context import GameContext
from src.game.maps.events import MapEvent, find_event_at, load_test_events
from src.game.maps.test_map import (
    find_creatures,
    find_npcs,
    find_player_start,
    is_walkable,
    load_test_map,
    map_height,
    map_width,
)
from src.game.save import (
    DEFAULT_LOCATION_ID,
    DEFAULT_SAVE_ID,
    GameSave,
    load_or_create_default_game_save,
    register_current_location,
    register_triggered_event,
    sync_game_save_context,
    update_player_position,
)
from src.game.scenes.base import BaseScene
from src.game.ui.dialogue_box import DialogueBox
from src.game.ui.hud import HUD
from src.storage.types import JsonStore


class OverworldScene(BaseScene):
    def __init__(self, pygame, context: GameContext | str, storage: JsonStore | None = None) -> None:
        self.pygame = pygame
        self.context = context if isinstance(context, GameContext) else GameContext(player_name=context)
        self.storage = storage
        self.should_quit = False
        self.requested_scene: str | None = None
        self.requested_creature: Creature | None = None
        self.map_data = load_test_map()
        self.game_save = self._load_game_save()
        start_x, start_y = self._starting_position()
        self.player = Player(start_x, start_y, name=self.context.player_name)
        self.npcs = [NPC(item.x, item.y, item.name, item.dialogues, choice=item.choice) for item in find_npcs(self.map_data)]
        self.creatures = [load_game_creature(storage, item.x, item.y) for item in find_creatures(self.map_data)]
        self.events = load_test_events()
        self.triggered_event_ids: set[str] = set(self.game_save.triggered_events if self.game_save else [])
        self.dialogue: DialogueBox | None = None
        self.pending_event: MapEvent | None = None
        self.pending_creature: Creature | None = None
        self.font = pygame.font.Font(None, 24)
        self.camera = Camera()
        self.hud = HUD(
            player_name=self.context.player_name,
            map_name=self.context.map_name,
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
        surface.fill(colors.BLACK)
        for y, row in enumerate(self.map_data):
            for x, tile in enumerate(row):
                screen_x, screen_y = self.camera.tile_to_screen(x, y)
                assets.draw_tile(self.pygame, surface, tile, screen_x, screen_y, self.assets)
        highlighted_npc = self.facing_npc()
        highlighted_creature = self.facing_creature()
        for npc in self.npcs:
            npc.draw(self.pygame, surface, self.camera, self.assets, highlighted=npc == highlighted_npc)
        for creature in self.creatures:
            creature.draw(self.pygame, surface, self.camera, self.assets, highlighted=creature == highlighted_creature)
        self.player.draw(self.pygame, surface, self.camera, self.assets)
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
            return False
        self.dialogue = DialogueBox(npc.name, npc.dialogues, choice=npc.choice)
        return True

    def facing_npc(self) -> NPC | None:
        return next((npc for npc in self.npcs if npc.can_interact(self.player)), None)

    def facing_creature(self) -> Creature | None:
        return next((creature for creature in self.creatures if creature.can_interact(self.player)), None)

    def open_creature_encounter(self, creature: Creature) -> None:
        self.pending_creature = creature
        self.dialogue = DialogueBox(creature.name, creature.encounter_messages(), choice=creature.encounter_choice())

    def trigger_event_at(self, x: int, y: int) -> MapEvent | None:
        event = find_event_at(self.events, x, y)
        if event is None or not event.can_trigger(self.triggered_event_ids):
            return None
        if not event.repeatable:
            self.triggered_event_ids.add(event.id)
        self._persist_triggered_event(event.id)
        self.dialogue = DialogueBox(event.speaker, event.messages, choice=event.choice)
        if event.choice is not None:
            self.pending_event = event
        elif self.storage is not None:
            register_map_event(self.storage, self.context, event, (x, y))
        return event

    def _handle_dialogue_option(self, selected_option) -> None:
        if self.pending_event is not None and self.storage is not None:
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

    def persist_state(self) -> None:
        if self.storage is None:
            return
        try:
            update_player_position(self.storage, DEFAULT_SAVE_ID, self.player.x, self.player.y)
            register_current_location(self.storage, DEFAULT_SAVE_ID, DEFAULT_LOCATION_ID)
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
                location_id=DEFAULT_LOCATION_ID,
            )
            return sync_game_save_context(
                self.storage,
                DEFAULT_SAVE_ID,
                self.context.character_id,
                self.context.campaign_id,
                self.context.campaign_session_id,
                DEFAULT_LOCATION_ID,
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


def load_player_appearance(storage: JsonStore | None, context: GameContext) -> dict[str, str] | None:
    if storage is None:
        return None
    try:
        character = get_character(storage, context.character_id)
    except ValueError:
        return None
    return appearance_from_notes(character.notes)
