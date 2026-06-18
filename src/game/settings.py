"""Game settings for the experimental PyGame prototype."""

from __future__ import annotations

import os
from typing import Any, Mapping

from src.storage.types import JsonStore


WINDOW_TITLE = "MAGIK Engine"
SCREEN_WIDTH = 640
SCREEN_HEIGHT = 480
FALLBACK_WINDOW_WIDTH = 1280
FALLBACK_WINDOW_HEIGHT = 720
MIN_SCREEN_WIDTH = 800
MIN_SCREEN_HEIGHT = 450
MAX_SCREEN_WIDTH = 3840
MAX_SCREEN_HEIGHT = 2160
AUTO_WINDOW_SCALE = 0.9
DEFAULT_ASPECT_RATIO = 16 / 9
TILE_SIZE = 32
FPS = 60

PLAYER_NAME_FALLBACK = "Aventureiro"
GAME_SETTINGS_FILENAME = "game_settings.json"
DISPLAY_MODE_ENV = "MAGIK_GAME_DISPLAY_MODE"
DISPLAY_MODE_WINDOWED = "windowed"
DISPLAY_MODE_FULLSCREEN = "fullscreen"
DISPLAY_MODE_BORDERLESS = "borderless"
DEFAULT_DISPLAY_MODE = DISPLAY_MODE_WINDOWED
DISPLAY_MODES = (DISPLAY_MODE_WINDOWED, DISPLAY_MODE_FULLSCREEN, DISPLAY_MODE_BORDERLESS)
DISPLAY_MODE_LABELS = {
    DISPLAY_MODE_WINDOWED: "Janela",
    DISPLAY_MODE_FULLSCREEN: "Tela cheia",
    DISPLAY_MODE_BORDERLESS: "Janela sem borda",
}


def get_game_resolution(
    env: Mapping[str, str] | None = None,
    display_size: tuple[int, int] | None = None,
) -> tuple[int, int]:
    values = env if env is not None else os.environ
    width = _read_dimension(values.get("MAGIK_GAME_WIDTH"), MIN_SCREEN_WIDTH, MAX_SCREEN_WIDTH)
    height = _read_dimension(values.get("MAGIK_GAME_HEIGHT"), MIN_SCREEN_HEIGHT, MAX_SCREEN_HEIGHT)
    if width is not None and height is not None:
        return width, height
    if display_size is not None:
        return calculate_auto_window_size(display_size[0], display_size[1])
    return FALLBACK_WINDOW_WIDTH, FALLBACK_WINDOW_HEIGHT


def get_game_display_mode(env: Mapping[str, str] | None = None, storage: JsonStore | None = None) -> str:
    values = env if env is not None else os.environ
    env_value = values.get(DISPLAY_MODE_ENV)
    if env_value is not None and env_value.strip():
        return normalize_display_mode(env_value)
    settings = load_game_settings(storage) if storage is not None else default_game_settings_data()
    return normalize_display_mode(settings.get("display_mode"))


def normalize_display_mode(value: Any) -> str:
    cleaned = str(value or "").strip().casefold()
    return cleaned if cleaned in DISPLAY_MODES else DEFAULT_DISPLAY_MODE


def display_mode_label(display_mode: str) -> str:
    return DISPLAY_MODE_LABELS[normalize_display_mode(display_mode)]


def default_game_settings_data() -> dict[str, str]:
    return {"display_mode": DEFAULT_DISPLAY_MODE}


def load_game_settings(storage: JsonStore) -> dict[str, str]:
    try:
        data = storage.read_json(GAME_SETTINGS_FILENAME, default=default_game_settings_data())
    except ValueError:
        return default_game_settings_data()
    if not isinstance(data, dict):
        return default_game_settings_data()
    return {"display_mode": normalize_display_mode(data.get("display_mode"))}


def save_game_display_mode(storage: JsonStore, display_mode: str) -> str:
    normalized = normalize_display_mode(display_mode)
    storage.write_json(GAME_SETTINGS_FILENAME, {"display_mode": normalized})
    return normalized


def display_flags_for_mode(pygame, display_mode: str) -> int:
    normalized = normalize_display_mode(display_mode)
    if normalized == DISPLAY_MODE_FULLSCREEN:
        return int(getattr(pygame, "FULLSCREEN", 0))
    if normalized == DISPLAY_MODE_BORDERLESS:
        return int(getattr(pygame, "NOFRAME", 0))
    return 0


def resolution_for_display_mode(
    display_mode: str,
    windowed_resolution: tuple[int, int],
    display_size: tuple[int, int] | None = None,
) -> tuple[int, int]:
    normalized = normalize_display_mode(display_mode)
    if normalized in {DISPLAY_MODE_FULLSCREEN, DISPLAY_MODE_BORDERLESS} and _valid_display_size(display_size):
        return int(display_size[0]), int(display_size[1])
    return windowed_resolution


def calculate_auto_window_size(
    display_width: int,
    display_height: int,
    scale: float = AUTO_WINDOW_SCALE,
    aspect_ratio: float = DEFAULT_ASPECT_RATIO,
) -> tuple[int, int]:
    if display_width < MIN_SCREEN_WIDTH or display_height < MIN_SCREEN_HEIGHT or scale <= 0 or aspect_ratio <= 0:
        return FALLBACK_WINDOW_WIDTH, FALLBACK_WINDOW_HEIGHT

    target_width = min(int(display_width * scale), display_width, MAX_SCREEN_WIDTH)
    target_height = min(int(display_height * scale), display_height, MAX_SCREEN_HEIGHT)
    if target_width <= 0 or target_height <= 0:
        return FALLBACK_WINDOW_WIDTH, FALLBACK_WINDOW_HEIGHT

    if target_width / target_height > aspect_ratio:
        target_width = int(target_height * aspect_ratio)
    else:
        target_height = int(target_width / aspect_ratio)

    if target_width < MIN_SCREEN_WIDTH or target_height < MIN_SCREEN_HEIGHT:
        if MIN_SCREEN_WIDTH <= display_width and MIN_SCREEN_HEIGHT <= display_height:
            return MIN_SCREEN_WIDTH, MIN_SCREEN_HEIGHT
        return FALLBACK_WINDOW_WIDTH, FALLBACK_WINDOW_HEIGHT
    return target_width, target_height


def _read_dimension(value: str | None, minimum: int, maximum: int) -> int | None:
    if value is None or not value.strip():
        return None
    try:
        number = int(value.strip())
    except ValueError:
        return None
    if not minimum <= number <= maximum:
        return None
    return number


def _valid_display_size(display_size: tuple[int, int] | None) -> bool:
    if display_size is None:
        return False
    width, height = display_size
    return MIN_SCREEN_WIDTH <= int(width) <= MAX_SCREEN_WIDTH and MIN_SCREEN_HEIGHT <= int(height) <= MAX_SCREEN_HEIGHT
