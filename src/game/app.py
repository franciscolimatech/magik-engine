"""PyGame entry point for the experimental MAGIK Engine 2D prototype."""

from __future__ import annotations

import os

from src.core.character import Character, MIKO_ID, get_character
from src.game.entities.creature import Creature
from src.game.game_context import DATA_PATH, GameContext, load_player_name as load_context_player_name
from src.game.settings import FPS, WINDOW_TITLE, get_game_resolution
from src.storage.json_storage import JSONStorage
from src.storage.types import JsonStore


def load_player_name(storage: JsonStore | None = None) -> str:
    return load_context_player_name(MIKO_ID, storage)


def run_game(max_frames: int | None = None) -> None:
    import pygame

    from src.game.scenes.battle import BattleScene
    from src.game.scenes.character_creator import CharacterCreatorScene
    from src.game.scenes.main_menu import MainMenuScene
    from src.game.scenes.overworld import OverworldScene

    storage = JSONStorage(DATA_PATH)
    context = GameContext.from_env(storage=storage)
    pygame.init()
    pygame.key.set_repeat(0)
    screen = pygame.display.set_mode(get_game_resolution(display_size=_detect_display_size(pygame)))
    pygame.display.set_caption(WINDOW_TITLE)
    clock = pygame.time.Clock()
    scene = MainMenuScene(pygame, context, storage=storage)
    running = True
    frame_count = 0

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            else:
                scene.handle_event(event)
        if getattr(scene, "should_quit", False):
            _persist_scene_state(scene)
            running = False
        requested_scene = _consume_requested_scene(scene)
        if requested_scene == "overworld":
            _persist_scene_state(scene)
            context = getattr(scene, "context", context)
            scene = getattr(scene, "return_scene", None) or OverworldScene(pygame, context, storage=storage)
        elif requested_scene == "character_creator":
            _persist_scene_state(scene)
            context = getattr(scene, "context", context)
            scene = CharacterCreatorScene(pygame, context, storage)
        elif requested_scene == "main_menu":
            _persist_scene_state(scene)
            context = getattr(scene, "context", context)
            scene = MainMenuScene(pygame, context, storage=storage)
        elif requested_scene == "battle":
            _persist_scene_state(scene)
            context = getattr(scene, "context", context)
            creature = _consume_requested_creature(scene)
            if creature is not None:
                scene = BattleScene(
                    pygame,
                    context,
                    _load_battle_character(storage, context),
                    creature,
                    return_scene=scene,
                    storage=storage,
                )
        scene.update()
        scene.draw(screen)
        pygame.display.flip()
        clock.tick(FPS)
        frame_count += 1
        if max_frames is not None and frame_count >= max_frames:
            running = False

    _persist_scene_state(scene)
    pygame.quit()


def _consume_requested_scene(scene) -> str | None:
    consume = getattr(scene, "consume_requested_scene", None)
    if consume is None:
        return None
    return consume()


def _consume_requested_creature(scene) -> Creature | None:
    consume = getattr(scene, "consume_requested_creature", None)
    if consume is None:
        return None
    return consume()


def _load_battle_character(storage: JsonStore, context: GameContext) -> Character:
    try:
        return get_character(storage, context.character_id)
    except ValueError:
        return Character(
            id=context.character_id,
            name=context.player_name,
            character_class="Aventureiro",
            max_health=20,
            current_health=20,
            armor=0,
        )


def _persist_scene_state(scene) -> None:
    persist = getattr(scene, "persist_state", None)
    if persist is not None:
        persist()


def _detect_display_size(pygame) -> tuple[int, int] | None:
    try:
        info = pygame.display.Info()
        width = int(getattr(info, "current_w", 0))
        height = int(getattr(info, "current_h", 0))
    except Exception:
        return None
    if width <= 0 or height <= 0:
        return None
    return width, height


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
