"""PyGame entry point for the experimental MAGIK Engine 2D prototype."""

from __future__ import annotations

import os
from pathlib import Path

from src.core.character import MIKO_ID, get_character
from src.game.settings import FPS, PLAYER_NAME_FALLBACK, SCREEN_HEIGHT, SCREEN_WIDTH, WINDOW_TITLE
from src.storage.json_storage import JSONStorage
from src.storage.types import JsonStore


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = PROJECT_ROOT / "data"


def load_player_name(storage: JsonStore | None = None) -> str:
    resolved_storage = storage or JSONStorage(DATA_PATH)
    try:
        return get_character(resolved_storage, MIKO_ID).name
    except ValueError:
        return PLAYER_NAME_FALLBACK


def run_game(max_frames: int | None = None) -> None:
    import pygame

    from src.game.scenes.overworld import OverworldScene

    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption(WINDOW_TITLE)
    clock = pygame.time.Clock()
    scene = OverworldScene(pygame, load_player_name())
    running = True
    frame_count = 0

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False
            else:
                scene.handle_event(event)
        scene.update()
        scene.draw(screen)
        pygame.display.flip()
        clock.tick(FPS)
        frame_count += 1
        if max_frames is not None and frame_count >= max_frames:
            running = False

    pygame.quit()


def _max_frames_from_env() -> int | None:
    value = os.environ.get("MAGIK_GAME_MAX_FRAMES", "").strip()
    if not value:
        return None
    try:
        return max(1, int(value))
    except ValueError:
        return None


def main() -> None:
    run_game(max_frames=_max_frames_from_env())


if __name__ == "__main__":
    main()
