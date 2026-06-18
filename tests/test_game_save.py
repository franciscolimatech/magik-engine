from pathlib import Path

from src.core.character import create_miko_meu
from src.game.game_context import GameContext
from src.game.save import (
    DEFAULT_LOCATION_ID,
    DEFAULT_SAVE_ID,
    GameSave,
    add_npc_flag,
    add_story_flag,
    add_world_flag,
    create_default_game_save,
    get_game_save,
    has_npc_flag,
    has_story_flag,
    has_world_flag,
    initialize_character_starting_save,
    list_relevant_flags,
    load_game_saves,
    load_or_create_default_game_save,
    register_current_location,
    register_important_choice,
    register_narrative_consequence,
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


def test_old_game_save_without_flags_loads_with_safe_defaults() -> None:
    storage = MemoryStorage(
        {
            "game_saves.json": {
                "saves": [
                    {
                        "id": DEFAULT_SAVE_ID,
                        "character_id": "miko-meu",
                        "location_id": DEFAULT_LOCATION_ID,
                        "player_position": {"x": 5, "y": 4},
                    }
                ]
            }
        }
    )

    save = get_game_save(storage)

    assert save.story_flags == []
    assert save.world_flags == []
    assert save.npc_flags == {}
    assert save.choice_history == []
    assert save.consequence_log == []


def test_create_default_game_save() -> None:
    save = create_default_game_save()

    assert save.id == DEFAULT_SAVE_ID
    assert save.character_id == "miko-meu"
    assert save.location_id == DEFAULT_LOCATION_ID
    assert save.position == (5, 4)
    assert save.visited_locations == [DEFAULT_LOCATION_ID]
    assert save.story_flags == []
    assert save.world_flags == []
    assert save.npc_flags == {}
    assert save.choice_history == []
    assert save.consequence_log == []


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


def test_add_story_flag_without_duplicate() -> None:
    storage = MemoryStorage({"game_saves.json": {"saves": [create_default_game_save().to_dict()]}})

    add_story_flag(storage, DEFAULT_SAVE_ID, "falou_com_velho_nox")
    save = add_story_flag(storage, DEFAULT_SAVE_ID, "falou_com_velho_nox")

    assert save.story_flags == ["falou_com_velho_nox"]


def test_add_world_flag_without_duplicate() -> None:
    storage = MemoryStorage({"game_saves.json": {"saves": [create_default_game_save().to_dict()]}})

    add_world_flag(storage, DEFAULT_SAVE_ID, "floresta_do_avesso_inquieta")
    save = add_world_flag(storage, DEFAULT_SAVE_ID, "floresta_do_avesso_inquieta")

    assert save.world_flags == ["floresta_do_avesso_inquieta"]


def test_add_npc_flag_without_duplicate() -> None:
    storage = MemoryStorage({"game_saves.json": {"saves": [create_default_game_save().to_dict()]}})

    add_npc_flag(storage, DEFAULT_SAVE_ID, "velho-nox", "conhecido")
    save = add_npc_flag(storage, DEFAULT_SAVE_ID, "velho-nox", "conhecido")

    assert save.npc_flags == {"velho-nox": ["conhecido"]}


def test_flag_checks_work() -> None:
    storage = MemoryStorage({"game_saves.json": {"saves": [create_default_game_save().to_dict()]}})

    add_story_flag(storage, DEFAULT_SAVE_ID, "falou_com_velho_nox")
    add_world_flag(storage, DEFAULT_SAVE_ID, "floresta_do_avesso_inquieta")
    add_npc_flag(storage, DEFAULT_SAVE_ID, "velho-nox", "desconfiado")

    assert has_story_flag(storage, DEFAULT_SAVE_ID, "falou_com_velho_nox") is True
    assert has_world_flag(storage, DEFAULT_SAVE_ID, "floresta_do_avesso_inquieta") is True
    assert has_npc_flag(storage, DEFAULT_SAVE_ID, "velho-nox", "desconfiado") is True
    assert has_story_flag(storage, DEFAULT_SAVE_ID, "nao-existe") is False


def test_register_important_choice_without_duplicate() -> None:
    storage = MemoryStorage({"game_saves.json": {"saves": [create_default_game_save().to_dict()]}})

    register_important_choice(
        storage,
        DEFAULT_SAVE_ID,
        "escolha-velho-nox-001",
        "Recusou dormir perto da fogueira.",
        location_id="floresta-do-avesso",
        npc_id="velho-nox",
    )
    save = register_important_choice(
        storage,
        DEFAULT_SAVE_ID,
        "escolha-velho-nox-001",
        "Recusou dormir perto da fogueira.",
        location_id="floresta-do-avesso",
        npc_id="velho-nox",
    )

    assert save.choice_history == [
        {
            "id": "escolha-velho-nox-001",
            "location_id": "floresta-do-avesso",
            "npc_id": "velho-nox",
            "choice": "Recusou dormir perto da fogueira.",
            "timestamp": None,
        }
    ]


def test_register_narrative_consequence_without_duplicate() -> None:
    storage = MemoryStorage({"game_saves.json": {"saves": [create_default_game_save().to_dict()]}})

    register_narrative_consequence(
        storage,
        DEFAULT_SAVE_ID,
        "consequencia-001",
        "Velho Nox passou a observar o personagem com mais cautela.",
        location_id="floresta-do-avesso",
        npc_id="velho-nox",
    )
    save = register_narrative_consequence(
        storage,
        DEFAULT_SAVE_ID,
        "consequencia-001",
        "Velho Nox passou a observar o personagem com mais cautela.",
        location_id="floresta-do-avesso",
        npc_id="velho-nox",
    )

    assert save.consequence_log == [
        {
            "id": "consequencia-001",
            "location_id": "floresta-do-avesso",
            "npc_id": "velho-nox",
            "text": "Velho Nox passou a observar o personagem com mais cautela.",
        }
    ]


def test_list_relevant_flags() -> None:
    storage = MemoryStorage({"game_saves.json": {"saves": [create_default_game_save().to_dict()]}})
    add_story_flag(storage, DEFAULT_SAVE_ID, "falou_com_velho_nox")
    add_world_flag(storage, DEFAULT_SAVE_ID, "floresta_do_avesso_inquieta")
    add_npc_flag(storage, DEFAULT_SAVE_ID, "velho-nox", "desconfiado")

    flags = list_relevant_flags(storage, DEFAULT_SAVE_ID, npc_id="velho-nox")

    assert flags == {
        "story_flags": ["falou_com_velho_nox"],
        "world_flags": ["floresta_do_avesso_inquieta"],
        "npc_flags": {"velho-nox": ["desconfiado"]},
    }


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


def test_save_and_reload_preserves_flags_and_logs(tmp_path: Path) -> None:
    storage = JSONStorage(tmp_path)
    save = create_default_game_save(character_id="lia", position=(3, 4))
    save.story_flags.append("falou_com_velho_nox")
    save.world_flags.append("floresta_do_avesso_inquieta")
    save.npc_flags["velho-nox"] = ["desconfiado"]
    save.choice_history.append(
        {
            "id": "escolha-001",
            "location_id": "floresta-do-avesso",
            "npc_id": "velho-nox",
            "choice": "Perguntou sobre a floresta.",
            "timestamp": None,
        }
    )
    save.consequence_log.append(
        {
            "id": "consequencia-001",
            "location_id": "floresta-do-avesso",
            "text": "A floresta pareceu escutar.",
        }
    )

    save_game_saves(storage, [save])
    reloaded = get_game_save(storage, DEFAULT_SAVE_ID)

    assert reloaded.story_flags == ["falou_com_velho_nox"]
    assert reloaded.world_flags == ["floresta_do_avesso_inquieta"]
    assert reloaded.npc_flags == {"velho-nox": ["desconfiado"]}
    assert reloaded.choice_history[0]["choice"] == "Perguntou sobre a floresta."
    assert reloaded.consequence_log[0]["text"] == "A floresta pareceu escutar."


def test_real_game_save_file_is_ignored() -> None:
    gitignore = Path(".gitignore").read_text(encoding="utf-8")

    assert "data/game_saves.json" in gitignore


def test_load_or_create_default_game_save_persists_when_missing() -> None:
    storage = MemoryStorage()

    save = load_or_create_default_game_save(storage, character_id="lia")

    assert save.character_id == "lia"
    assert get_game_save(storage).character_id == "lia"


def test_initialize_character_starting_save_uses_character_origin() -> None:
    storage = MemoryStorage()
    character = create_miko_meu()
    character.id = "lia"
    character.origin_location_id = "cidade-de-pedralume"

    save = initialize_character_starting_save(storage, character)

    assert save.character_id == "lia"
    assert save.location_id == "cidade-de-pedralume"
    assert save.position == (5, 4)
    assert save.visited_locations == ["cidade-de-pedralume"]
    assert get_game_save(storage).location_id == "cidade-de-pedralume"


def test_initialize_character_starting_save_invalid_origin_uses_fallback() -> None:
    storage = MemoryStorage()
    character = create_miko_meu()
    character.id = "lia"
    character.origin_location_id = "local-inexistente"

    save = initialize_character_starting_save(storage, character)

    assert save.character_id == "lia"
    assert save.location_id == DEFAULT_LOCATION_ID
    assert save.visited_locations == [DEFAULT_LOCATION_ID]


def test_initialize_character_starting_save_preserves_existing_progress() -> None:
    storage = MemoryStorage()
    existing = create_default_game_save(
        character_id="miko-meu",
        location_id="floresta-do-avesso",
        position=(8, 9),
    )
    existing.triggered_events.append("pressagio-antigo")
    existing.visited_locations.append("cidade-de-pedralume")
    save_game_saves(storage, [existing])
    character = create_miko_meu()
    character.id = "lia"
    character.origin_location_id = "cidade-de-pedralume"

    save = initialize_character_starting_save(storage, character)

    assert save.character_id == "lia"
    assert save.location_id == "cidade-de-pedralume"
    assert save.position == (8, 9)
    assert save.triggered_events == ["pressagio-antigo"]
    assert save.visited_locations.count("cidade-de-pedralume") == 1


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
    assert context.location_id == DEFAULT_LOCATION_ID


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
            "MAGIK_GAME_LOCATION_ID": "cidade-de-pedralume",
        },
        storage=storage,
    )

    assert context.character_id == "lia"
    assert context.campaign_id == "campanha-2"
    assert context.campaign_session_id == "sessao-2"
    assert context.location_id == "cidade-de-pedralume"


