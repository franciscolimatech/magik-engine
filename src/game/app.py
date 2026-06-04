"""PyGame entry point for the experimental MAGIK Engine 2D prototype."""

from __future__ import annotations

import os

from src.core.character import MIKO_ID
from src.game.game_context import DATA_PATH, GameContext, load_player_name as load_context_player_name
from src.game.settings import FPS, SCREEN_HEIGHT, SCREEN_WIDTH, WINDOW_TITLE
from src.storage.json_storage import JSONStorage
from src.storage.types import JsonStore


def load_player_name(storage: JsonStore | None = None) -> str:
    return load_context_player_name(MIKO_ID, storage)


def run_game(max_frames: int | None = None) -> None:
    import pygame

    from src.game.scenes.overworld import OverworldScene

    storage = JSONStorage(DATA_PATH)
    context = GameContext.from_env(storage=storage)
    pygame.init()
    pygame.key.set_repeat(0)
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption(WINDOW_TITLE)
    clock = pygame.time.Clock()
    scene = OverworldScene(pygame, context, storage=storage)
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
