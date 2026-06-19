from src.game.area_interactions import (
    ENTRY_WHISPER_HEARD_FLAG,
    NOX_TRAIL_MENTIONED_FLAG,
    SHADOW_TRAIL_INTERACTION_ID,
    SHADOW_TRAIL_INVESTIGATED_FLAG,
    WHISPERING_TREE_INTERACTION_ID,
    apply_area_interaction_effects_to_storage,
    area_interaction_available,
    get_area_interaction,
    list_area_interactions,
)
from src.game.save import DEFAULT_SAVE_ID, GameSave, get_game_save
from src.storage.memory import MemoryStorage


def test_shadow_trail_interaction_is_declared_for_clearing() -> None:
    interactions = list_area_interactions("floresta-do-avesso-clareira")

    assert [interaction.id for interaction in interactions] == [SHADOW_TRAIL_INTERACTION_ID]
    interaction = interactions[0]
    assert interaction.area_id == "floresta-do-avesso-clareira"
    assert interaction.position == (8, 5)
    assert interaction.label == "investigar rastro"
    assert interaction.marker_style == "rune"
    assert interaction.repeatable is True


def test_whispering_tree_interaction_is_declared_for_entry() -> None:
    interactions = list_area_interactions("floresta-do-avesso-entrada")

    assert [interaction.id for interaction in interactions] == [WHISPERING_TREE_INTERACTION_ID]
    interaction = interactions[0]
    assert interaction.area_id == "floresta-do-avesso-entrada"
    assert interaction.position == (7, 4)
    assert interaction.label == "ouvir sussurro"
    assert interaction.marker_style == "whisper"
    assert interaction.repeatable is True


def test_shadow_trail_interaction_requires_nox_hint() -> None:
    interaction = get_area_interaction(SHADOW_TRAIL_INTERACTION_ID)
    save_without_hint = GameSave(id=DEFAULT_SAVE_ID, character_id="miko-meu")
    save_with_hint = GameSave(
        id=DEFAULT_SAVE_ID,
        character_id="miko-meu",
        story_flags=[NOX_TRAIL_MENTIONED_FLAG],
    )

    assert area_interaction_available(interaction, save_without_hint, "floresta-do-avesso") is False
    assert area_interaction_available(interaction, save_with_hint, "floresta-do-avesso") is True


def test_whispering_tree_interaction_requires_shadow_trail_investigation() -> None:
    interaction = get_area_interaction(WHISPERING_TREE_INTERACTION_ID)
    save_without_trail = GameSave(id=DEFAULT_SAVE_ID, character_id="miko-meu")
    save_with_trail = GameSave(
        id=DEFAULT_SAVE_ID,
        character_id="miko-meu",
        story_flags=[SHADOW_TRAIL_INVESTIGATED_FLAG],
    )

    assert area_interaction_available(interaction, save_without_trail, "floresta-do-avesso") is False
    assert area_interaction_available(interaction, save_with_trail, "floresta-do-avesso") is True


def test_shadow_trail_interaction_respects_location() -> None:
    interaction = get_area_interaction(SHADOW_TRAIL_INTERACTION_ID)
    save = GameSave(
        id=DEFAULT_SAVE_ID,
        character_id="miko-meu",
        story_flags=[NOX_TRAIL_MENTIONED_FLAG],
    )

    assert area_interaction_available(interaction, save, "cidade-de-pedralume") is False


def test_shadow_trail_interaction_effects_are_idempotent() -> None:
    interaction = get_area_interaction(SHADOW_TRAIL_INTERACTION_ID)
    storage = MemoryStorage(
        {
            "game_saves.json": {
                "saves": [
                    GameSave(
                        id=DEFAULT_SAVE_ID,
                        character_id="miko-meu",
                        story_flags=[NOX_TRAIL_MENTIONED_FLAG],
                    ).to_dict()
                ]
            }
        }
    )

    apply_area_interaction_effects_to_storage(storage, interaction)
    apply_area_interaction_effects_to_storage(storage, interaction)
    save = get_game_save(storage)

    assert save.story_flags.count(SHADOW_TRAIL_INVESTIGATED_FLAG) == 1
    assert save.consequence_log == [
        {
            "id": "rastro-da-sombra-investigado",
            "location_id": "floresta-do-avesso",
            "npc_id": None,
            "text": "O personagem investigou o rastro da sombra na Clareira da Floresta do Avesso.",
        }
    ]


def test_whispering_tree_interaction_effects_are_idempotent() -> None:
    interaction = get_area_interaction(WHISPERING_TREE_INTERACTION_ID)
    storage = MemoryStorage(
        {
            "game_saves.json": {
                "saves": [
                    GameSave(
                        id=DEFAULT_SAVE_ID,
                        character_id="miko-meu",
                        story_flags=[SHADOW_TRAIL_INVESTIGATED_FLAG],
                    ).to_dict()
                ]
            }
        }
    )

    apply_area_interaction_effects_to_storage(storage, interaction)
    apply_area_interaction_effects_to_storage(storage, interaction)
    save = get_game_save(storage)

    assert save.story_flags.count(ENTRY_WHISPER_HEARD_FLAG) == 1
    assert save.consequence_log == [
        {
            "id": "sussurro-da-entrada-ouvido",
            "location_id": "floresta-do-avesso",
            "npc_id": None,
            "text": "O personagem ouviu a arvore da entrada repetir seu nome de forma errada.",
        }
    ]
