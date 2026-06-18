from src.game.narrative_conditions import (
    apply_narrative_effects,
    apply_narrative_effects_to_storage,
    conditions_met,
    normalize_conditions,
    normalize_effects,
)
from src.game.save import DEFAULT_LOCATION_ID, DEFAULT_SAVE_ID, GameSave, create_default_game_save, get_game_save
from src.storage.memory import MemoryStorage


def test_empty_conditions_are_met() -> None:
    save = GameSave(id=DEFAULT_SAVE_ID, character_id="miko-meu")

    assert conditions_met(save, {}) is True
    assert conditions_met(save, None) is True


def test_required_story_flags_work() -> None:
    save = GameSave(id=DEFAULT_SAVE_ID, character_id="miko-meu", story_flags=["falou_com_velho_nox"])

    assert conditions_met(save, {"required_story_flags": ["falou_com_velho_nox"]}) is True
    assert conditions_met(save, {"required_story_flags": ["recusou_velho_nox"]}) is False


def test_blocked_story_flags_work() -> None:
    save = GameSave(id=DEFAULT_SAVE_ID, character_id="miko-meu", story_flags=["recusou_velho_nox"])

    assert conditions_met(save, {"blocked_story_flags": ["recusou_velho_nox"]}) is False
    assert conditions_met(save, {"blocked_story_flags": ["falou_com_velho_nox"]}) is True


def test_required_world_flags_work() -> None:
    save = GameSave(id=DEFAULT_SAVE_ID, character_id="miko-meu", world_flags=["floresta_do_avesso_inquieta"])

    assert conditions_met(save, {"required_world_flags": ["floresta_do_avesso_inquieta"]}) is True
    assert conditions_met(save, {"required_world_flags": ["pedralume_em_festa"]}) is False


def test_blocked_world_flags_work() -> None:
    save = GameSave(id=DEFAULT_SAVE_ID, character_id="miko-meu", world_flags=["pedralume_em_festa"])

    assert conditions_met(save, {"blocked_world_flags": ["pedralume_em_festa"]}) is False
    assert conditions_met(save, {"blocked_world_flags": ["floresta_do_avesso_inquieta"]}) is True


def test_required_npc_flags_work() -> None:
    save = GameSave(id=DEFAULT_SAVE_ID, character_id="miko-meu", npc_flags={"velho-nox": ["conhecido"]})

    assert conditions_met(save, {"required_npc_flags": {"velho-nox": ["conhecido"]}}) is True
    assert conditions_met(save, {"required_npc_flags": {"velho-nox": ["desconfiado"]}}) is False


def test_blocked_npc_flags_work() -> None:
    save = GameSave(id=DEFAULT_SAVE_ID, character_id="miko-meu", npc_flags={"velho-nox": ["desconfiado"]})

    assert conditions_met(save, {"blocked_npc_flags": {"velho-nox": ["desconfiado"]}}) is False
    assert conditions_met(save, {"blocked_npc_flags": {"velho-nox": ["conhecido"]}}) is True


def test_normalize_conditions_accepts_partial_data() -> None:
    conditions = normalize_conditions(
        {
            "required_story_flags": "falou_com_velho_nox",
            "required_npc_flags": {"velho-nox": "conhecido"},
            "blocked_world_flags": ["", "pedralume_em_festa", "pedralume_em_festa"],
        }
    )

    assert conditions["required_story_flags"] == ["falou_com_velho_nox"]
    assert conditions["required_npc_flags"] == {"velho-nox": ["conhecido"]}
    assert conditions["blocked_world_flags"] == ["pedralume_em_festa"]


def test_effects_add_story_flags_without_duplicate() -> None:
    save = GameSave(id=DEFAULT_SAVE_ID, character_id="miko-meu")
    effects = {"add_story_flags": ["viu_sombra_na_floresta", "viu_sombra_na_floresta"]}

    apply_narrative_effects(save, effects)
    apply_narrative_effects(save, effects)

    assert save.story_flags == ["viu_sombra_na_floresta"]


def test_effects_add_world_flags_without_duplicate() -> None:
    save = GameSave(id=DEFAULT_SAVE_ID, character_id="miko-meu")
    effects = {"add_world_flags": ["floresta_do_avesso_inquieta"]}

    apply_narrative_effects(save, effects)
    apply_narrative_effects(save, effects)

    assert save.world_flags == ["floresta_do_avesso_inquieta"]


