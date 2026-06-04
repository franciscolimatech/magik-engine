from src.core.character import Character, create_miko_meu
from src.core.campaigns import create_campaign, create_campaign_session, get_campaign_session
from src.core.session import list_events
from src.game.assets import create_assets
from src.game.app import _max_frames_from_env, load_player_name
from src.game.camera import Camera
from src.game.entities.npc import NPC
from src.game.entities.player import Player
from src.game.event_registry import register_map_event
from src.game.game_context import GameContext
from src.game.maps.events import MapEvent, find_event_at
from src.game.maps.test_map import (
    find_npcs,
    find_player_start,
    is_obstacle,
    is_walkable,
    load_test_map,
    map_height,
    map_width,
)
from src.game.scenes.main_menu import MainMenuScene
from src.game.ui.dialogue_box import DialogueBox, wrap_text
from src.game.ui.hud import HUD
from src.storage.memory import MemoryStorage


class FakePygame:
    KEYDOWN = 1
    K_DOWN = 2
    K_s = 3
    K_UP = 4
    K_w = 5
    K_RETURN = 6
    K_SPACE = 7
    K_ESCAPE = 8
    K_e = 9


class FakeEvent:
    def __init__(self, key: int) -> None:
        self.type = FakePygame.KEYDOWN
        self.key = key


def test_test_map_loads_with_player_start() -> None:
    map_data = load_test_map()

    assert map_data
    assert find_player_start(map_data) == (5, 4)
    assert map_width(map_data) > 20
    assert map_height(map_data) > 15


def test_test_map_loads_npcs() -> None:
    npcs = find_npcs(load_test_map())

    assert len(npcs) >= 1
    assert npcs[0].name
    assert npcs[0].dialogues


def test_generated_assets_include_tiles_and_sprites() -> None:
    import pygame

    pygame.init()
    assets = create_assets(pygame)

    assert assets.wall_tile.get_size() == (32, 32)
    assert assets.water_tile.get_size() == (32, 32)
    assert assets.floor_tiles["g"].get_size() == (32, 32)
    assert assets.npc.get_size() == (32, 32)
    assert assets.interaction_marker.get_width() > 0
    pygame.quit()


def test_player_sprites_exist_for_each_direction() -> None:
    import pygame

    pygame.init()
    assets = create_assets(pygame)

    assert set(assets.player) == {"up", "down", "left", "right"}
    assert all(len(frames) == 2 for frames in assets.player.values())
    assert all(frame.get_size() == (32, 32) for frames in assets.player.values() for frame in frames)
    pygame.quit()


def test_collision_blocks_wall() -> None:
    map_data = load_test_map()

    assert is_obstacle(map_data, 0, 0) is True
    player = Player(1, 1)

    moved = player.move(-1, 0, map_data)

    assert moved is False
    assert player.position == (1, 1)
    assert player.direction == "left"


def test_valid_movement_changes_position() -> None:
    map_data = load_test_map()
    player = Player(1, 1)

    moved = player.move(1, 0, map_data)

    assert moved is True
    assert player.position == (2, 1)
    assert player.direction == "right"
    assert player.walk_frame == 1


def test_floor_and_grass_are_walkable_but_water_blocks() -> None:
    map_data = [
        "######",
        "#.g?w#",
        "######",
    ]

    assert is_walkable(map_data, 1, 1) is True
    assert is_walkable(map_data, 2, 1) is True
    assert is_walkable(map_data, 3, 1) is True
    assert is_obstacle(map_data, 4, 1) is True


def test_player_cannot_leave_map() -> None:
    map_data = load_test_map()
    player = Player(0, 0)

    moved = player.move(-1, 0, map_data)

    assert moved is False
    assert player.position == (0, 0)


def test_npc_does_not_interact_by_adjacency_only() -> None:
    player = Player(2, 2)
    npc = NPC(3, 2, "Guarda", "Ola.")

    assert npc.is_adjacent_to(player) is True
    assert npc.can_interact(player) is False


def test_npc_detects_player_facing_it() -> None:
    player = Player(2, 2, direction="up")
    npc = NPC(2, 1, "Guarda", "Ola.")

    assert npc.is_in_front_of(player) is True
    assert npc.can_interact(player) is True


