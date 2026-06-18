"""Game settings for the experimental PyGame prototype."""

from __future__ import annotations

import os
from typing import Mapping


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