def test_effects_add_npc_flags_without_duplicate() -> None:
    save = GameSave(id=DEFAULT_SAVE_ID, character_id="miko-meu")
    effects = {"add_npc_flags": {"velho-nox": ["observando_jogador"]}}

    apply_narrative_effects(save, effects)
    apply_narrative_effects(save, effects)

    assert save.npc_flags == {"velho-nox": ["observando_jogador"]}


def test_effects_register_important_choice() -> None:
    save = GameSave(id=DEFAULT_SAVE_ID, character_id="miko-meu")
    effects = {
        "important_choice": {
            "id": "velho-nox-primeiro-contato",
            "location_id": "floresta-do-avesso",
            "npc_id": "velho-nox",
            "choice": "O jogador aceitou ouvir Velho Nox.",
        }
    }

    apply_narrative_effects(save, effects)
    apply_narrative_effects(save, effects)

    assert save.choice_history == [
        {
            "id": "velho-nox-primeiro-contato",
            "location_id": "floresta-do-avesso",
            "npc_id": "velho-nox",
            "choice": "O jogador aceitou ouvir Velho Nox.",
            "timestamp": None,
        }
    ]


def test_effects_register_narrative_consequence() -> None:
    save = GameSave(id=DEFAULT_SAVE_ID, character_id="miko-meu")
    effects = {
        "narrative_consequence": {
            "id": "velho-nox-observa",
            "location_id": "floresta-do-avesso",
            "text": "Velho Nox passou a observar o personagem com mais atencao.",
        }
    }

    apply_narrative_effects(save, effects)
    apply_narrative_effects(save, effects)

    assert save.consequence_log == [
        {
            "id": "velho-nox-observa",
            "location_id": "floresta-do-avesso",
            "npc_id": None,
            "text": "Velho Nox passou a observar o personagem com mais atencao.",
        }
    ]


def test_empty_effects_do_not_break() -> None:
    save = GameSave(id=DEFAULT_SAVE_ID, character_id="miko-meu")

    result = apply_narrative_effects(save, {})

    assert result is save
    assert save.story_flags == []
    assert save.choice_history == []


def test_normalize_effects_ignores_incomplete_entries() -> None:
    effects = normalize_effects(
        {
            "add_story_flags": ["", "viu_sombra"],
            "important_choice": {"id": "sem-texto"},
            "narrative_consequence": {"text": "Sem id."},
        }
    )

    assert effects["add_story_flags"] == ["viu_sombra"]
    assert effects["important_choice"] is None
    assert effects["narrative_consequence"] is None


def test_old_save_remains_compatible_with_conditions() -> None:
    storage = MemoryStorage(
        {
            "game_saves.json": {
                "saves": [
                    {
                        "id": DEFAULT_SAVE_ID,
                        "character_id": "miko-meu",
                        "location_id": DEFAULT_LOCATION_ID,
                    }
                ]
            }
        }
    )
    save = get_game_save(storage)

    assert conditions_met(save, {}) is True
    assert apply_narrative_effects(save, {"add_story_flags": ["primeira_flag"]}).story_flags == ["primeira_flag"]


def test_apply_narrative_effects_to_storage_uses_save_layer() -> None:
    storage = MemoryStorage({"game_saves.json": {"saves": [create_default_game_save().to_dict()]}})
    effects = {
        "add_story_flags": ["falou_com_velho_nox"],
        "add_world_flags": ["floresta_do_avesso_inquieta"],
        "add_npc_flags": {"velho-nox": ["observando_jogador"]},
        "important_choice": {
            "id": "velho-nox-primeiro-contato",
            "location_id": "floresta-do-avesso",
            "npc_id": "velho-nox",
            "choice": "O jogador aceitou ouvir Velho Nox.",
        },
        "narrative_consequence": {
            "id": "velho-nox-observa",
            "location_id": "floresta-do-avesso",
            "npc_id": "velho-nox",
            "text": "Velho Nox passou a observar o personagem.",
        },
    }

    save = apply_narrative_effects_to_storage(storage, DEFAULT_SAVE_ID, effects)
    save = apply_narrative_effects_to_storage(storage, DEFAULT_SAVE_ID, effects)

    assert save.story_flags == ["falou_com_velho_nox"]
    assert save.world_flags == ["floresta_do_avesso_inquieta"]
    assert save.npc_flags == {"velho-nox": ["observando_jogador"]}
    assert len(save.choice_history) == 1
    assert len(save.consequence_log) == 1
