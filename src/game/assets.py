"""Generated retro sprites for the no-external-assets prototype."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.game import colors
from src.game.appearance import EYE_COLORS, HAIR_COLORS, OUTFIT_COLORS, normalize_appearance
from src.game.settings import TILE_SIZE


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TITLE_BACKGROUND_PATH = PROJECT_ROOT / "assets" / "images" / "title_background.png"
_SCALED_SURFACE_CACHE: dict[tuple[int, tuple[int, int]], object] = {}


@dataclass
class GameAssets:
    floor_tiles: dict[str, object]
    wall_tile: object
    water_tile: object
    shadow: object
    npc: object
    creature: object
    interaction_marker: object
    player: dict[str, list[object]]


def create_assets(pygame, player_appearance: dict | None = None) -> GameAssets:
    player_sprites = create_player_sprites_from_appearance(pygame, player_appearance)
    return GameAssets(
        floor_tiles={
            ".": _floor_tile(pygame, colors.FLOOR),
            "P": _floor_tile(pygame, colors.FLOOR),
            "N": _floor_tile(pygame, colors.FLOOR),
            "C": _floor_tile(pygame, colors.FLOOR),
            "?": _event_tile(pygame),
            "g": _grass_tile(pygame),
        },
        wall_tile=_wall_tile(pygame),
        water_tile=_water_tile(pygame),
        shadow=_shadow_sprite(pygame),
        npc=_npc_sprite(pygame),
        creature=_creature_sprite(pygame),
        interaction_marker=_interaction_marker(pygame),
        player=player_sprites,
    )


def create_player_sprites_from_appearance(pygame, appearance: dict | None = None) -> dict[str, list[object]]:
    resolved = normalize_appearance(appearance)
    return {
        "down": [_player_sprite(pygame, "down", 0, resolved), _player_sprite(pygame, "down", 1, resolved)],
        "up": [_player_sprite(pygame, "up", 0, resolved), _player_sprite(pygame, "up", 1, resolved)],
        "left": [_player_sprite(pygame, "left", 0, resolved), _player_sprite(pygame, "left", 1, resolved)],
        "right": [_player_sprite(pygame, "right", 0, resolved), _player_sprite(pygame, "right", 1, resolved)],
    }


def draw_tile(pygame, surface, tile: str, x: int, y: int, assets: GameAssets | None = None, size: int = TILE_SIZE) -> None:
    if assets is None:
        assets = create_assets(pygame)
    if tile == "#":
        blit_scaled(pygame, surface, assets.wall_tile, (x, y), size)
    elif tile == "w":
        blit_scaled(pygame, surface, assets.water_tile, (x, y), size)
    else:
        blit_scaled(pygame, surface, assets.floor_tiles.get(tile, assets.floor_tiles["."]), (x, y), size)


def blit_scaled(pygame, surface, sprite, position: tuple[int, int], size: int | tuple[int, int]) -> None:
    target_size = (size, size) if isinstance(size, int) else size
    if sprite.get_size() == target_size:
        surface.blit(sprite, position)
        return
    cache_key = (id(sprite), target_size)
    scaled = _SCALED_SURFACE_CACHE.get(cache_key)
    if scaled is None:
        scaled = pygame.transform.scale(sprite, target_size)
        _SCALED_SURFACE_CACHE[cache_key] = scaled
    surface.blit(scaled, position)


def load_optional_image(pygame, path: str | Path):
    candidate = Path(path)
    if not candidate.is_file():
        return None
    try:
        image = pygame.image.load(str(candidate))
        return image.convert_alpha() if hasattr(image, "convert_alpha") else image
    except Exception:
        return None


def scale_surface_cover(pygame, surface, target_width: int, target_height: int):
    if target_width <= 0 or target_height <= 0:
        raise ValueError("Dimensoes de destino devem ser positivas.")
    source_width, source_height = surface.get_size()
    if source_width <= 0 or source_height <= 0:
        raise ValueError("Imagem de origem deve ter dimensoes positivas.")
    scale = max(target_width / source_width, target_height / source_height)
    scaled_size = (
        max(1, int(round(source_width * scale))),
        max(1, int(round(source_height * scale))),
    )
    scaled = pygame.transform.smoothscale(surface, scaled_size)
    offset = (
        (target_width - scaled_size[0]) // 2,
        (target_height - scaled_size[1]) // 2,
    )
    return scaled, offset


def draw_cover_background(pygame, surface, image) -> None:
    scaled, offset = scale_surface_cover(pygame, image, surface.get_width(), surface.get_height())
    surface.blit(scaled, offset)


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


def _event_tile(pygame):
    surface = _floor_tile(pygame, colors.FLOOR)
    pygame.draw.rect(surface, (139, 124, 246), (14, 9, 4, 4))
    pygame.draw.rect(surface, (81, 167, 255), (15, 15, 2, 2))
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


def _creature_sprite(pygame):
    surface = _surface(pygame)
    pygame.draw.ellipse(surface, (4, 6, 12, 140), (5, 23, 22, 7))
    pygame.draw.rect(surface, (38, 26, 58), (8, 13, 16, 12))
    pygame.draw.rect(surface, (69, 44, 108), (10, 9, 12, 9))
    pygame.draw.rect(surface, (120, 82, 180), (7, 16, 5, 6))
    pygame.draw.rect(surface, (120, 82, 180), (20, 16, 5, 6))
    pygame.draw.rect(surface, (222, 233, 255), (12, 13, 2, 2))
    pygame.draw.rect(surface, (222, 233, 255), (18, 13, 2, 2))
    pygame.draw.rect(surface, (18, 14, 29), (12, 25, 3, 4))
    pygame.draw.rect(surface, (18, 14, 29), (18, 25, 3, 4))
    return surface


def _interaction_marker(pygame):
    surface = pygame.Surface((12, 16), pygame.SRCALPHA)
    pygame.draw.rect(surface, (255, 232, 140), (5, 1, 2, 8))
    pygame.draw.rect(surface, (255, 232, 140), (5, 12, 2, 2))
    return surface


def _player_sprite(pygame, direction: str, frame: int, appearance: dict | None = None):
    resolved = normalize_appearance(appearance)
    outfit_color = OUTFIT_COLORS[resolved["outfit_color"]]
    hair_color = HAIR_COLORS[resolved["hair_color"]]
    eye_color = EYE_COLORS[resolved["eye_color"]]
    surface = _surface(pygame)
    step = 1 if frame % 2 else 0
    pygame.draw.ellipse(surface, (4, 6, 12, 100), (6, 23, 20, 6))
    _draw_outfit(pygame, surface, resolved["outfit_style"], outfit_color)
    _draw_hair(pygame, surface, resolved["hair_style"], hair_color)
    if direction == "up":
        pygame.draw.rect(surface, _darken(hair_color), (10, 8, 12, 4))
    elif direction == "left":
        pygame.draw.rect(surface, eye_color, (11, 11, 2, 2))
    elif direction == "right":
        pygame.draw.rect(surface, eye_color, (19, 11, 2, 2))
    else:
        pygame.draw.rect(surface, eye_color, (12, 11, 2, 2))
        pygame.draw.rect(surface, eye_color, (18, 11, 2, 2))
    pygame.draw.rect(surface, colors.PLAYER_SHADOW, (10, 22, 4, 6 + step))
    pygame.draw.rect(surface, colors.PLAYER_SHADOW, (18, 22, 4, 6 - step))
    return surface


def _draw_outfit(pygame, surface, style: str, outfit_color: tuple[int, int, int]) -> None:
    pygame.draw.rect(surface, outfit_color, (10, 9, 12, 13))
    if style == "manto":
        pygame.draw.rect(surface, _darken(outfit_color), (8, 13, 16, 10))
    elif style == "guerreiro leve":
        pygame.draw.rect(surface, (190, 196, 208), (11, 10, 10, 4))
    elif style == "aprendiz":
        pygame.draw.rect(surface, (238, 218, 128), (15, 9, 2, 13))
    elif style == "roupa simples":
        pygame.draw.rect(surface, _darken(outfit_color), (10, 18, 12, 4))
    else:
        pygame.draw.rect(surface, _darken(outfit_color), (9, 14, 3, 7))


def _draw_hair(pygame, surface, style: str, hair_color: tuple[int, int, int]) -> None:
    if style == "careca/coberto":
        pygame.draw.rect(surface, hair_color, (9, 6, 14, 4))
    elif style == "longo":
        pygame.draw.rect(surface, hair_color, (8, 7, 16, 10))
        pygame.draw.rect(surface, hair_color, (7, 14, 4, 8))
        pygame.draw.rect(surface, hair_color, (21, 14, 4, 8))
    elif style == "medio":
        pygame.draw.rect(surface, hair_color, (9, 7, 14, 8))
        pygame.draw.rect(surface, hair_color, (8, 12, 3, 5))
        pygame.draw.rect(surface, hair_color, (21, 12, 3, 5))
    elif style == "preso":
        pygame.draw.rect(surface, hair_color, (9, 7, 14, 6))
        pygame.draw.rect(surface, hair_color, (22, 9, 4, 4))
    else:
        pygame.draw.rect(surface, hair_color, (9, 7, 14, 7))


def _darken(color: tuple[int, int, int]) -> tuple[int, int, int]:
    return tuple(max(0, int(value * 0.55)) for value in color)
