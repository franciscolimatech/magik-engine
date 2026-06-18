from pathlib import Path

from src.core.character import create_miko_meu
from src.game.game_context import GameContext
from src.game.save import (
    DEFAULT_SAVE_ID,
    GameSave,
    create_default_game_save,
    get_game_save,
    load_game_saves,
    load_or_create_default_game_save,
    register_current_location,
    register_triggered_event,
    save_game_saves,
    sync_game_save_context,
    update_player_position,
)
from src.game.scenes.overworld import OverworldScene
from src.storage.json_storage import JSONStorage
from src.storage.memory import MemoryStorage


def test_missing_game_save_uses_safe_fallback(tmp_path: Path) -> None:
    storage = JSONStorage(tmp_path)

    assert load_game_saves(storage) == []


def test_empty_game_save_uses_safe_fallback(tmp_path: Path) -> None:
    storage = JSONStorage(tmp_path)
    storage.path_for("game_saves.json").write_text("", encoding="utf-8")

    assert load_game_saves(storage) == []


def test_invalid_game_save_uses_safe_fallback(tmp_path: Path) -> None:
    storage = JSONStorage(tmp_path)
    storage.path_for("game_saves.json").write_text("{invalid", encoding="utf-8")

    assert load_game_saves(storage) == []


def test_create_default_game_save() -> None:
    save = create_default_game_save()

    assert save.id == DEFAULT_SAVE_ID
    assert save.character_id == "miko-meu"
    assert save.location_id == "mapa-de-teste"
    assert save.position == (5, 4)
    assert save.visited_locations == ["mapa-de-teste"]


def test_get_game_save_by_id() -> None:
    storage = MemoryStorage({"game_saves.json": {"saves": [create_default_game_save().to_dict()]}})

    save = get_game_save(storage, "default")

    assert save.id == DEFAULT_SAVE_ID


def test_update_player_position() -> None:
    storage = MemoryStorage({"game_saves.json": {"saves": [create_default_game_save().to_dict()]}})

    save = update_player_position(storage, DEFAULT_SAVE_ID, 7, 8)

    assert save.position == (7, 8)
    assert get_game_save(storage).position == (7, 8)


def test_register_triggered_event_without_duplicate() -> None:
    storage = MemoryStorage({"game_saves.json": {"saves": [create_default_game_save().to_dict()]}})

    register_triggered_event(storage, DEFAULT_SAVE_ID, "ikisaki-stir")
    save = register_triggered_event(storage, DEFAULT_SAVE_ID, "ikisaki-stir")

    assert save.triggered_events == ["ikisaki-stir"]


def test_register_current_location_tracks_visit_once() -> None:
    storage = MemoryStorage({"game_saves.json": {"saves": [create_default_game_save().to_dict()]}})

    register_current_location(storage, DEFAULT_SAVE_ID, "floresta-do-avesso")
    save = register_current_location(storage, DEFAULT_SAVE_ID, "floresta-do-avesso")

    assert save.location_id == "floresta-do-avesso"
    assert save.visited_locations.count("floresta-do-avesso") == 1


def test_save_and_reload_keeps_data(tmp_path: Path) -> None:
    storage = JSONStorage(tmp_path)
    save = create_default_game_save(character_id="lia", position=(3, 4))
    save.triggered_events.append("pressagio")

    save_game_saves(storage, [save])
    reloaded = get_game_save(storage, DEFAULT_SAVE_ID)

    assert reloaded.character_id == "lia"
    assert reloaded.position == (3, 4)
    assert reloaded.triggered_events == ["pressagio"]


def test_load_or_create_default_game_save_persists_when_missing() -> None:
    storage = MemoryStorage()

    save = load_or_create_default_game_save(storage, character_id="lia")

    assert save.character_id == "lia"
    assert get_game_save(storage).character_id == "lia"


def test_sync_game_save_context_updates_character_and_session() -> None:
    storage = MemoryStorage({"game_saves.json": {"saves": [create_default_game_save().to_dict()]}})

    save = sync_game_save_context(
        storage,
        character_id="lia",
        campaign_id="campanha-1",
        session_id="sessao-1",
        location_id="floresta-do-avesso",
    )

    assert save.character_id == "lia"
    assert save.campaign_id == "campanha-1"
    assert save.session_id == "sessao-1"
    assert save.location_id == "floresta-do-avesso"


def test_game_context_uses_default_save_when_environment_is_absent() -> None:
    storage = MemoryStorage(
        {
            "characters.json": {"characters": [create_miko_meu().to_dict()]},
            "game_saves.json": {
                "saves": [
                    GameSave(
                        id=DEFAULT_SAVE_ID,
                        character_id="miko-meu",
                        campaign_id="campanha-1",
                        session_id="sessao-1",
                    ).to_dict()
                ]
            },
        }
    )

    context = GameContext.from_env(env={}, storage=storage)

    assert context.character_id == "miko-meu"
    assert context.campaign_id == "campanha-1"
    assert context.campaign_session_id == "sessao-1"


def test_game_context_environment_overrides_save() -> None:
    storage = MemoryStorage(
        {
            "game_saves.json": {
                "saves": [
                    GameSave(
                        id=DEFAULT_SAVE_ID,
                        character_id="miko-meu",
                        campaign_id="campanha-1",
                        session_id="sessao-1",
                    ).to_dict()
                ]
            }
        }
    )

    context = GameContext.from_env(
        env={
            "MAGIK_GAME_CHARACTER_ID": "lia",
            "MAGIK_GAME_CAMPAIGN_ID": "campanha-2",
            "MAGIK_GAME_SESSION_ID": "sessao-2",
        },
        storage=storage,
    )

    assert context.character_id == "lia"
    assert context.campaign_id == "campanha-2"
    assert context.campaign_session_id == "sessao-2"


def test_overworld_uses_saved_position_when_available() -> None:
    import pygame

    storage = MemoryStorage(
        {
            "characters.json": {"characters": [create_miko_meu().to_dict()]},
            "game_saves.json": {
                "saves": [
                    GameSave(
                        id=DEFAULT_SAVE_ID,
                        character_id="miko-meu",
                        player_position={"x": 6, "y": 4},
                    ).to_dict()
                ]
            },
        }
    )
    pygame.init()

    scene = OverworldScene(pygame, GameContext(character_id="miko-meu", player_name="Miko Meu"), storage)

    assert scene.player.position == (6, 4)
    pygame.quit()


def test_overworld_registers_triggered_event_in_save() -> None:
    import pygame

    storage = MemoryStorage({"characters.json": {"characters": [create_miko_meu().to_dict()]}})
    pygame.init()
    scene = OverworldScene(pygame, GameContext(character_id="miko-meu", player_name="Miko Meu"), storage)

    event = scene.trigger_event_at(14, 4)
    save = get_game_save(storage)

    assert event is not None
    assert "ikisaki-stir" in save.triggered_events
    pygame.quit()