def test_game_context_invalid_location_uses_safe_fallback() -> None:
    storage = MemoryStorage(
        {
            "characters.json": {"characters": [create_miko_meu().to_dict()]},
            "game_saves.json": {
                "saves": [
                    GameSave(
                        id=DEFAULT_SAVE_ID,
                        character_id="miko-meu",
                        location_id="local-inexistente",
                    ).to_dict()
                ]
            },
        }
    )

    context = GameContext.from_env(env={}, storage=storage)

    assert context.location_id == DEFAULT_LOCATION_ID


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
    assert scene.location_id == DEFAULT_LOCATION_ID
    assert scene.location_display_name == "Floresta do Avesso"
    assert scene.lore_summary is not None
    assert scene.lore_summary["location"]["id"] == DEFAULT_LOCATION_ID
    assert scene.hud.map_name == "Floresta do Avesso"
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


def test_overworld_shadow_event_applies_narrative_flags_and_logs() -> None:
    import pygame

    storage = MemoryStorage({"characters.json": {"characters": [create_miko_meu().to_dict()]}})
    pygame.init()
    scene = OverworldScene(pygame, GameContext(character_id="miko-meu", player_name="Miko Meu"), storage)

    event = scene.trigger_event_at(9, 4)
    assert event is not None
    assert event.id == "evento-sombra-observa"

    scene._handle_dialogue_option(event.choice.options[0])
    save = get_game_save(storage)

    assert "viu_sombra_na_floresta_do_avesso" in save.story_flags
    assert "floresta_do_avesso_inquieta" in save.world_flags
    assert save.choice_history == [
        {
            "id": "evento-sombra-observa-escolha",
            "location_id": "floresta-do-avesso",
            "npc_id": None,
            "choice": "Observar em silencio.",
            "timestamp": None,
        }
    ]
    assert save.consequence_log == [
        {
            "id": "evento-sombra-observa-consequencia",
            "location_id": "floresta-do-avesso",
            "npc_id": None,
            "text": "A Floresta do Avesso pareceu notar que o personagem tambem observa de volta.",
        }
    ]
    pygame.quit()


