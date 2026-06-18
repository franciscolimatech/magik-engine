"""Small persistent save layer for the 2D game prototype.

Game saves are local player state. They do not activate quests, grant rewards,
apply item effects, or change combat rules.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from src.core.character import MIKO_ID
from src.core.world import get_location_by_id
from src.game.maps.area_registry import DEFAULT_AREA_ID, resolve_area
from src.storage.types import JsonStore


SAVE_FILENAME = "game_saves.json"
DEFAULT_SAVE_ID = "default"
DEFAULT_LOCATION_ID = "floresta-do-avesso"
DEFAULT_PLAYER_POSITION = (5, 4)


@dataclass
class GameSave:
    id: str
    character_id: str
    campaign_id: str | None = None
    session_id: str | None = None
    location_id: str = DEFAULT_LOCATION_ID
    area_id: str = DEFAULT_AREA_ID
    player_position: dict[str, int] = field(default_factory=lambda: _position_dict(DEFAULT_PLAYER_POSITION))
    visited_locations: list[str] = field(default_factory=list)
    triggered_events: list[str] = field(default_factory=list)
    known_quest_ids: list[str] = field(default_factory=list)
    active_quest_ids: list[str] = field(default_factory=list)
    completed_quest_ids: list[str] = field(default_factory=list)
    defeated_enemy_ids: list[str] = field(default_factory=list)
    story_flags: list[str] = field(default_factory=list)
    world_flags: list[str] = field(default_factory=list)
    npc_flags: dict[str, list[str]] = field(default_factory=dict)
    choice_history: list[dict[str, Any]] = field(default_factory=list)
    consequence_log: list[dict[str, Any]] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    @property
    def position(self) -> tuple[int, int]:
        return int(self.player_position.get("x", 0)), int(self.player_position.get("y", 0))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GameSave":
        try:
            save = cls(
                id=str(data["id"]),
                character_id=str(data.get("character_id", MIKO_ID)),
                campaign_id=data.get("campaign_id"),
                session_id=data.get("session_id"),
                location_id=str(data.get("location_id", DEFAULT_LOCATION_ID)),
                area_id=_resolve_valid_area_id(data.get("area_id", DEFAULT_AREA_ID)),
                player_position=_normalize_position(data.get("player_position", {})),
                visited_locations=list(data.get("visited_locations", [])),
                triggered_events=list(data.get("triggered_events", [])),
                known_quest_ids=list(data.get("known_quest_ids", [])),
                active_quest_ids=list(data.get("active_quest_ids", [])),
                completed_quest_ids=list(data.get("completed_quest_ids", [])),
                defeated_enemy_ids=list(data.get("defeated_enemy_ids", [])),
                story_flags=list(data.get("story_flags", [])),
                world_flags=list(data.get("world_flags", [])),
                npc_flags=_normalize_npc_flags(data.get("npc_flags", {})),
                choice_history=_normalize_dict_list(data.get("choice_history", [])),
                consequence_log=_normalize_dict_list(data.get("consequence_log", [])),
                notes=list(data.get("notes", [])),
            )
        except KeyError as exc:
            raise ValueError(f"Save do jogo invalido: campo ausente {exc}.") from exc
        validate_game_save(save)
        return save


def default_game_saves_data() -> dict[str, Any]:
    return {"saves": []}


def create_default_game_save(
    character_id: str = MIKO_ID,
    campaign_id: str | None = None,
    session_id: str | None = None,
    location_id: str = DEFAULT_LOCATION_ID,
    area_id: str = DEFAULT_AREA_ID,
    position: tuple[int, int] = DEFAULT_PLAYER_POSITION,
) -> GameSave:
    return GameSave(
        id=DEFAULT_SAVE_ID,
        character_id=character_id or MIKO_ID,
        campaign_id=campaign_id,
        session_id=session_id,
        location_id=location_id or DEFAULT_LOCATION_ID,
        area_id=_resolve_valid_area_id(area_id),
        player_position=_position_dict(position),
        visited_locations=_unique_strings([location_id or DEFAULT_LOCATION_ID]),
    )


def load_game_saves(storage: JsonStore) -> list[GameSave]:
    try:
        data = storage.read_json(SAVE_FILENAME, default=default_game_saves_data())
        saves_data = _read_collection(data)
        saves = [GameSave.from_dict(item) for item in saves_data]
    except (TypeError, ValueError):
        return []
    validate_unique_save_ids(saves)
    return saves


def save_game_saves(storage: JsonStore, saves: list[GameSave]) -> None:
    validate_unique_save_ids(saves)
    storage.write_json(SAVE_FILENAME, {"saves": [save.to_dict() for save in saves]})


def get_game_save(storage: JsonStore, save_id: str = DEFAULT_SAVE_ID) -> GameSave:
    normalized = save_id.strip().casefold()
    for save in load_game_saves(storage):
        if save.id.casefold() == normalized:
            return save
    raise ValueError(f"Save do jogo nao encontrado: {save_id}.")


def load_or_create_default_game_save(
    storage: JsonStore,
    character_id: str = MIKO_ID,
    campaign_id: str | None = None,
    session_id: str | None = None,
    location_id: str = DEFAULT_LOCATION_ID,
    area_id: str = DEFAULT_AREA_ID,
) -> GameSave:
    saves = load_game_saves(storage)
    for save in saves:
        if save.id == DEFAULT_SAVE_ID:
            return save
    save = create_default_game_save(
        character_id=character_id,
        campaign_id=campaign_id,
        session_id=session_id,
        location_id=location_id,
        area_id=area_id,
    )
    saves.append(save)
    save_game_saves(storage, saves)
    return save


def sync_game_save_context(
    storage: JsonStore,
    save_id: str = DEFAULT_SAVE_ID,
    character_id: str = MIKO_ID,
    campaign_id: str | None = None,
    session_id: str | None = None,
    location_id: str = DEFAULT_LOCATION_ID,
    area_id: str | None = None,
) -> GameSave:
    save = _get_or_create_save(storage, save_id, character_id, campaign_id, session_id, location_id)
    save.character_id = character_id or MIKO_ID
    save.campaign_id = campaign_id
    save.session_id = session_id
    save.location_id = location_id or DEFAULT_LOCATION_ID
    save.area_id = _resolve_valid_area_id(area_id or save.area_id)
    if save.location_id not in save.visited_locations:
        save.visited_locations.append(save.location_id)
    _replace_save(storage, save)
    return save


def initialize_character_starting_save(
    storage: JsonStore,
    character: Any,
    campaign_id: str | None = None,
    session_id: str | None = None,
    fallback_location_id: str = DEFAULT_LOCATION_ID,
) -> GameSave:
    """Prepare the default save for a new game character.

    This updates only the runtime save state. The character origin remains stored
    on the character sheet, while the current location remains stored here.
    Existing progress lists and player position are preserved when a save already
    exists.
    """
    character_id = str(getattr(character, "id", "") or MIKO_ID)
    location_id = _resolve_valid_location_id(
        storage,
        getattr(character, "origin_location_id", None),
        fallback_location_id,
    )
    saves = load_game_saves(storage)
    for save in saves:
        if save.id == DEFAULT_SAVE_ID:
            save.character_id = character_id
            save.campaign_id = campaign_id
            save.session_id = session_id
            save.location_id = location_id
            if location_id not in save.visited_locations:
                save.visited_locations.append(location_id)
            _replace_save(storage, save)
            return save
    save = create_default_game_save(
        character_id=character_id,
        campaign_id=campaign_id,
        session_id=session_id,
        location_id=location_id,
    )
    saves.append(save)
    save_game_saves(storage, saves)
    return save


def update_player_position(
    storage: JsonStore,
    save_id: str = DEFAULT_SAVE_ID,
    x: int = 0,
    y: int = 0,
) -> GameSave:
    save = _get_or_create_save(storage, save_id)
    save.player_position = _position_dict((x, y))
    _replace_save(storage, save)
    return save


def register_current_area(
    storage: JsonStore,
    save_id: str = DEFAULT_SAVE_ID,
    area_id: str = DEFAULT_AREA_ID,
) -> GameSave:
    save = _get_or_create_save(storage, save_id)
    save.area_id = _resolve_valid_area_id(area_id)
    _replace_save(storage, save)
    return save


def update_area_and_player_position(
    storage: JsonStore,
    save_id: str = DEFAULT_SAVE_ID,
    area_id: str = DEFAULT_AREA_ID,
    x: int = DEFAULT_PLAYER_POSITION[0],
    y: int = DEFAULT_PLAYER_POSITION[1],
    location_id: str | None = None,
) -> GameSave:
    save = _get_or_create_save(storage, save_id)
    save.area_id = _resolve_valid_area_id(area_id)
    save.player_position = _position_dict((x, y))
    if location_id is not None:
        cleaned_location = location_id.strip() or DEFAULT_LOCATION_ID
        save.location_id = cleaned_location
        if cleaned_location not in save.visited_locations:
            save.visited_locations.append(cleaned_location)
    _replace_save(storage, save)
    return save


def register_triggered_event(
    storage: JsonStore,
    save_id: str = DEFAULT_SAVE_ID,
    event_id: str = "",
) -> GameSave:
    save = _get_or_create_save(storage, save_id)
    cleaned = event_id.strip()
    if cleaned and cleaned not in save.triggered_events:
        save.triggered_events.append(cleaned)
        _replace_save(storage, save)
    return save


def register_current_location(
    storage: JsonStore,
    save_id: str = DEFAULT_SAVE_ID,
    location_id: str = DEFAULT_LOCATION_ID,
) -> GameSave:
    save = _get_or_create_save(storage, save_id)
    cleaned = location_id.strip() or DEFAULT_LOCATION_ID
    save.location_id = cleaned
    if cleaned not in save.visited_locations:
        save.visited_locations.append(cleaned)
    _replace_save(storage, save)
    return save


def register_defeated_enemy(
    storage: JsonStore,
    save_id: str = DEFAULT_SAVE_ID,
    enemy_id: str = "",
) -> GameSave:
    save = _get_or_create_save(storage, save_id)
    cleaned = enemy_id.strip()
    if cleaned and cleaned not in save.defeated_enemy_ids:
        save.defeated_enemy_ids.append(cleaned)
        _replace_save(storage, save)
    return save


def add_story_flag(
    storage: JsonStore,
    save_id: str = DEFAULT_SAVE_ID,
    flag: str = "",
) -> GameSave:
    save = _get_or_create_save(storage, save_id)
    _append_unique(save.story_flags, flag)
    _replace_save(storage, save)
    return save


def add_world_flag(
    storage: JsonStore,
    save_id: str = DEFAULT_SAVE_ID,
    flag: str = "",
) -> GameSave:
    save = _get_or_create_save(storage, save_id)
    _append_unique(save.world_flags, flag)
    _replace_save(storage, save)
    return save


def add_npc_flag(
    storage: JsonStore,
    save_id: str = DEFAULT_SAVE_ID,
    npc_id: str = "",
    flag: str = "",
) -> GameSave:
    save = _get_or_create_save(storage, save_id)
    cleaned_npc_id = npc_id.strip()
    if cleaned_npc_id:
        flags = save.npc_flags.setdefault(cleaned_npc_id, [])
        _append_unique(flags, flag)
        if not flags:
            save.npc_flags.pop(cleaned_npc_id, None)
    _replace_save(storage, save)
    return save


def has_story_flag(storage: JsonStore, save_id: str = DEFAULT_SAVE_ID, flag: str = "") -> bool:
    return _has_flag(get_game_save(storage, save_id).story_flags, flag)


def has_world_flag(storage: JsonStore, save_id: str = DEFAULT_SAVE_ID, flag: str = "") -> bool:
    return _has_flag(get_game_save(storage, save_id).world_flags, flag)


def has_npc_flag(storage: JsonStore, save_id: str = DEFAULT_SAVE_ID, npc_id: str = "", flag: str = "") -> bool:
    save = get_game_save(storage, save_id)
    return _has_flag(save.npc_flags.get(npc_id.strip(), []), flag)


def register_important_choice(
    storage: JsonStore,
    save_id: str = DEFAULT_SAVE_ID,
    choice_id: str = "",
    choice: str = "",
    location_id: str | None = None,
    npc_id: str | None = None,
    timestamp: str | None = None,
) -> GameSave:
    save = _get_or_create_save(storage, save_id)
    cleaned_id = choice_id.strip()
    cleaned_choice = choice.strip()
    if cleaned_id and cleaned_choice and not _entry_exists(save.choice_history, cleaned_id):
        save.choice_history.append(
            {
                "id": cleaned_id,
                "location_id": location_id,
                "npc_id": npc_id,
                "choice": cleaned_choice,
                "timestamp": timestamp,
            }
        )
        _replace_save(storage, save)
    return save


def register_narrative_consequence(
    storage: JsonStore,
    save_id: str = DEFAULT_SAVE_ID,
    consequence_id: str = "",
    text: str = "",
    location_id: str | None = None,
    npc_id: str | None = None,
) -> GameSave:
    save = _get_or_create_save(storage, save_id)
    cleaned_id = consequence_id.strip()
    cleaned_text = text.strip()
    if cleaned_id and cleaned_text and not _entry_exists(save.consequence_log, cleaned_id):
        save.consequence_log.append(
            {
                "id": cleaned_id,
                "location_id": location_id,
                "npc_id": npc_id,
                "text": cleaned_text,
            }
        )
        _replace_save(storage, save)
    return save


def list_relevant_flags(storage: JsonStore, save_id: str = DEFAULT_SAVE_ID, npc_id: str | None = None) -> dict[str, Any]:
    save = get_game_save(storage, save_id)
    result: dict[str, Any] = {
        "story_flags": list(save.story_flags),
        "world_flags": list(save.world_flags),
        "npc_flags": dict(save.npc_flags),
    }
    if npc_id is not None:
        result["npc_flags"] = {npc_id: list(save.npc_flags.get(npc_id, []))}
    return result


def validate_unique_save_ids(saves: list[GameSave]) -> None:
    seen: set[str] = set()
    for save in saves:
        normalized = save.id.strip().casefold()
        if not normalized:
            raise ValueError("Id do save do jogo e obrigatorio.")
        if normalized in seen:
            raise ValueError(f"Id de save duplicado: {save.id}.")
        seen.add(normalized)


def validate_game_save(save: GameSave) -> None:
    if not save.id.strip():
        raise ValueError("Id do save do jogo e obrigatorio.")
    if not save.character_id.strip():
        raise ValueError("character_id do save e obrigatorio.")
    if not save.location_id.strip():
        raise ValueError("location_id do save e obrigatorio.")
    if not save.area_id.strip():
        raise ValueError("area_id do save e obrigatorio.")
    _normalize_position(save.player_position)
    for field_name in (
        "visited_locations",
        "triggered_events",
        "known_quest_ids",
        "active_quest_ids",
        "completed_quest_ids",
        "defeated_enemy_ids",
        "story_flags",
        "world_flags",
        "notes",
    ):
        if not all(isinstance(item, str) for item in getattr(save, field_name)):
            raise ValueError(f"{field_name} deve conter apenas strings.")
    if not all(isinstance(npc_id, str) and isinstance(flags, list) for npc_id, flags in save.npc_flags.items()):
        raise ValueError("npc_flags deve ser um objeto com listas de strings.")
    if not all(all(isinstance(flag, str) for flag in flags) for flags in save.npc_flags.values()):
        raise ValueError("npc_flags deve conter apenas strings.")
    if not all(isinstance(item, dict) for item in save.choice_history):
        raise ValueError("choice_history deve conter apenas objetos JSON.")
    if not all(isinstance(item, dict) for item in save.consequence_log):
        raise ValueError("consequence_log deve conter apenas objetos JSON.")


def _get_or_create_save(
    storage: JsonStore,
    save_id: str,
    character_id: str = MIKO_ID,
    campaign_id: str | None = None,
    session_id: str | None = None,
    location_id: str = DEFAULT_LOCATION_ID,
    area_id: str = DEFAULT_AREA_ID,
) -> GameSave:
    saves = load_game_saves(storage)
    normalized = save_id.strip().casefold()
    for save in saves:
        if save.id.casefold() == normalized:
            return save
    save = create_default_game_save(character_id, campaign_id, session_id, location_id, area_id)
    save.id = save_id.strip() or DEFAULT_SAVE_ID
    saves.append(save)
    save_game_saves(storage, saves)
    return save


def _replace_save(storage: JsonStore, updated_save: GameSave) -> None:
    saves = load_game_saves(storage)
    replaced = False
    for index, save in enumerate(saves):
        if save.id.casefold() == updated_save.id.casefold():
            saves[index] = updated_save
            replaced = True
            break
    if not replaced:
        saves.append(updated_save)
    save_game_saves(storage, saves)


def _read_collection(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, dict):
        collection = data.get("saves", [])
    elif isinstance(data, list):
        collection = data
    else:
        raise ValueError("game_saves.json deve conter uma lista ou um objeto com a chave 'saves'.")
    if not isinstance(collection, list):
        raise ValueError("A chave 'saves' em game_saves.json deve conter uma lista.")
    if not all(isinstance(item, dict) for item in collection):
        raise ValueError("Cada save em game_saves.json deve ser um objeto JSON.")
    return collection


def _normalize_position(value: Any) -> dict[str, int]:
    if not isinstance(value, dict):
        return _position_dict(DEFAULT_PLAYER_POSITION)
    try:
        return {"x": int(value.get("x", DEFAULT_PLAYER_POSITION[0])), "y": int(value.get("y", DEFAULT_PLAYER_POSITION[1]))}
    except (TypeError, ValueError):
        return _position_dict(DEFAULT_PLAYER_POSITION)


def _position_dict(position: tuple[int, int]) -> dict[str, int]:
    x, y = position
    return {"x": int(x), "y": int(y)}


def _normalize_npc_flags(value: Any) -> dict[str, list[str]]:
    if not isinstance(value, dict):
        return {}
    result: dict[str, list[str]] = {}
    for npc_id, flags in value.items():
        if not isinstance(npc_id, str) or not isinstance(flags, list):
            continue
        result[npc_id] = _unique_strings([flag for flag in flags if isinstance(flag, str)])
    return result


def _normalize_dict_list(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _unique_strings(values: list[str]) -> list[str]:
    result: list[str] = []
    for value in values:
        if isinstance(value, str) and value and value not in result:
            result.append(value)
    return result


def _append_unique(values: list[str], value: str) -> None:
    cleaned = value.strip()
    if cleaned and cleaned not in values:
        values.append(cleaned)


def _has_flag(values: list[str], flag: str) -> bool:
    return flag.strip() in values


def _entry_exists(entries: list[dict[str, Any]], entry_id: str) -> bool:
    return any(str(entry.get("id", "")).casefold() == entry_id.casefold() for entry in entries)


def _resolve_valid_location_id(storage: JsonStore, candidate: Any, fallback: str) -> str:
    for value in (candidate, fallback, DEFAULT_LOCATION_ID):
        cleaned = str(value or "").strip()
        if not cleaned:
            continue
        try:
            return get_location_by_id(storage, cleaned).id
        except ValueError:
            continue
    return DEFAULT_LOCATION_ID


def _resolve_valid_area_id(candidate: Any) -> str:
    return resolve_area(str(candidate or DEFAULT_AREA_ID)).id
