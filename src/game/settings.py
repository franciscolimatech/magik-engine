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
COMMON_WINDOW_RESOLUTIONS = (
    (800, 450),
    (960, 540),
    (1024, 576),
    (1152, 648),
    (1280, 720),
    (1366, 768),
    (1600, 900),
    (1920, 1080),
    (2560, 1440),
    (3840, 2160),
)


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


def get_window_resolution(
    env: Mapping[str, str] | None = None,
    storage: JsonStore | None = None,
    display_size: tuple[int, int] | None = None,
) -> tuple[int, int]:
    values = env if env is not None else os.environ
    env_resolution = _read_env_resolution(values)
    if env_resolution is not None:
        return env_resolution
    if storage is not None:
        settings = load_game_settings(storage)
        saved_resolution = normalize_resolution(
            (settings.get("window_width"), settings.get("window_height")),
            display_size=display_size,
            fallback=None,
        )
        if saved_resolution is not None:
            return saved_resolution
    return get_game_resolution(values, display_size)


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


def default_game_settings_data() -> dict[str, Any]:
    return {
        "display_mode": DEFAULT_DISPLAY_MODE,
        "window_width": FALLBACK_WINDOW_WIDTH,
        "window_height": FALLBACK_WINDOW_HEIGHT,
    }


def load_game_settings(storage: JsonStore) -> dict[str, Any]:
    try:
        data = storage.read_json(GAME_SETTINGS_FILENAME, default=default_game_settings_data())
    except ValueError:
        return default_game_settings_data()
    if not isinstance(data, dict):
        return default_game_settings_data()
    resolution = normalize_resolution(
        (data.get("window_width"), data.get("window_height")),
        fallback=(FALLBACK_WINDOW_WIDTH, FALLBACK_WINDOW_HEIGHT),
    )
    return {
        "display_mode": normalize_display_mode(data.get("display_mode")),
        "window_width": resolution[0],
        "window_height": resolution[1],
    }


def save_game_display_mode(storage: JsonStore, display_mode: str) -> str:
    settings = load_game_settings(storage)
    normalized = normalize_display_mode(display_mode)
    storage.write_json(
        GAME_SETTINGS_FILENAME,
        {
            "display_mode": normalized,
            "window_width": settings["window_width"],
            "window_height": settings["window_height"],
        },
    )
    return normalized


def save_game_display_preferences(
    storage: JsonStore,
    display_mode: str,
    window_resolution: tuple[int, int],
) -> dict[str, Any]:
    normalized_mode = normalize_display_mode(display_mode)
    normalized_resolution = normalize_resolution(
        window_resolution,
        fallback=(FALLBACK_WINDOW_WIDTH, FALLBACK_WINDOW_HEIGHT),
    )
    data = {
        "display_mode": normalized_mode,
        "window_width": normalized_resolution[0],
        "window_height": normalized_resolution[1],
    }
    storage.write_json(GAME_SETTINGS_FILENAME, data)
    return data


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
    if normalized == DISPLAY_MODE_BORDERLESS and _valid_display_size(display_size):
        return int(display_size[0]), int(display_size[1])
    if normalized == DISPLAY_MODE_FULLSCREEN and _valid_display_size(display_size):
        return _fit_resolution_to_display(windowed_resolution, display_size)
    return windowed_resolution


def normalize_resolution(
    value: Any,
    display_size: tuple[int, int] | None = None,
    fallback: tuple[int, int] | None = (FALLBACK_WINDOW_WIDTH, FALLBACK_WINDOW_HEIGHT),
) -> tuple[int, int] | None:
    try:
        width, height = value
        width = int(width)
        height = int(height)
    except (TypeError, ValueError):
        return fallback
    if not (MIN_SCREEN_WIDTH <= width <= MAX_SCREEN_WIDTH and MIN_SCREEN_HEIGHT <= height <= MAX_SCREEN_HEIGHT):
        return fallback
    if _valid_display_size(display_size) and (width > display_size[0] or height > display_size[1]):
        return fallback
    return width, height


def available_window_resolutions(
    display_size: tuple[int, int] | None,
    listed_modes: Any = None,
) -> list[tuple[int, int]]:
    candidates = _normalize_listed_modes(listed_modes)
    if not candidates:
        candidates = list(COMMON_WINDOW_RESOLUTIONS)
    candidates.extend(COMMON_WINDOW_RESOLUTIONS)
    filtered = filter_resolutions_by_display(candidates, display_size)
    if filtered:
        return filtered
    return [(MIN_SCREEN_WIDTH, MIN_SCREEN_HEIGHT)]


def filter_resolutions_by_display(
    resolutions: list[tuple[int, int]] | tuple[tuple[int, int], ...],
    display_size: tuple[int, int] | None,
) -> list[tuple[int, int]]:
    max_width, max_height = display_size if _valid_display_size(display_size) else (MAX_SCREEN_WIDTH, MAX_SCREEN_HEIGHT)
    result: list[tuple[int, int]] = []
    for resolution in resolutions:
        normalized = normalize_resolution(resolution, fallback=None)
        if normalized is None:
            continue
        width, height = normalized
        if width > max_width or height > max_height:
            continue
        if normalized not in result:
            result.append(normalized)
    result.sort(key=lambda item: (item[0] * item[1], item[0], item[1]))
    return result


def choose_window_resolution(
    preferred: tuple[int, int] | None,
    available_resolutions: list[tuple[int, int]],
    display_size: tuple[int, int] | None = None,
) -> tuple[int, int]:
    normalized = normalize_resolution(preferred, display_size=display_size, fallback=None)
    if normalized in available_resolutions:
        return normalized
    if normalized is not None:
        candidates = [resolution for resolution in available_resolutions if resolution[0] <= normalized[0] and resolution[1] <= normalized[1]]
        if candidates:
            return candidates[-1]
    if available_resolutions:
        default = normalize_resolution((FALLBACK_WINDOW_WIDTH, FALLBACK_WINDOW_HEIGHT), display_size=display_size, fallback=None)
        if default in available_resolutions:
            return default
        return available_resolutions[-1]
    return MIN_SCREEN_WIDTH, MIN_SCREEN_HEIGHT


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


def _read_env_resolution(values: Mapping[str, str]) -> tuple[int, int] | None:
    width = _read_dimension(values.get("MAGIK_GAME_WIDTH"), MIN_SCREEN_WIDTH, MAX_SCREEN_WIDTH)
    height = _read_dimension(values.get("MAGIK_GAME_HEIGHT"), MIN_SCREEN_HEIGHT, MAX_SCREEN_HEIGHT)
    if width is not None and height is not None:
        return width, height
    return None


def _valid_display_size(display_size: tuple[int, int] | None) -> bool:
    if display_size is None:
        return False
    width, height = display_size
    return MIN_SCREEN_WIDTH <= int(width) <= MAX_SCREEN_WIDTH and MIN_SCREEN_HEIGHT <= int(height) <= MAX_SCREEN_HEIGHT


def _normalize_listed_modes(listed_modes: Any) -> list[tuple[int, int]]:
    if listed_modes in (None, -1):
        return []
    if not isinstance(listed_modes, (list, tuple)):
        return []
    result = []
    for mode in listed_modes:
        normalized = normalize_resolution(mode, fallback=None)
        if normalized is not None:
            result.append(normalized)
    return result


def _fit_resolution_to_display(
    resolution: tuple[int, int],
    display_size: tuple[int, int],
) -> tuple[int, int]:
    normalized = normalize_resolution(resolution, display_size=display_size, fallback=None)
    if normalized is not None:
        return normalized
    return int(display_size[0]), int(display_size[1])
