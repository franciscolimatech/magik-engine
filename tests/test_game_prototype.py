from src.core.character import Character, create_miko_meu
from src.core.campaigns import create_campaign, create_campaign_session, get_campaign_session
from src.core.creatures import create_creature
from src.core.session import list_events
from src.game.assets import create_assets
from src.game.app import _load_battle_character, _max_frames_from_env, load_player_name
from src.game.camera import Camera
from src.game.dialogue import DialogueChoice, DialogueOption
from src.game.entities.creature import Creature, default_creature, load_game_creature
from src.game.entities.npc import NPC
from src.game.entities.player import Player
from src.game.event_registry import register_battle_event, register_creature_encounter, register_map_event
from src.game.game_context import GameContext
from src.game.maps.events import MapEvent, find_event_at
from src.game.maps.test_map import (
    find_creatures,
    find_npcs,
    find_player_start,
    is_obstacle,
    is_walkable,
    load_test_map,
    map_height,
    map_width,
)
from src.game.scenes.battle import BattleScene
from src.game.scenes.main_menu import MainMenuScene
from src.game.scenes.overworld import OverworldScene
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
    K_BACKSPACE = 10


class FakeEvent:
    def __init__(self, key: int, unicode: str = "") -> None:
        self.type = FakePygame.KEYDOWN
        self.key = key
        self.unicode = unicode


class FakeRng:
    def __init__(self, values: list[int]) -> None:
        self.values = list(values)

    def randint(self, a: int, b: int) -> int:
        value = self.values.pop(0)
        return max(a, min(value, b))


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


def test_test_map_loads_creatures() -> None:
    creatures = find_creatures(load_test_map())

    assert len(creatures) >= 1
    assert load_test_map()[creatures[0].y][creatures[0].x] == "C"


def test_generated_assets_include_tiles_and_sprites() -> None:
    import pygame

    pygame.init()
    assets = create_assets(pygame)

    assert assets.wall_tile.get_size() == (32, 32)
    assert assets.water_tile.get_size() == (32, 32)
    assert assets.floor_tiles["g"].get_size() == (32, 32)
    assert assets.floor_tiles["C"].get_size() == (32, 32)
    assert assets.npc.get_size() == (32, 32)
    assert assets.creature.get_size() == (32, 32)
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
        "#..C.#",
        "######",
    ]

    assert is_walkable(map_data, 1, 1) is True
    assert is_walkable(map_data, 2, 1) is True
    assert is_walkable(map_data, 3, 1) is True
    assert is_obstacle(map_data, 4, 1) is True
    assert is_obstacle(map_data, 3, 2) is True


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


def test_creature_instantiates_correctly() -> None:
    creature = Creature(
        id="sombra",
        name="Sombra",
        x=3,
        y=2,
        description="Uma sombra baixa.",
        current_health=8,
        max_health=10,
        armor=1,
        hostile=True,
    )

    assert creature.id == "sombra"
    assert creature.name == "Sombra"
    assert creature.position == (3, 2)
    assert creature.current_health == 8
    assert creature.max_health == 10
    assert creature.armor == 1
    assert creature.hostile is True


def test_default_creature_uses_test_values() -> None:
    creature = default_creature(4, 5)

    assert creature.name == "Sombra Rastejante"
    assert creature.position == (4, 5)
    assert creature.max_health > 0


def test_game_creature_loads_core_creature_when_available() -> None:
    storage = MemoryStorage()
    create_creature(
        storage,
        name="Lodo da Estrada",
        creature_type="criatura",
        max_health=18,
        armor=3,
        description="Um lodo escuro observa sem olhos.",
    )

    creature = load_game_creature(storage, 7, 8)

    assert creature.name == "Lodo da Estrada"
    assert creature.position == (7, 8)
    assert creature.max_health == 18
    assert creature.current_health == 18
    assert creature.armor == 3
    assert creature.description == "Um lodo escuro observa sem olhos."