def test_dialogue_box_keeps_speaker_name() -> None:
    dialogue = DialogueBox("Guarda", "Ola.")

    assert dialogue.speaker == "Guarda"
    assert dialogue.visible is True


def test_npc_accepts_multiple_dialogues() -> None:
    npc = NPC(1, 1, "Velho", ["Primeira fala.", "Segunda fala."])

    assert npc.dialogue == "Primeira fala."
    assert npc.dialogues == ("Primeira fala.", "Segunda fala.")


def test_dialogue_advances_and_closes_after_last_line() -> None:
    dialogue = DialogueBox("Velho", ["Uma.", "Duas."])

    assert dialogue.current_text == "Uma."
    assert dialogue.advance() is True
    assert dialogue.current_text == "Duas."
    assert dialogue.advance() is False
    assert dialogue.visible is False


def test_wrap_text_returns_multiple_lines_for_long_text() -> None:
    class FakeFont:
        def size(self, text: str) -> tuple[int, int]:
            return len(text) * 8, 12

    lines = wrap_text("A Floresta do Avesso escuta quem fala sozinho.", FakeFont(), max_width=120)

    assert len(lines) > 1


def test_player_facing_position_uses_direction() -> None:
    player = Player(4, 5, direction="left")

    assert player.facing_position() == (3, 5)


def test_camera_centers_and_converts_world_to_screen() -> None:
    camera = Camera(screen_width=320, screen_height=240, tile_size=32)

    camera.follow(10, 8, map_width=30, map_height=25)

    assert camera.offset_x == 176
    assert camera.offset_y == 152
    assert camera.tile_to_screen(10, 8) == (144, 104)


def test_camera_clamps_to_map_bounds() -> None:
    camera = Camera(screen_width=640, screen_height=480, tile_size=32)

    camera.follow(0, 0, map_width=32, map_height=22)
    assert camera.offset_x == 0
    assert camera.offset_y == 0

    camera.follow(31, 21, map_width=32, map_height=22)
    assert camera.offset_x == 384
    assert camera.offset_y == 224


def test_hud_can_be_instantiated() -> None:
    hud = HUD(player_name="Miko Meu")

    assert hud.player_name == "Miko Meu"
    assert hud.map_name == "Mapa de Teste"
    assert hud.campaign_label == "Sem campanha ativa"


def test_hud_shows_campaign_and_session_labels() -> None:
    hud = HUD(player_name="Miko Meu", campaign_label="Campanha: estrada", session_label="Sessao: estrada-sessao-1")

    assert hud._campaign_text() == "Campanha: estrada | Sessao: estrada-sessao-1"


def test_main_menu_scene_instantiates_without_error() -> None:
    scene = MainMenuScene(FakePygame, GameContext(player_name="Miko Meu"))

    assert scene.selected_option == "Iniciar jogo"
    assert scene.mode == "main"


def test_main_menu_starts_with_start_game_selected() -> None:
    scene = MainMenuScene(FakePygame, GameContext(player_name="Miko Meu"))

    assert scene.selected_index == 0
    assert scene.selected_option == "Iniciar jogo"


def test_main_menu_navigation_down_changes_option() -> None:
    scene = MainMenuScene(FakePygame, GameContext(player_name="Miko Meu"))

    scene.handle_event(FakeEvent(FakePygame.K_DOWN))

    assert scene.selected_option == "Ver contexto"


def test_main_menu_navigation_up_wraps_to_exit() -> None:
    scene = MainMenuScene(FakePygame, GameContext(player_name="Miko Meu"))

    scene.handle_event(FakeEvent(FakePygame.K_UP))

    assert scene.selected_option == "Sair"


def test_main_menu_start_game_requests_overworld() -> None:
    scene = MainMenuScene(FakePygame, GameContext(player_name="Miko Meu"))

    scene.handle_event(FakeEvent(FakePygame.K_RETURN))

    assert scene.consume_requested_scene() == "overworld"
    assert scene.consume_requested_scene() is None


