"""Game settings for the experimental PyGame prototype."""

from __future__ import annotations

import os
from typing import Mapping


WINDOW_TITLE = "MAGIK Engine"
SCREEN_WIDTH = 640
SCREEN_HEIGHT = 480
MIN_SCREEN_WIDTH = 800
MIN_SCREEN_HEIGHT = 450
MAX_SCREEN_WIDTH = 3840
MAX_SCREEN_HEIGHT = 2160
TILE_SIZE = 32
FPS = 60

PLAYER_NAME_FALLBACK = "Aventureiro"


def get_game_resolution(env: Mapping[str, str] | None = None) -> tuple[int, int]:
    values = env if env is not None else os.environ
    width = _read_dimension(values.get("MAGIK_GAME_WIDTH"), MIN_SCREEN_WIDTH, MAX_SCREEN_WIDTH)
    height = _read_dimension(values.get("MAGIK_GAME_HEIGHT"), MIN_SCREEN_HEIGHT, MAX_SCREEN_HEIGHT)
    if width is None or height is None:
        return SCREEN_WIDTH, SCREEN_HEIGHT
    return width, height


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