def test_creature_detects_player_facing_it() -> None:
    player = Player(2, 2, direction="right")
    creature = default_creature(3, 2)

    assert creature.can_interact(player) is True


def test_creature_encounter_opens_with_options() -> None:
    creature = default_creature(3, 2)
    choice = creature.encounter_choice()

    assert choice.question == "O que voce faz?"
    assert [option.text for option in choice.options] == ["Observar", "Ameacar", "Recuar", "Iniciar combate"]


def test_creature_observe_option_shows_response() -> None:
    creature = default_creature(3, 2)
    option = creature.encounter_choice().options[0]
    dialogue = DialogueBox(creature.name, creature.encounter_messages(), choice=creature.encounter_choice())
    dialogue.advance()
    dialogue.advance()

    selected = dialogue.confirm_choice()

    assert selected == option
    assert "Vida:" in dialogue.current_text


def test_creature_retreat_option_closes_encounter() -> None:
    creature = default_creature(3, 2)
    retreat_option = creature.encounter_choice().options[2]
    dialogue = DialogueBox(creature.name, creature.encounter_messages(), choice=creature.encounter_choice())

    class SceneLike:
        storage = None
        context = GameContext(player_name="Miko Meu")
        pending_event = None
        pending_creature = creature
        dialogue = None

    SceneLike.dialogue = dialogue

    OverworldScene._handle_dialogue_option(SceneLike, retreat_option)

    assert SceneLike.dialogue.visible is False
    assert SceneLike.pending_creature is None


def test_creature_start_combat_option_prepares_battle() -> None:
    creature = default_creature(3, 2)
    option = creature.encounter_choice().options[3]

    assert option.text == "Iniciar combate"
    assert option.event == "start_combat"
    assert option.response == "Voce se prepara para o combate visual."


def test_battle_scene_instantiates_with_character_and_creature() -> None:
    character = create_miko_meu()
    creature = default_creature(3, 2)

    scene = BattleScene(FakePygame, GameContext(player_name=character.name), character, creature)

    assert scene.character.name == "Miko Meu"
    assert scene.creature.name == "Sombra Rastejante"
    assert scene.selected_option == "Atacar"


def test_battle_menu_navigation_works() -> None:
    scene = BattleScene(FakePygame, GameContext(player_name="Miko Meu"), create_miko_meu(), default_creature(3, 2))

    scene.handle_event(FakeEvent(FakePygame.K_DOWN))
    assert scene.selected_option == "Habilidade"

    scene.handle_event(FakeEvent(FakePygame.K_UP))
    assert scene.selected_option == "Atacar"


def test_battle_observe_adds_text_to_log() -> None:
    scene = BattleScene(FakePygame, GameContext(player_name="Miko Meu"), create_miko_meu(), default_creature(3, 2))
    scene.selected_index = 2

    scene.confirm_selection()

    assert "Vida:" in scene.log[-1]
    assert "Armadura:" in scene.log[-1]
    assert "Dica:" in scene.log[-1]


def test_battle_flee_requests_return_to_overworld() -> None:
    scene = BattleScene(FakePygame, GameContext(player_name="Miko Meu"), create_miko_meu(), default_creature(3, 2))
    scene.selected_index = 3

    scene.confirm_selection()

    assert scene.consume_requested_scene() == "overworld"
    assert "fugiu" in scene.log[-1]
    assert scene.fled is True


def test_battle_menu_includes_ability() -> None:
    assert BattleScene.OPTIONS == ("Atacar", "Habilidade", "Observar", "Fugir")


def test_battle_ability_without_abilities_adds_message() -> None:
    character = Character(
        id="lia",
        name="Lia",
        character_class="Guia",
        max_health=20,
        current_health=20,
        armor=0,
        abilities=[],
    )
    scene = BattleScene(FakePygame, GameContext(player_name="Lia"), character, default_creature(3, 2))
    scene.selected_index = 1

    scene.confirm_selection()

    assert scene.log[-1] == "Nenhuma habilidade disponivel."
    assert scene.mode == "actions"


