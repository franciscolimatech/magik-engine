"""Small narrative memory summary for the PyGame overworld.

The summary only reads flags and consequences already saved by Python. It does
not create quests, rewards, inventory changes, or mechanical effects.
"""

from __future__ import annotations

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
from src.game.save import GameSave


EMPTY_STORY_SUMMARY = "Nada ainda ecoa com clareza."


def build_story_summary(save: GameSave | None) -> tuple[str, ...]:
    if save is None:
        return (EMPTY_STORY_SUMMARY,)

    flags = set(save.story_flags)
    consequence_ids = {str(entry.get("id", "")) for entry in save.consequence_log}
    memories: list[str] = []

    if VELHO_NOX_TALKED_FLAG in flags:
        memories.append("Voce encontrou o Velho Nox na cabana alem da Clareira.")
    if NOX_TRAIL_MENTIONED_FLAG in flags:
        memories.append("Nox falou de um lugar na Clareira onde as folhas caem para cima.")
    if SHADOW_TRAIL_INVESTIGATED_FLAG in flags:
        memories.append("Voce tocou o rastro da sombra. O ar dobrou, e sua sombra se atrasou.")
    if ENTRY_WHISPER_HEARD_FLAG in flags:
        memories.append("Na Entrada, uma voz tentou repetir seu nome e errou a ultima silaba.")
    if MISALIGNED_SHADOW_ID in save.defeated_enemy_ids:
        memories.append("Na Clareira, voce enfrentou uma sombra que se movia atrasada em relacao ao mundo.")
    if VELHO_NOX_WHISPER_CONSEQUENCE_ID in consequence_ids:
        memories.append("Nox disse que a floresta respondeu. Enquanto ela erra seu nome, voce ainda e seu.")
    elif VELHO_NOX_SHADOW_CONSEQUENCE_ID in consequence_ids:
        memories.append("Nox reconheceu que algo na Floresta do Avesso ja olhou para voce.")

    return tuple(memories) if memories else (EMPTY_STORY_SUMMARY,)
