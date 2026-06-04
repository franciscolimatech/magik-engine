"""Generated retro sprites for the no-external-assets prototype."""

from __future__ import annotations

from dataclasses import dataclass

from src.game import colors
from src.game.settings import TILE_SIZE


@dataclass
class GameAssets:
    floor_tiles: dict[str, object]
    wall_tile: object
    water_tile: object
    shadow: object
    npc: object
    interaction_marker: object
    player: dict[str, list[object]]


def create_assets(pygame) -> GameAssets:
    return GameAssets(
        floor_tiles={
            ".": _floor_tile(pygame, colors.FLOOR),
            "P": _floor_tile(pygame, colors.FLOOR),
            "N": _floor_tile(pygame, colors.FLOOR),
            "g": _grass_tile(pygame),
        },
        wall_tile=_wall_tile(pygame),
        water_tile=_water_tile(pygame),
        shadow=_shadow_sprite(pygame),
        npc=_npc_sprite(pygame),
        interaction_marker=_interaction_marker(pygame),
        player={
            "down": [_player_sprite(pygame, "down", 0), _player_sprite(pygame, "down", 1)],
            "up": [_player_sprite(pygame, "up", 0), _player_sprite(pygame, "up", 1)],
            "left": [_player_sprite(pygame, "left", 0), _player_sprite(pygame, "left", 1)],
            "right": [_player_sprite(pygame, "right", 0), _player_sprite(pygame, "right", 1)],
        },
    )


def draw_tile(pygame, surface, tile: str, x: int, y: int, assets: GameAssets | None = None) -> None:
    if assets is None:
        assets = create_assets(pygame)
    if tile == "#":
        surface.blit(assets.wall_tile, (x, y))
    elif tile == "w":
        surface.blit(assets.water_tile, (x, y))
    else:
        surface.blit(assets.floor_tiles.get(tile, assets.floor_tiles["."]), (x, y))


def _surface(pygame, size: tuple[int, int] = (TILE_SIZE, TILE_SIZE)):
    return pygame.Surface(size, pygame.SRCALPHA)


def _floor_tile(pygame, base_color: tuple[int, int, int]):
    surface = _surface(pygame)
    surface.fill(base_color)
    pygame.draw.rect(surface, colors.FLOOR_ALT, (2, 2, 4, 4))
    pygame.draw.rect(surface, (30, 37, 54), (22, 18, 3, 3))
    return surface


def _grass_tile(pygame):
    surface = _floor_tile(pygame, (31, 58, 50))
    for x, y in ((6, 20), (12, 11), (20, 23), (25, 9)):
        pygame.draw.line(surface, (80, 142, 84), (x, y + 4), (x + 2, y), width=2)
        pygame.draw.line(surface, (54, 107, 68), (x + 3, y + 4), (x + 1, y + 1), width=1)
    return surface


def _wall_tile(pygame):
    surface = _surface(pygame)
    surface.fill(colors.WALL_DARK)
    pygame.draw.rect(surface, colors.WALL, (2, 5, 28, 22), border_radius=3)
    pygame.draw.rect(surface, (60, 112, 84), (5, 8, 9, 5))
    pygame.draw.rect(surface, (34, 69, 58), (17, 17, 10, 6))
    pygame.draw.rect(surface, (19, 39, 36), (2, 25, 28, 3))
    return surface


def _water_tile(pygame):
    surface = _surface(pygame)
    surface.fill((22, 54, 82))
    pygame.draw.rect(surface, (37, 91, 132), (0, 0, TILE_SIZE, TILE_SIZE))
    for y in (8, 18, 27):
        pygame.draw.line(surface, (91, 158, 201), (3, y), (14, y), width=2)
        pygame.draw.line(surface, (91, 158, 201), (20, y + 2), (29, y + 2), width=1)
    return surface


def _shadow_sprite(pygame):
    surface = _surface(pygame)
    pygame.draw.ellipse(surface, (4, 6, 12, 100), (6, 22, 20, 7))
    return surface


def _npc_sprite(pygame):
    surface = _surface(pygame)
    pygame.draw.rect(surface, colors.NPC_SHADOW, (9, 22, 14, 5))
    pygame.draw.rect(surface, (42, 94, 154), (10, 10, 12, 14))
    pygame.draw.rect(surface, colors.NPC, (9, 8, 14, 9))
    pygame.draw.rect(surface, colors.WHITE, (12, 11, 2, 2))
    pygame.draw.rect(surface, colors.WHITE, (18, 11, 2, 2))
    pygame.draw.rect(surface, (16, 28, 48), (11, 24, 4, 5))
    pygame.draw.rect(surface, (16, 28, 48), (18, 24, 4, 5))
    return surface


def _interaction_marker(pygame):
    surface = pygame.Surface((12, 16), pygame.SRCALPHA)
    pygame.draw.rect(surface, (255, 232, 140), (5, 1, 2, 8))
    pygame.draw.rect(surface, (255, 232, 140), (5, 12, 2, 2))
    return surface


def _player_sprite(pygame, direction: str, frame: int):
    surface = _surface(pygame)
    step = 1 if frame % 2 else 0
    pygame.draw.ellipse(surface, (4, 6, 12, 100), (6, 23, 20, 6))
    pygame.draw.rect(surface, colors.PLAYER, (10, 9, 12, 13))
    pygame.draw.rect(surface, (178, 169, 255), (9, 7, 14, 7))
    if direction == "up":
        pygame.draw.rect(surface, (63, 56, 129), (10, 8, 12, 4))
    elif direction == "left":
        pygame.draw.rect(surface, colors.WHITE, (11, 11, 2, 2))
    elif direction == "right":
        pygame.draw.rect(surface, colors.WHITE, (19, 11, 2, 2))
    else:
        pygame.draw.rect(surface, colors.WHITE, (12, 11, 2, 2))
        pygame.draw.rect(surface, colors.WHITE, (18, 11, 2, 2))
    pygame.draw.rect(surface, colors.PLAYER_SHADOW, (10, 22, 4, 6 + step))
    pygame.draw.rect(surface, colors.PLAYER_SHADOW, (18, 22, 4, 6 - step))
    return surface