def test_main_menu_exit_requests_quit() -> None:
    scene = MainMenuScene(FakePygame, GameContext(player_name="Miko Meu"))
    scene.selected_index = 3

    scene.handle_event(FakeEvent(FakePygame.K_RETURN))

    assert scene.should_quit is True


def test_main_menu_context_lines_show_context() -> None:
    context = GameContext(
        character_id="miko-meu",
        player_name="Miko Meu",
        campaign_id="estrada",
        campaign_session_id="estrada-sessao-1",
        map_name="Mapa de Teste",
    )
    scene = MainMenuScene(FakePygame, context)

    lines = scene.context_lines()

    assert "Personagem: Miko Meu" in lines
    assert "Campaign ID: estrada" in lines
    assert "Session ID: estrada-sessao-1" in lines
    assert "Status: Com campanha ativa" in lines


def test_main_menu_controls_lines_show_commands() -> None:
    scene = MainMenuScene(FakePygame, GameContext(player_name="Miko Meu"))

    lines = scene.controls_lines()

    assert "WASD/setas: mover" in lines
    assert "E/Espaco: interagir" in lines
    assert "ESC: voltar/sair" in lines


def test_max_frames_from_env_still_supports_smoke_test(monkeypatch) -> None:
    monkeypatch.setenv("MAGIK_GAME_MAX_FRAMES", "3")

    assert _max_frames_from_env() == 3


def test_scene_style_movement_blocks_during_dialogue() -> None:
    class SceneLike:
        player = Player(1, 1)
        map_data = load_test_map()
        dialogue = DialogueBox("NPC", "Ola.")

        def try_move_player(self, dx: int, dy: int) -> bool:
            if self.dialogue and self.dialogue.visible:
                return False
            return self.player.move(dx, dy, self.map_data)

    scene = SceneLike()

    assert scene.try_move_player(1, 0) is False
    assert scene.player.position == (1, 1)


def test_map_event_triggers_when_entering_tile() -> None:
    event = MapEvent("pressagio", 2, 1, "pressagio", ("Algo se mexe.",))
    triggered: set[str] = set()

    found = find_event_at([event], 2, 1)

    assert found is event
    assert found.can_trigger(triggered) is True


def test_unique_map_event_does_not_trigger_twice() -> None:
    event = MapEvent("pressagio", 2, 1, "pressagio", ("Algo se mexe.",), repeatable=False)
    triggered = {"pressagio"}

    assert event.can_trigger(triggered) is False


def test_repeatable_map_event_can_trigger_more_than_once() -> None:
    event = MapEvent("placa", 2, 1, "mensagem", ("Leia de novo.",), repeatable=True)
    triggered = {"placa"}

    assert event.can_trigger(triggered) is True


def test_scene_style_unique_event_opens_dialogue_once() -> None:
    class SceneLike:
        events = [MapEvent("pressagio", 2, 1, "pressagio", ("Algo se mexe.",), repeatable=False)]
        triggered_event_ids: set[str] = set()
        dialogue = None

        def trigger_event_at(self, x: int, y: int):
            event = find_event_at(self.events, x, y)
            if event is None or not event.can_trigger(self.triggered_event_ids):
                return None
            if not event.repeatable:
                self.triggered_event_ids.add(event.id)
            self.dialogue = DialogueBox(event.speaker, event.messages)
            return event

    scene = SceneLike()

    assert scene.trigger_event_at(2, 1) is not None
    assert scene.dialogue.current_text == "Algo se mexe."
    scene.dialogue = None
    assert scene.trigger_event_at(2, 1) is None
    assert scene.dialogue is None


def test_scene_style_repeatable_event_opens_more_than_once() -> None:
    class SceneLike:
        events = [MapEvent("placa", 2, 1, "mensagem", ("Leia de novo.",), repeatable=True)]
        triggered_event_ids: set[str] = set()
        dialogue = None

        def trigger_event_at(self, x: int, y: int):
            event = find_event_at(self.events, x, y)
            if event is None or not event.can_trigger(self.triggered_event_ids):
                return None
            self.dialogue = DialogueBox(event.speaker, event.messages)
            return event

    scene = SceneLike()

    assert scene.trigger_event_at(2, 1) is not None
    scene.dialogue = None
    assert scene.trigger_event_at(2, 1) is not None


