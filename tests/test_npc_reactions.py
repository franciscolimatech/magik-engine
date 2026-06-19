from src.game.entities.npc import NPC
from src.game.game_context import GameContext
from src.game.npc_reactions import (
    ENTRY_WHISPER_HEARD_FLAG,
    NOX_TRAIL_MENTIONED_FLAG,
    VELHO_NOX_AFTER_WHISPER_DIALOGUE,
    SHADOW_TRAIL_INVESTIGATED_FLAG,
    VELHO_NOX_AFTER_TRAIL_DIALOGUE,
    VELHO_NOX_REPEAT_DIALOGUE,
    VELHO_NOX_SHADOW_CONSEQUENCE_ID,
    VELHO_NOX_SHADOW_CONSEQUENCE_TEXT,
    VELHO_NOX_SHADOW_DIALOGUE,
    VELHO_NOX_WHISPER_CONSEQUENCE_ID,
    VELHO_NOX_WHISPER_CONSEQUENCE_TEXT,
    apply_npc_interaction_effects,
    apply_npc_interaction_effects_to_storage,
    get_npc_dialogue_for_state,
)
from src.game.save import DEFAULT_LOCATION_ID, DEFAULT_SAVE_ID, GameSave, create_default_game_save, get_game_save
from src.storage.memory import MemoryStorage


def velho_nox() -> NPC:
    return NPC(
        5,
        10,
        "Velho Nox",
        (
            "Velho Nox observa as arvores como se elas estivessem respirando.",
            "'Nem toda sombra pertence a quem a carrega.'",
        ),
        npc_id="velho-nox",
        location_id="floresta-do-avesso",
    )


def test_velho_nox_dialogue_before_shadow_is_unchanged() -> None:
    save = GameSave(id=DEFAULT_SAVE_ID, character_id="miko-meu")

    dialogue = get_npc_dialogue_for_state(velho_nox(), save, GameContext(location_id=DEFAULT_LOCATION_ID))

    assert dialogue == (
        "Velho Nox observa as arvores como se elas estivessem respirando.",
        "'Nem toda sombra pertence a quem a carrega.'",
    )


def test_velho_nox_dialogue_after_shadow_flag_changes() -> None:
    save = GameSave(
        id=DEFAULT_SAVE_ID,
        character_id="miko-meu",
        story_flags=["viu_sombra_na_floresta_do_avesso"],
    )

    dialogue = get_npc_dialogue_for_state(velho_nox(), save, GameContext(location_id=DEFAULT_LOCATION_ID))

    assert dialogue == VELHO_NOX_SHADOW_DIALOGUE


def test_velho_nox_dialogue_after_first_talk_uses_repeat_line() -> None:
    save = GameSave(
        id=DEFAULT_SAVE_ID,
        character_id="miko-meu",
        story_flags=["falou_com_velho_nox"],
    )

    dialogue = get_npc_dialogue_for_state(velho_nox(), save, GameContext(location_id=DEFAULT_LOCATION_ID))

    assert dialogue == VELHO_NOX_REPEAT_DIALOGUE


def test_apply_npc_interaction_effects_adds_velho_nox_flags() -> None:
    save = GameSave(id=DEFAULT_SAVE_ID, character_id="miko-meu")

    updated = apply_npc_interaction_effects(velho_nox(), save, GameContext(location_id=DEFAULT_LOCATION_ID))

    assert updated.story_flags == ["falou_com_velho_nox", NOX_TRAIL_MENTIONED_FLAG]
    assert updated.npc_flags == {"velho-nox": ["conhecido"]}
    assert updated.consequence_log == []


def test_velho_nox_dialogue_after_trail_investigation_changes() -> None:
    save = GameSave(
        id=DEFAULT_SAVE_ID,
        character_id="miko-meu",
        story_flags=[SHADOW_TRAIL_INVESTIGATED_FLAG],
    )

    dialogue = get_npc_dialogue_for_state(velho_nox(), save, GameContext(location_id=DEFAULT_LOCATION_ID))

    assert dialogue == VELHO_NOX_AFTER_TRAIL_DIALOGUE