def test_battle_ability_with_ability_adds_text_to_log_and_consumes_use() -> None:
    character = create_miko_meu()
    character.abilities = [
        {
            "id": "golpe-sombrio",
            "name": "Golpe Sombrio",
            "type": "ataque",
            "use": "limitado",
            "effect": "Um golpe envolto em sombra.",
            "cost": "1 folego",
            "usage_limit": 1,
            "remaining_uses": 1,
        }
    ]
    scene = BattleScene(FakePygame, GameContext(player_name=character.name), character, default_creature(3, 2))

    scene.open_abilities()
    scene.use_selected_ability()

    assert any("Miko Meu usou Golpe Sombrio" in line for line in scene.log)
    assert any("Usos restantes: 0" in line for line in scene.log)
    assert character.abilities[0]["remaining_uses"] == 0


def test_battle_ability_use_without_campaign_does_not_break() -> None:
    character = create_miko_meu()
    scene = BattleScene(FakePygame, GameContext(player_name=character.name), character, default_creature(3, 2))

    scene.open_abilities()
    scene.use_selected_ability()

    assert scene.mode == "actions"
    assert any("usou" in line for line in scene.log)


def test_battle_attack_reduces_creature_armor_with_physical_rule() -> None:
    character = create_miko_meu()
    creature = Creature("sombra", "Sombra", 3, 2, "Uma sombra.", current_health=10, max_health=10, armor=3)
    scene = BattleScene(FakePygame, GameContext(player_name=character.name), character, creature, rng=FakeRng([2, 1]))

    scene.attack()

    assert scene.creature.armor == 1
    assert scene.creature.current_health == 10
    assert "causou 2 de dano" in scene.log[-2]


def test_battle_creature_responds_when_alive() -> None:
    character = create_miko_meu()
    character.armor = 0
    creature = Creature("sombra", "Sombra", 3, 2, "Uma sombra.", current_health=10, max_health=10, armor=0)
    scene = BattleScene(FakePygame, GameContext(player_name=character.name), character, creature, rng=FakeRng([2, 3]))

    scene.attack()

    assert scene.creature.current_health == 8
    assert scene.character.current_health == 22
    assert "Sombra atacou Miko Meu e causou 3 de dano." in scene.log[-1]


def test_battle_detects_victory_when_creature_reaches_zero() -> None:
    character = create_miko_meu()
    creature = Creature("sombra", "Sombra", 3, 2, "Uma sombra.", current_health=1, max_health=1, armor=0)
    scene = BattleScene(FakePygame, GameContext(player_name=character.name), character, creature, rng=FakeRng([1]))

    scene.attack()

    assert scene.victory is True
    assert scene.turn_state == "vitoria"
    assert scene.creature.current_health == 0
    assert any("Vitoria!" in line for line in scene.log)


def test_battle_return_to_map_after_victory() -> None:
    scene = BattleScene(
        FakePygame,
        GameContext(player_name="Miko Meu"),
        create_miko_meu(),
        Creature("sombra", "Sombra", 3, 2, "Uma sombra.", current_health=1, max_health=1, armor=0),
        rng=FakeRng([1]),
    )

    scene.attack()
    scene.handle_event(FakeEvent(FakePygame.K_RETURN))

    assert scene.consume_requested_scene() == "overworld"
    assert scene.selected_option == "Voltar ao mapa"


