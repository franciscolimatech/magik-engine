"""Small NPC reaction layer based on saved narrative state.

This module keeps NPC-specific memory outside the Overworld scene. It does not
start quests, grant rewards, change reputation, or apply mechanical effects.
"""

from __future__ import annotations

from src.game.area_interactions import (
    ENTRY_WHISPER_HEARD_FLAG,
    NOX_TRAIL_MENTIONED_FLAG,
    SHADOW_TRAIL_INVESTIGATED_FLAG,
)
from src.game.entities.npc import NPC
from src.game.game_context import GameContext
from src.game.maps.area_registry import MISALIGNED_SHADOW_ID
from src.game.narrative_conditions import apply_narrative_effects, apply_narrative_effects_to_storage
from src.game.save import DEFAULT_SAVE_ID, GameSave, get_game_save
from src.storage.types import JsonStore


VELHO_NOX_ID = "velho-nox"
FLORESTA_DO_AVESSO_ID = "floresta-do-avesso"
SHADOW_SEEN_FLAG = "viu_sombra_na_floresta_do_avesso"
VELHO_NOX_TALKED_FLAG = "falou_com_velho_nox"
VELHO_NOX_KNOWN_FLAG = "conhecido"
VELHO_NOX_SHADOW_CONSEQUENCE_ID = "velho-nox-reconhece-sombra"
VELHO_NOX_SHADOW_CONSEQUENCE_TEXT = "Velho Nox reconheceu que o personagem viu uma sombra na Floresta do Avesso."
VELHO_NOX_WHISPER_CONSEQUENCE_ID = "velho-nox-reconhece-sussurro"
VELHO_NOX_WHISPER_CONSEQUENCE_TEXT = "Velho Nox reconheceu que a floresta respondeu ao personagem na entrada."
VELHO_NOX_DEFEATED_SHADOW_CONSEQUENCE_ID = "velho-nox-reconhece-sombra-derrotada"
VELHO_NOX_DEFEATED_SHADOW_CONSEQUENCE_TEXT = "Velho Nox reconheceu que o personagem derrotou a Sombra Desalinhada."
VELHO_NOX_SHADOW_DIALOGUE = (
    "Velho Nox aperta os olhos.",
    "'Entao ela ja olhou para voce. Nao olhe de volta por muito tempo.'",
)
VELHO_NOX_REPEAT_DIALOGUE = (
    "Velho Nox ajeita o manto sem olhar diretamente para voce.",
    "'Volte quando a floresta comecar a repetir o seu nome.'",
)
VELHO_NOX_AFTER_TRAIL_DIALOGUE = (
    "Velho Nox fica em silencio por tempo demais.",
    "'Agora ela sabe que voce percebeu. Isso e diferente de apenas ser visto.'",
)
VELHO_NOX_AFTER_WHISPER_DIALOGUE = (
    "Velho Nox inclina a cabeca, como se escutasse algo atras de voce.",
    "'A floresta respondeu. Ainda baixo, ainda torto... mas respondeu.'",
    "'Enquanto ela erra seu nome, voce ainda e seu.'",
)
VELHO_NOX_AFTER_DEFEATED_SHADOW_DIALOGUE = (
    "Velho Nox ergue o rosto antes que voce diga qualquer coisa.",
    "'Entao voce cortou uma sombra que ainda nao tinha alcancado o proprio corpo.'",
    "'Isso nao mata a floresta. Mas ensina a ela que voce pode ferir o que ela envia.'",
)


def get_npc_dialogue_for_state(npc: NPC, save: GameSave | None, context: GameContext) -> tuple[str, ...]:
    if not _is_velho_nox_in_floresta(npc, context):
        return tuple(npc.dialogues)
    return get_velho_nox_reaction(save, npc)


def get_velho_nox_reaction(save: GameSave | None, npc: NPC) -> tuple[str, ...]:
    if save is not None:
        if MISALIGNED_SHADOW_ID in save.defeated_enemy_ids:
            return VELHO_NOX_AFTER_DEFEATED_SHADOW_DIALOGUE
        if ENTRY_WHISPER_HEARD_FLAG in save.story_flags:
            return VELHO_NOX_AFTER_WHISPER_DIALOGUE
        if SHADOW_TRAIL_INVESTIGATED_FLAG in save.story_flags:
            return VELHO_NOX_AFTER_TRAIL_DIALOGUE
        if SHADOW_SEEN_FLAG in save.story_flags:
            return VELHO_NOX_SHADOW_DIALOGUE
        if VELHO_NOX_TALKED_FLAG in save.story_flags:
            return VELHO_NOX_REPEAT_DIALOGUE
    return tuple(npc.dialogues)


def apply_npc_interaction_effects(npc: NPC, save: GameSave, context: GameContext) -> GameSave:
    if not _is_velho_nox_in_floresta(npc, context):
        return save
    return apply_narrative_effects(save, _velho_nox_effects(save))


def apply_npc_interaction_effects_to_storage(
    storage: JsonStore,
    npc: NPC,
    context: GameContext,
    save_id: str = DEFAULT_SAVE_ID,
) -> GameSave:
    save = get_game_save(storage, save_id)
    if not _is_velho_nox_in_floresta(npc, context):
        return save
    return apply_narrative_effects_to_storage(storage, save_id, _velho_nox_effects(save))


def _velho_nox_effects(save: GameSave) -> dict:
    effects: dict = {
        "add_story_flags": [VELHO_NOX_TALKED_FLAG, NOX_TRAIL_MENTIONED_FLAG],
        "add_npc_flags": {
            VELHO_NOX_ID: [VELHO_NOX_KNOWN_FLAG],
        },
    }
    if MISALIGNED_SHADOW_ID in save.defeated_enemy_ids:
        effects["narrative_consequence"] = {
            "id": VELHO_NOX_DEFEATED_SHADOW_CONSEQUENCE_ID,
            "location_id": FLORESTA_DO_AVESSO_ID,
            "npc_id": VELHO_NOX_ID,
            "text": VELHO_NOX_DEFEATED_SHADOW_CONSEQUENCE_TEXT,
        }
    elif ENTRY_WHISPER_HEARD_FLAG in save.story_flags:
        effects["narrative_consequence"] = {
            "id": VELHO_NOX_WHISPER_CONSEQUENCE_ID,
            "location_id": FLORESTA_DO_AVESSO_ID,
            "npc_id": VELHO_NOX_ID,
            "text": VELHO_NOX_WHISPER_CONSEQUENCE_TEXT,
        }
    elif SHADOW_SEEN_FLAG in save.story_flags:
        effects["narrative_consequence"] = {
            "id": VELHO_NOX_SHADOW_CONSEQUENCE_ID,
            "location_id": FLORESTA_DO_AVESSO_ID,
            "npc_id": VELHO_NOX_ID,
            "text": VELHO_NOX_SHADOW_CONSEQUENCE_TEXT,
        }
    return effects


def _is_velho_nox_in_floresta(npc: NPC, context: GameContext) -> bool:
    return (
        npc.npc_id == VELHO_NOX_ID
        and npc.location_id == FLORESTA_DO_AVESSO_ID
        and context.location_id == FLORESTA_DO_AVESSO_ID
    )