def test_load_player_name_uses_miko_when_available() -> None:
    storage = MemoryStorage({"characters.json": {"characters": [create_miko_meu().to_dict()]}})

    assert load_player_name(storage) == "Miko Meu"


def test_load_player_name_uses_fallback_without_miko() -> None:
    other = Character(
        id="lia",
        name="Lia",
        character_class="Guardia",
        max_health=20,
        current_health=20,
        armor=2,
    )
    storage = MemoryStorage({"characters.json": {"characters": [other.to_dict()]}})

    assert load_player_name(storage) == "Aventureiro"


def test_game_context_loads_defaults_without_environment() -> None:
    storage = MemoryStorage({"characters.json": {"characters": [create_miko_meu().to_dict()]}})

    context = GameContext.from_env(env={}, storage=storage)

    assert context.character_id == "miko-meu"
    assert context.campaign_id is None
    assert context.campaign_session_id is None
    assert context.player_name == "Miko Meu"
    assert context.campaign_label == "Sem campanha ativa"


def test_game_context_reads_environment_values() -> None:
    storage = MemoryStorage({"characters.json": {"characters": [create_miko_meu().to_dict()]}})

    context = GameContext.from_env(
        env={
            "MAGIK_GAME_CHARACTER_ID": "miko-meu",
            "MAGIK_GAME_CAMPAIGN_ID": "estrada",
            "MAGIK_GAME_SESSION_ID": "estrada-sessao-1",
        },
        storage=storage,
    )

    assert context.character_id == "miko-meu"
    assert context.campaign_id == "estrada"
    assert context.campaign_session_id == "estrada-sessao-1"
    assert context.has_campaign_session is True


def test_map_event_without_campaign_does_not_attempt_registration() -> None:
    storage = MemoryStorage()
    context = GameContext(player_name="Miko Meu")
    event = MapEvent("pressagio", 2, 1, "pressagio", ("Algo se mexe.",))

    def fail_if_called(*args) -> object:
        raise AssertionError("registrar should not be called")

    assert register_map_event(storage, context, event, (2, 1), registrar=fail_if_called) is False


def test_map_event_with_campaign_session_registers_in_core_history() -> None:
    storage = MemoryStorage()
    campaign = create_campaign(storage, "Estrada do Viajante")
    session = create_campaign_session(storage, campaign.id, "Chegada", number=1)
    context = GameContext(
        player_name="Miko Meu",
        campaign_id=campaign.id,
        campaign_session_id=session.id,
        map_name="Mapa de Teste",
    )
    event = MapEvent("pressagio", 2, 1, "pressagio", ("Algo se mexe.",), tags=("teste",))

    assert register_map_event(storage, context, event, (2, 1)) is True

    history = list_events(storage)
    updated_session = get_campaign_session(storage, session.id)
    assert len(history) == 1
    assert history[0].campaign_id == campaign.id
    assert history[0].campaign_session_id == session.id
    assert "origem=game" in history[0].notes
    assert "posicao=(2,1)" in history[0].notes
    assert updated_session.events == ["Miko Meu: Evento de mapa - Algo se mexe."]


def test_map_event_marked_not_to_register_is_ignored_even_with_context() -> None:
    storage = MemoryStorage()
    campaign = create_campaign(storage, "Estrada do Viajante")
    session = create_campaign_session(storage, campaign.id, "Chegada", number=1)
    context = GameContext(player_name="Miko Meu", campaign_id=campaign.id, campaign_session_id=session.id)
    event = MapEvent(
        "placa",
        2,
        1,
        "mensagem",
        ("Leia de novo.",),
        registrar_no_historico=False,
    )

    assert register_map_event(storage, context, event, (2, 1)) is False
    assert list_events(storage) == []
    assert get_campaign_session(storage, session.id).events == []


def test_invalid_campaign_context_does_not_crash_game_registration() -> None:
    storage = MemoryStorage()
    context = GameContext(player_name="Miko Meu", campaign_id="invalida", campaign_session_id="sessao-invalida")
    event = MapEvent("pressagio", 2, 1, "pressagio", ("Algo se mexe.",))

    assert register_map_event(storage, context, event, (2, 1)) is False
