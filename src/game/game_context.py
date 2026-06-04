"""Runtime context for the experimental 2D game layer."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from src.core.character import MIKO_ID, get_character
from src.game.settings import PLAYER_NAME_FALLBACK
from src.storage.json_storage import JSONStorage
from src.storage.types import JsonStore


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = PROJECT_ROOT / "data"
DEFAULT_MAP_NAME = "Mapa de Teste"


@dataclass(frozen=True)
class GameContext:
    character_id: str = MIKO_ID
    campaign_id: str | None = None
    campaign_session_id: str | None = None
    map_name: str = DEFAULT_MAP_NAME
    player_name: str = PLAYER_NAME_FALLBACK

    @classmethod
    def from_env(
        cls,
        env: Mapping[str, str] | None = None,
        storage: JsonStore | None = None,
        map_name: str = DEFAULT_MAP_NAME,
    ) -> "GameContext":
        values = env if env is not None else os.environ
        character_id = _env_text(values, "MAGIK_GAME_CHARACTER_ID") or MIKO_ID
        campaign_id = _env_text(values, "MAGIK_GAME_CAMPAIGN_ID")
        campaign_session_id = _env_text(values, "MAGIK_GAME_SESSION_ID")
        return cls(
            character_id=character_id,
            campaign_id=campaign_id,
            campaign_session_id=campaign_session_id,
            map_name=map_name,
            player_name=load_player_name(character_id, storage),
        )

    @property
    def has_campaign_session(self) -> bool:
        return bool(self.campaign_id and self.campaign_session_id)

    @property
    def campaign_label(self) -> str:
        if not self.campaign_id:
            return "Sem campanha ativa"
        return f"Campanha: {self.campaign_id}"

    @property
    def session_label(self) -> str:
        if not self.campaign_session_id:
            return ""
        return f"Sessao: {self.campaign_session_id}"

    def with_character(self, character_id: str, storage: JsonStore | None = None) -> "GameContext":
        cleaned_id = character_id.strip() or MIKO_ID
        return GameContext(
            character_id=cleaned_id,
            campaign_id=self.campaign_id,
            campaign_session_id=self.campaign_session_id,
            map_name=self.map_name,
            player_name=load_player_name(cleaned_id, storage),
        )


def load_player_name(character_id: str = MIKO_ID, storage: JsonStore | None = None) -> str:
    resolved_storage = storage or JSONStorage(DATA_PATH)
    try:
        return get_character(resolved_storage, character_id).name
    except ValueError:
        return PLAYER_NAME_FALLBACK


def _env_text(env: Mapping[str, str], key: str) -> str | None:
    value = env.get(key, "").strip()
    return value or None