def test_overworld_shadow_event_does_not_duplicate_narrative_state() -> None:
    import pygame

    storage = MemoryStorage({"characters.json": {"characters": [create_miko_meu().to_dict()]}})
    pygame.init()
    scene = OverworldScene(pygame, GameContext(character_id="miko-meu", player_name="Miko Meu"), storage)
    event = scene.trigger_event_at(9, 4)
    assert event is not None

    scene._handle_dialogue_option(event.choice.options[1])
    repeated = scene.trigger_event_at(9, 4)
    save = get_game_save(storage)

    assert repeated is None
    assert save.story_flags.count("viu_sombra_na_floresta_do_avesso") == 1
    assert save.world_flags.count("floresta_do_avesso_inquieta") == 1
    assert len(save.choice_history) == 1
    assert len(save.consequence_log) == 1
    pygame.quit()


def test_overworld_shadow_event_respects_location_id() -> None:
    import pygame

    storage = MemoryStorage({"characters.json": {"characters": [create_miko_meu().to_dict()]}})
    pygame.init()
    scene = OverworldScene(
        pygame,
        GameContext(character_id="miko-meu", player_name="Miko Meu", location_id="cidade-de-pedralume"),
        storage,
    )

    event = scene.trigger_event_at(9, 4)
    save = get_game_save(storage)

    assert scene.location_id == "cidade-de-pedralume"
    assert event is None
    assert save.story_flags == []
    assert save.world_flags == []
    pygame.quit()


