"""Narrative condition and effect helpers for game saves.

This module only reads and writes narrative state in ``GameSave``. It does not
activate quests, grant rewards, change combat, or apply mechanical bonuses.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from src.game.save import (
    DEFAULT_SAVE_ID,
    GameSave,
    add_npc_flag,
    add_story_flag,
    add_world_flag,
    get_game_save,
    register_important_choice,
    register_narrative_consequence,
)
from src.storage.types import JsonStore


CONDITION_LIST_FIELDS = (
    "required_story_flags",
    "blocked_story_flags",
    "required_world_flags",
    "blocked_world_flags",
)
CONDITION_NPC_FIELDS = ("required_npc_flags", "blocked_npc_flags")


def normalize_conditions(conditions: Mapping[str, Any] | None) -> dict[str, Any]:
    data = dict(conditions or {})
    return {
        "required_story_flags": _unique_strings(data.get("required_story_flags", [])),
        "blocked_story_flags": _unique_strings(data.get("blocked_story_flags", [])),
        "required_world_flags": _unique_strings(data.get("required_world_flags", [])),
        "blocked_world_flags": _unique_strings(data.get("blocked_world_flags", [])),
        "required_npc_flags": _normalize_flag_map(data.get("required_npc_flags", {})),
        "blocked_npc_flags": _normalize_flag_map(data.get("blocked_npc_flags", {})),
    }


def conditions_met(save: GameSave, conditions: Mapping[str, Any] | None) -> bool:
    normalized = normalize_conditions(conditions)
    if not _has_all(save.story_flags, normalized["required_story_flags"]):
        return False
    if _has_any(save.story_flags, normalized["blocked_story_flags"]):
        return False
    if not _has_all(save.world_flags, normalized["required_world_flags"]):
        return False
    if _has_any(save.world_flags, normalized["blocked_world_flags"]):
        return False
    if not _npc_flags_match(save.npc_flags, normalized["required_npc_flags"], require_all=True):
        return False
    if _npc_flags_match(save.npc_flags, normalized["blocked_npc_flags"], require_all=False):
        return False
    return True


def normalize_effects(effects: Mapping[str, Any] | None) -> dict[str, Any]:
    data = dict(effects or {})
    return {
        "add_story_flags": _unique_strings(data.get("add_story_flags", [])),
        "add_world_flags": _unique_strings(data.get("add_world_flags", [])),
        "add_npc_flags": _normalize_flag_map(data.get("add_npc_flags", {})),
        "important_choice": _normalize_choice(data.get("important_choice")),
        "narrative_consequence": _normalize_consequence(data.get("narrative_consequence")),
    }


def apply_narrative_effects(save: GameSave, effects: Mapping[str, Any] | None) -> GameSave:
    normalized = normalize_effects(effects)
    for flag in normalized["add_story_flags"]:
        _append_unique(save.story_flags, flag)
    for flag in normalized["add_world_flags"]:
        _append_unique(save.world_flags, flag)
    for npc_id, flags in normalized["add_npc_flags"].items():
        npc_flags = save.npc_flags.setdefault(npc_id, [])
        for flag in flags:
            _append_unique(npc_flags, flag)
    choice = normalized["important_choice"]
    if choice is not None and not _entry_exists(save.choice_history, choice["id"]):
        save.choice_history.append(choice)
    consequence = normalized["narrative_consequence"]
    if consequence is not None and not _entry_exists(save.consequence_log, consequence["id"]):
        save.consequence_log.append(consequence)
    return save


def apply_narrative_effects_to_storage(
    storage: JsonStore,
    save_id: str = DEFAULT_SAVE_ID,
    effects: Mapping[str, Any] | None = None,
) -> GameSave:
    normalized = normalize_effects(effects)
    for flag in normalized["add_story_flags"]:
        add_story_flag(storage, save_id, flag)
    for flag in normalized["add_world_flags"]:
        add_world_flag(storage, save_id, flag)
    for npc_id, flags in normalized["add_npc_flags"].items():
        for flag in flags:
            add_npc_flag(storage, save_id, npc_id, flag)
    choice = normalized["important_choice"]
    if choice is not None:
        register_important_choice(
            storage,
            save_id,
            choice_id=choice["id"],
            choice=choice["choice"],
            location_id=choice["location_id"],
            npc_id=choice["npc_id"],
            timestamp=choice["timestamp"],
        )
    consequence = normalized["narrative_consequence"]
    if consequence is not None:
        register_narrative_consequence(
            storage,
            save_id,
            consequence_id=consequence["id"],
            text=consequence["text"],
            location_id=consequence["location_id"],
            npc_id=consequence["npc_id"],
        )
    return get_game_save(storage, save_id)


def _normalize_choice(value: Any) -> dict[str, Any] | None:
    if not isinstance(value, Mapping):
        return None
    choice_id = str(value.get("id", "")).strip()
    choice_text = str(value.get("choice", "")).strip()
    if not choice_id or not choice_text:
        return None
    return {
        "id": choice_id,
        "location_id": _optional_text(value.get("location_id")),
        "npc_id": _optional_text(value.get("npc_id")),
        "choice": choice_text,
        "timestamp": _optional_text(value.get("timestamp")),
    }


def _normalize_consequence(value: Any) -> dict[str, Any] | None:
    if not isinstance(value, Mapping):
        return None
    consequence_id = str(value.get("id", "")).strip()
    text = str(value.get("text", "")).strip()
    if not consequence_id or not text:
        return None
    return {
        "id": consequence_id,
        "location_id": _optional_text(value.get("location_id")),
        "npc_id": _optional_text(value.get("npc_id")),
        "text": text,
    }


def _normalize_flag_map(value: Any) -> dict[str, list[str]]:
    if not isinstance(value, Mapping):
        return {}
    result: dict[str, list[str]] = {}
    for raw_key, raw_flags in value.items():
        key = str(raw_key).strip()
        flags = _unique_strings(raw_flags)
        if key and flags:
            result[key] = flags
    return result


def _unique_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        candidates = [value]
    elif isinstance(value, (list, tuple, set)):
        candidates = list(value)
    else:
        return []
    result: list[str] = []
    for item in candidates:
        cleaned = str(item).strip()
        if cleaned and cleaned not in result:
            result.append(cleaned)
    return result


def _has_all(current: list[str], required: list[str]) -> bool:
    return all(flag in current for flag in required)


def _has_any(current: list[str], blocked: list[str]) -> bool:
    return any(flag in current for flag in blocked)


def _npc_flags_match(current: dict[str, list[str]], expected: dict[str, list[str]], require_all: bool) -> bool:
    if not expected:
        return True if require_all else False
    for npc_id, flags in expected.items():
        current_flags = current.get(npc_id, [])
        if require_all and not _has_all(current_flags, flags):
            return False
        if not require_all and _has_any(current_flags, flags):
            return True
    return True if require_all else False


def _append_unique(values: list[str], value: str) -> None:
    cleaned = value.strip()
    if cleaned and cleaned not in values:
        values.append(cleaned)


def _entry_exists(entries: list[dict[str, Any]], entry_id: str) -> bool:
    return any(str(entry.get("id", "")).casefold() == entry_id.casefold() for entry in entries)


def _optional_text(value: Any) -> str | None:
    if value is None:
        return None
    cleaned = str(value).strip()
    return cleaned or None
