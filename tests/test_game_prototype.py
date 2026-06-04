from src.core.character import Character, create_miko_meu
from src.game.app import load_player_name
from src.game.entities.npc import NPC
from src.game.entities.player import Player
from src.game.maps.test_map import find_npcs, find_player_start, is_obstacle, load_test_map
from src.storage.memory import MemoryStorage


def test_test_map_loads_with_player_start() -> None:
    map_data = load_test_map()

    assert map_data
    assert find_player_start(map_data) == (5, 4)


def test_test_map_loads_npcs() -> None:
    npcs = find_npcs(load_test_map())

    assert len(npcs) >= 1
    assert npcs[0].name
    assert npcs[0].dialogue


def test_collision_blocks_wall() -> None:
    map_data = load_test_map()

    assert is_obstacle(map_data, 0, 0) is True
    player = Player(1, 1)

    moved = player.move(-1, 0, map_data)

    assert moved is False
    assert player.position == (1, 1)


def test_valid_movement_changes_position() -> None:
    map_data = load_test_map()
    player = Player(1, 1)

    moved = player.move(1, 0, map_data)

    assert moved is True
    assert player.position == (2, 1)


def test_player_cannot_leave_map() -> None:
    map_data = load_test_map()
    player = Player(0, 0)

    moved = player.move(-1, 0, map_data)

    assert moved is False
    assert player.position == (0, 0)


def test_npc_detects_adjacent_player() -> None:
    player = Player(2, 2)
    npc = NPC(3, 2, "Guarda", "Ola.")

    assert npc.is_adjacent_to(player) is True
    assert npc.can_interact(player) is True


def test_npc_detects_player_facing_it() -> None:
    player = Player(2, 2, facing=(0, -1))
    npc = NPC(2, 1, "Guarda", "Ola.")

    assert npc.is_in_front_of(player) is True
    assert npc.can_interact(player) is True


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
