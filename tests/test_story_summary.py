from src.game.area_interactions import (
    ENTRY_WHISPER_HEARD_FLAG,
    NOX_TRAIL_MENTIONED_FLAG,
    SHADOW_TRAIL_INVESTIGATED_FLAG,
)
from src.game.maps.area_registry import MISALIGNED_SHADOW_ID
from src.game.npc_reactions import (
    VELHO_NOX_SHADOW_CONSEQUENCE_ID,
    VELHO_NOX_TALKED_FLAG,
    VELHO_NOX_WHISPER_CONSEQUENCE_ID,
)
from src.game.save import DEFAULT_SAVE_ID, GameSave
from src.game.story_summary import EMPTY_STORY_SUMMARY, build_story_summary


def test_empty_story_summary_returns_default_message() -> None:
    save = GameSave(id=DEFAULT_SAVE_ID, character_id="miko-meu")

    assert build_story_summary(save) == (EMPTY_STORY_SUMMARY,)


def test_story_summary_includes_velho_nox_memory() -> None:
    save = GameSave(id=DEFAULT_SAVE_ID, character_id="miko-meu", story_flags=[VELHO_NOX_TALKED_FLAG])

    summary = build_story_summary(save)

    assert any("Velho Nox" in memory for memory in summary)


def test_story_summary_includes_clearing_hint_memory() -> None:
    save = GameSave(id=DEFAULT_SAVE_ID, character_id="miko-meu", story_flags=[NOX_TRAIL_MENTIONED_FLAG])

    summary = build_story_summary(save)

    assert any("folhas caem para cima" in memory for memory in summary)


def test_story_summary_includes_shadow_trail_memory() -> None:
    save = GameSave(id=DEFAULT_SAVE_ID, character_id="miko-meu", story_flags=[SHADOW_TRAIL_INVESTIGATED_FLAG])

    summary = build_story_summary(save)

    assert any("rastro da sombra" in memory for memory in summary)


def test_story_summary_includes_entry_whisper_memory() -> None:
    save = GameSave(id=DEFAULT_SAVE_ID, character_id="miko-meu", story_flags=[ENTRY_WHISPER_HEARD_FLAG])

    summary = build_story_summary(save)

    assert any("errou a ultima silaba" in memory for memory in summary)


def test_story_summary_includes_misaligned_shadow_defeat_memory() -> None:
    save = GameSave(id=DEFAULT_SAVE_ID, character_id="miko-meu", defeated_enemy_ids=[MISALIGNED_SHADOW_ID])

    summary = build_story_summary(save)

    assert any("sombra que se movia atrasada" in memory for memory in summary)


def test_story_summary_omits_misaligned_shadow_defeat_memory_before_defeat() -> None:
    save = GameSave(id=DEFAULT_SAVE_ID, character_id="miko-meu", story_flags=[ENTRY_WHISPER_HEARD_FLAG])

    summary = build_story_summary(save)

    assert not any("sombra que se movia atrasada" in memory for memory in summary)


def test_story_summary_includes_nox_whisper_consequence() -> None:
    save = GameSave(
        id=DEFAULT_SAVE_ID,
        character_id="miko-meu",
        consequence_log=[
            {
                "id": VELHO_NOX_WHISPER_CONSEQUENCE_ID,
                "location_id": "floresta-do-avesso",
                "npc_id": "velho-nox",
                "text": "Velho Nox reconheceu que a floresta respondeu ao personagem na entrada.",
            }
        ],
    )

    summary = build_story_summary(save)

    assert any("floresta respondeu" in memory for memory in summary)


def test_story_summary_includes_shadow_consequence_when_whisper_is_absent() -> None:
    save = GameSave(
        id=DEFAULT_SAVE_ID,
        character_id="miko-meu",
        consequence_log=[
            {
                "id": VELHO_NOX_SHADOW_CONSEQUENCE_ID,
                "location_id": "floresta-do-avesso",
                "npc_id": "velho-nox",
                "text": "Velho Nox reconheceu que o personagem viu uma sombra na Floresta do Avesso.",
            }
        ],
    )

    summary = build_story_summary(save)

    assert any("ja olhou para voce" in memory for memory in summary)