def test_velho_nox_dialogue_after_entry_whisper_has_priority_over_trail() -> None:
    save = GameSave(
        id=DEFAULT_SAVE_ID,
        character_id="miko-meu",
        story_flags=[SHADOW_TRAIL_INVESTIGATED_FLAG, ENTRY_WHISPER_HEARD_FLAG],
    )

    dialogue = get_npc_dialogue_for_state(velho_nox(), save, GameContext(location_id=DEFAULT_LOCATION_ID))

    assert dialogue == VELHO_NOX_AFTER_WHISPER_DIALOGUE


def test_apply_npc_interaction_effects_after_shadow_adds_consequence_once() -> None:
    save = GameSave(
        id=DEFAULT_SAVE_ID,
        character_id="miko-meu",
        story_flags=["viu_sombra_na_floresta_do_avesso"],
    )

    apply_npc_interaction_effects(velho_nox(), save, GameContext(location_id=DEFAULT_LOCATION_ID))
    updated = apply_npc_interaction_effects(velho_nox(), save, GameContext(location_id=DEFAULT_LOCATION_ID))

    assert updated.story_flags.count("falou_com_velho_nox") == 1
    assert updated.story_flags.count(NOX_TRAIL_MENTIONED_FLAG) == 1
    assert updated.npc_flags["velho-nox"].count("conhecido") == 1
    assert updated.consequence_log == [
        {
            "id": VELHO_NOX_SHADOW_CONSEQUENCE_ID,
            "location_id": "floresta-do-avesso",
            "npc_id": "velho-nox",
            "text": VELHO_NOX_SHADOW_CONSEQUENCE_TEXT,
        }
    ]


def test_apply_npc_interaction_effects_after_whisper_adds_consequence_once() -> None:
    save = GameSave(
        id=DEFAULT_SAVE_ID,
        character_id="miko-meu",
        story_flags=[ENTRY_WHISPER_HEARD_FLAG],
    )

    apply_npc_interaction_effects(velho_nox(), save, GameContext(location_id=DEFAULT_LOCATION_ID))
    updated = apply_npc_interaction_effects(velho_nox(), save, GameContext(location_id=DEFAULT_LOCATION_ID))

    assert updated.story_flags.count("falou_com_velho_nox") == 1
    assert updated.story_flags.count(NOX_TRAIL_MENTIONED_FLAG) == 1
    assert updated.npc_flags["velho-nox"].count("conhecido") == 1
    assert updated.consequence_log == [
        {
            "id": VELHO_NOX_WHISPER_CONSEQUENCE_ID,
            "location_id": "floresta-do-avesso",
            "npc_id": "velho-nox",
            "text": VELHO_NOX_WHISPER_CONSEQUENCE_TEXT,
        }
    ]


def test_velho_nox_reaction_respects_location_id() -> None:
    save = GameSave(
        id=DEFAULT_SAVE_ID,
        character_id="miko-meu",
        story_flags=["viu_sombra_na_floresta_do_avesso"],
    )
    context = GameContext(location_id="cidade-de-pedralume")

    dialogue = get_npc_dialogue_for_state(velho_nox(), save, context)
    updated = apply_npc_interaction_effects(velho_nox(), save, context)

    assert dialogue == tuple(velho_nox().dialogues)
    assert updated.story_flags == ["viu_sombra_na_floresta_do_avesso"]
    assert updated.npc_flags == {}
    assert updated.consequence_log == []


def test_apply_npc_interaction_effects_to_storage_uses_save_layer() -> None:
    storage = MemoryStorage({"game_saves.json": {"saves": [create_default_game_save().to_dict()]}})

    apply_npc_interaction_effects_to_storage(storage, velho_nox(), GameContext(location_id=DEFAULT_LOCATION_ID))
    save = get_game_save(storage)

    assert save.story_flags == ["falou_com_velho_nox", NOX_TRAIL_MENTIONED_FLAG]
    assert save.npc_flags == {"velho-nox": ["conhecido"]}