def test_battle_detects_defeat_when_character_reaches_zero() -> None:
    character = Character(
        id="lia",
        name="Lia",
        character_class="Guia",
        max_health=2,
        current_health=2,
        armor=0,
    )
    creature = Creature("sombra", "Sombra", 3, 2, "Uma sombra.", current_health=10, max_health=10, armor=0)
    scene = BattleScene(FakePygame, GameContext(player_name=character.name), character, creature, rng=FakeRng([1, 2]))

    scene.attack()

    assert scene.defeat is True
    assert scene.turn_state == "derrota"
    assert scene.character.current_health == 0
    assert any("caiu" in line for line in scene.log)


def test_battle_event_registers_with_campaign_session() -> None:
    storage = MemoryStorage()
    campaign = create_campaign(storage, "Estrada do Viajante")
    session = create_campaign_session(storage, campaign.id, "Chegada", number=1)
    context = GameContext(player_name="Miko Meu", campaign_id=campaign.id, campaign_session_id=session.id)
    creature = default_creature(3, 2)

    assert register_battle_event(storage, context, creature, creature.position, "inicio", "Teste.") is True

    history = list_events(storage)
    assert history[0].action == "Combate visual"
    assert "tipo=battle" in history[0].notes
    assert "evento=inicio" in history[0].notes


def test_overworld_start_combat_choice_requests_battle_scene() -> None:
    creature = default_creature(3, 2)
    start_option = creature.encounter_choice().options[3]

    class SceneLike:
        storage = None
        context = GameContext(player_name="Miko Meu")
        pending_event = None
        pending_creature = creature
        dialogue = DialogueBox(creature.name, creature.encounter_messages(), choice=creature.encounter_choice())
        requested_scene = None
        requested_creature = None

    OverworldScene._handle_dialogue_option(SceneLike, start_option)

    assert SceneLike.requested_scene == "battle"
    assert SceneLike.requested_creature == creature
    assert SceneLike.pending_creature is None


def test_dialogue_box_keeps_speaker_name() -> None:
    dialogue = DialogueBox("Guarda", "Ola.")

    assert dialogue.speaker == "Guarda"
    assert dialogue.visible is True


def test_dialogue_box_enters_choice_mode_after_messages() -> None:
    choice = DialogueChoice(
        "Vai seguir?",
        (
            DialogueOption("Sim", "Entao cuidado."),
            DialogueOption("Nao", "Sabio."),
        ),
    )
    dialogue = DialogueBox("Velho", "Ola.", choice=choice)

    dialogue.advance()

    assert dialogue.mode == "choice"
    assert dialogue.current_text == "Vai seguir?"
    assert dialogue.selected_option_index == 0


def test_dialogue_choice_navigation_down_and_up() -> None:
    choice = DialogueChoice(
        "Escolha.",
        (
            DialogueOption("Primeira", "Um."),
            DialogueOption("Segunda", "Dois."),
        ),
    )
    dialogue = DialogueBox("Velho", "Ola.", choice=choice)
    dialogue.advance()

    dialogue.handle_key(FakePygame, FakePygame.K_DOWN)
    assert dialogue.selected_option_index == 1

    dialogue.handle_key(FakePygame, FakePygame.K_UP)
    assert dialogue.selected_option_index == 0


def test_dialogue_confirm_choice_returns_option_and_shows_response() -> None:
    option = DialogueOption("Sim", "Entao leve cuidado.", tags=("coragem",))
    dialogue = DialogueBox("Velho", "Ola.", choice=DialogueChoice("Vai?", (option,)))
    dialogue.advance()

    selected = dialogue.handle_key(FakePygame, FakePygame.K_RETURN)

    assert selected == option
    assert dialogue.mode == "response"
    assert dialogue.current_text == "Entao leve cuidado."
    assert dialogue.chosen_option == option


def test_dialogue_closes_after_choice_response() -> None:
    dialogue = DialogueBox("Velho", "Ola.", choice=DialogueChoice("Vai?", (DialogueOption("Sim", "Va."),)))
    dialogue.advance()
    dialogue.confirm_choice()

    dialogue.handle_key(FakePygame, FakePygame.K_SPACE)

    assert dialogue.visible is False