def test_overworld_shadow_event_does_not_trigger_when_story_flag_exists() -> None:
    import pygame

    storage = MemoryStorage(
        {
            "characters.json": {"characters": [create_miko_meu().to_dict()]},
            "game_saves.json": {
                "saves": [
                    GameSave(
                        id=DEFAULT_SAVE_ID,
                        character_id="miko-meu",
                        location_id=DEFAULT_LOCATION_ID,
                        story_flags=["viu_sombra_na_floresta_do_avesso"],
                    ).to_dict()
                ]
            },
        }
    )
    pygame.init()
    scene = OverworldScene(pygame, GameContext(character_id="miko-meu", player_name="Miko Meu"), storage)

    event = scene.trigger_event_at(9, 4)
    save = get_game_save(storage)

    assert event is None
    assert save.story_flags == ["viu_sombra_na_floresta_do_avesso"]
    assert save.choice_history == []
    pygame.quit()


def test_overworld_velho_nox_interaction_adds_memory_flags() -> None:
    import pygame

    storage = MemoryStorage({"characters.json": {"characters": [create_miko_meu().to_dict()]}})
    pygame.init()
    scene = OverworldScene(pygame, GameContext(character_id="miko-meu", player_name="Miko Meu"), storage)
    scene.player.x = 4
    scene.player.y = 10
    scene.player.direction = "right"

    assert scene.interact() is True
    save = get_game_save(storage)

    assert scene.dialogue.speaker == "Velho Nox"
    assert scene.dialogue.current_text == "Velho Nox observa as arvores como se elas estivessem respirando."
    assert "falou_com_velho_nox" in save.story_flags
    assert save.npc_flags["velho-nox"] == ["conhecido"]
    assert save.consequence_log == []
    pygame.quit()