def test_npc_accepts_multiple_dialogues() -> None:
    npc = NPC(1, 1, "Velho", ["Primeira fala.", "Segunda fala."])

    assert npc.dialogue == "Primeira fala."
    assert npc.dialogues == ("Primeira fala.", "Segunda fala.")


def test_npc_can_have_choice() -> None:
    choice = DialogueChoice("Vai seguir?", (DialogueOption("Sim", "Cuidado."),))
    npc = NPC(1, 1, "Velho", ["Primeira fala."], choice=choice)

    assert npc.choice == choice


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

    assert scene.selected_option == "Continuar"
    assert scene.mode == "main"


def test_main_menu_starts_with_start_game_selected() -> None:
    scene = MainMenuScene(FakePygame, GameContext(player_name="Miko Meu"))

    assert scene.selected_index == 0
    assert scene.selected_option == "Continuar"
    assert "Novo Jogo" in scene.OPTIONS
    assert "Carregar Personagem" in scene.OPTIONS


def test_main_menu_navigation_down_changes_option() -> None:
    scene = MainMenuScene(FakePygame, GameContext(player_name="Miko Meu"))

    scene.handle_event(FakeEvent(FakePygame.K_DOWN))

    assert scene.selected_option == "Novo Jogo"


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
    scene.selected_index = 5

    scene.handle_event(FakeEvent(FakePygame.K_RETURN))

    assert scene.should_quit is True


def test_game_context_can_switch_character_and_player_name() -> None:
    other = Character(
        id="lia",
        name="Lia",
        character_class="Guia",
        max_health=20,
        current_health=20,
        armor=1,
    )
    storage = MemoryStorage({"characters.json": {"characters": [create_miko_meu().to_dict(), other.to_dict()]}})

    context = GameContext(player_name="Miko Meu").with_character("lia", storage)

    assert context.character_id == "lia"
    assert context.player_name == "Lia"


def test_main_menu_load_existing_character_updates_context() -> None:
    other = Character(
        id="lia",
        name="Lia",
        character_class="Guia",
        max_health=20,
        current_health=20,
        armor=1,
    )
    storage = MemoryStorage({"characters.json": {"characters": [create_miko_meu().to_dict(), other.to_dict()]}})
    scene = MainMenuScene(FakePygame, GameContext(player_name="Miko Meu"), storage=storage)

    assert scene.select_character(1) is True

    assert scene.context.character_id == "lia"
    assert scene.context.player_name == "Lia"
    assert scene.consume_requested_scene() == "overworld"


def test_main_menu_new_game_requires_name() -> None:
    scene = MainMenuScene(FakePygame, GameContext(player_name="Miko Meu"), storage=MemoryStorage())
    scene.mode = "name"

    scene.handle_event(FakeEvent(FakePygame.K_RETURN))

    assert scene.mode == "name"
    assert scene.error_message == "Nome do personagem e obrigatorio."


def test_main_menu_new_game_class_selection_works() -> None:
    scene = MainMenuScene(FakePygame, GameContext(player_name="Miko Meu"), storage=MemoryStorage())
    scene.mode = "class"

    scene.handle_event(FakeEvent(FakePygame.K_DOWN))

    assert scene.selected_option == "Guerreiro"


def test_main_menu_new_game_creates_character_with_player_created_tag() -> None:
    storage = MemoryStorage()
    scene = MainMenuScene(FakePygame, GameContext(player_name="Aventureiro"), storage=storage)
    scene.new_character_name = "Lia Nova"
    scene.class_index = 1

    character = scene.create_new_character()

    assert character.name == "Lia Nova"
    assert character.character_class == "Guerreiro"
    assert character.max_health == 25
    assert character.current_health == 25
    assert character.armor == 0
    assert "player-created" in character.tags
    assert "Criado pelo jogo 2D" in character.notes
    assert scene.context.character_id == character.id
    assert scene.context.player_name == "Lia Nova"