def test_overworld_velho_nox_reacts_after_shadow_flag() -> None:
    import pygame

    storage = MemoryStorage(
        {
            "characters.json": {"characters": [create_miko_meu().to_dict()]},
            "game_saves.json": {
                "saves": [
                    GameSave(
                        id=DEFAULT_SAVE_ID,
                        character_id="miko-meu",
                        location_id=DEFAULT_LOCATION_ID,
                        story_flags=["viu_sombra_na_floresta_do_avesso"],
                    ).to_dict()
                ]
            },
        }
    )
    pygame.init()
    scene = OverworldScene(pygame, GameContext(character_id="miko-meu", player_name="Miko Meu"), storage)
    scene.player.x = 4
    scene.player.y = 10
    scene.player.direction = "right"

    assert scene.interact() is True
    save = get_game_save(storage)

    assert scene.dialogue.speaker == "Velho Nox"
    assert scene.dialogue.current_text == "Velho Nox aperta os olhos."
    scene.dialogue.advance()
    assert scene.dialogue.current_text == "'Entao voce tambem viu. A floresta ja comecou a olhar de volta.'"
    assert "falou_com_velho_nox" in save.story_flags
    assert save.npc_flags["velho-nox"] == ["conhecido"]
    assert save.consequence_log == [
        {
            "id": "velho-nox-reconhece-sombra",
            "location_id": "floresta-do-avesso",
            "npc_id": "velho-nox",
            "text": "Velho Nox reconheceu que o personagem viu uma sombra na Floresta do Avesso.",
        }
    ]
    pygame.quit()


def test_overworld_velho_nox_consequence_does_not_duplicate() -> None:
    import pygame

    storage = MemoryStorage(
        {
            "characters.json": {"characters": [create_miko_meu().to_dict()]},
            "game_saves.json": {
                "saves": [
                    GameSave(
                        id=DEFAULT_SAVE_ID,
                        character_id="miko-meu",
                        location_id=DEFAULT_LOCATION_ID,
                        story_flags=["viu_sombra_na_floresta_do_avesso"],
                    ).to_dict()
                ]
            },
        }
    )
    pygame.init()
    scene = OverworldScene(pygame, GameContext(character_id="miko-meu", player_name="Miko Meu"), storage)
    scene.player.x = 4
    scene.player.y = 10
    scene.player.direction = "right"

    scene.interact()
    scene.interact()
    save = get_game_save(storage)

    assert save.story_flags.count("falou_com_velho_nox") == 1
    assert save.npc_flags["velho-nox"].count("conhecido") == 1
    assert len(save.consequence_log) == 1
    pygame.quit()


def test_overworld_velho_nox_reaction_respects_location_id() -> None:
    import pygame

    storage = MemoryStorage({"characters.json": {"characters": [create_miko_meu().to_dict()]}})
    pygame.init()
    scene = OverworldScene(
        pygame,
        GameContext(character_id="miko-meu", player_name="Miko Meu", location_id="cidade-de-pedralume"),
        storage,
    )
    scene.player.x = 4
    scene.player.y = 10
    scene.player.direction = "right"

    assert scene.interact() is True
    save = get_game_save(storage)

    assert scene.location_id == "cidade-de-pedralume"
    assert scene.dialogue.current_text == "Velho Nox observa as arvores como se elas estivessem respirando."
    assert "falou_com_velho_nox" not in save.story_flags
    assert "velho-nox" not in save.npc_flags
    assert save.consequence_log == []
    pygame.quit()