def test_main_menu_new_game_generates_unique_id() -> None:
    storage = MemoryStorage()
    first = MainMenuScene(FakePygame, GameContext(player_name="Aventureiro"), storage=storage)
    first.new_character_name = "Lia Nova"
    first.create_new_character()
    second = MainMenuScene(FakePygame, GameContext(player_name="Aventureiro"), storage=storage)
    second.new_character_name = "Lia Nova"

    character = second.create_new_character()

    assert character.id == "lia-nova-2"


def test_main_menu_name_input_accepts_allowed_characters() -> None:
    scene = MainMenuScene(FakePygame, GameContext(player_name="Aventureiro"), storage=MemoryStorage())
    scene.mode = "name"

    scene.handle_event(FakeEvent(0, unicode="L"))
    scene.handle_event(FakeEvent(0, unicode="i"))
    scene.handle_event(FakeEvent(FakePygame.K_SPACE, unicode=" "))
    scene.handle_event(FakeEvent(0, unicode="_"))

    assert scene.new_character_name == "Li _"


def test_battle_character_loader_uses_selected_context_character() -> None:
    other = Character(
        id="lia",
        name="Lia",
        character_class="Guia",
        max_health=20,
        current_health=20,
        armor=1,
    )
    storage = MemoryStorage({"characters.json": {"characters": [create_miko_meu().to_dict(), other.to_dict()]}})
    context = GameContext(character_id="lia", player_name="Lia")

    character = _load_battle_character(storage, context)

    assert character.id == "lia"
    assert character.name == "Lia"


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


def test_map_event_can_have_choice() -> None:
    choice = DialogueChoice("Tocar a corrente?", (DialogueOption("Tocar", "Ela aperta de volta."),))
    event = MapEvent("pressagio", 2, 1, "pressagio", ("Algo se mexe.",), choice=choice)

    assert event.choice == choice
    assert event.choice.options[0].text == "Tocar"


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


def test_map_event_registration_includes_selected_option() -> None:
    storage = MemoryStorage()
    campaign = create_campaign(storage, "Estrada do Viajante")
    session = create_campaign_session(storage, campaign.id, "Chegada", number=1)
    context = GameContext(player_name="Miko Meu", campaign_id=campaign.id, campaign_session_id=session.id)
    event = MapEvent("pressagio", 2, 1, "pressagio", ("Algo se mexe.",))
    option = DialogueOption("Tocar", "Ela aperta de volta.", tags=("toque",))

    assert register_map_event(storage, context, event, (2, 1), selected_option=option) is True

    history = list_events(storage)
    assert "Escolha: Tocar" in history[0].result
    assert "opcao=Tocar" in history[0].notes
    assert "opcao_tags=toque" in history[0].notes


def test_creature_encounter_registers_with_campaign_session() -> None:
    storage = MemoryStorage()
    campaign = create_campaign(storage, "Estrada do Viajante")
    session = create_campaign_session(storage, campaign.id, "Chegada", number=1)
    context = GameContext(player_name="Miko Meu", campaign_id=campaign.id, campaign_session_id=session.id)
    creature = default_creature(3, 2)
    option = creature.encounter_choice().options[3]

    assert register_creature_encounter(storage, context, creature, creature.position, selected_option=option) is True

    history = list_events(storage)
    assert len(history) == 1
    assert history[0].action == "Encontro com criatura"
    assert "Escolha: Iniciar combate" in history[0].result
    assert "tipo=creature_encounter" in history[0].notes
    assert "opcao=Iniciar combate" in history[0].notes


def test_creature_encounter_without_campaign_does_not_break() -> None:
    storage = MemoryStorage()
    context = GameContext(player_name="Miko Meu")
    creature = default_creature(3, 2)

    assert register_creature_encounter(storage, context, creature, creature.position) is False
    assert list_events(storage) == []


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
