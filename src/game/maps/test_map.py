"""Small test map for the first 2D MAGIK Engine prototype."""

from __future__ import annotations

from dataclasses import dataclass


TEST_MAP = [
    "################################",
    "#.....ggg.........N............#",
    "#..######....gggg..............#",
    "#...........###.........www....#",
    "#....P....gg.?....##....www....#",
    "#..........N............www....#",
    "#..####..................####..#",
    "#..............gggg............#",
    "#......#####...................#",
    "#.....................?g.......#",
    "#....N.................N.......#",
    "#..................######......#",
    "#..........www.................#",
    "#...........####...............#",
    "#..........www.................#",
    "#....#####.............ggg.....#",
    "#..........................N...#",
    "#.................####.........#",
    "#......gggg....................#",
    "#.........N....................#",
    "#..............................#",
    "################################",
]

OBSTACLE_TILES = {"#", "w"}
FLOOR_TILES = {".", "g", "?", "P", "N"}


@dataclass(frozen=True)
class MapNpc:
    x: int
    y: int
    name: str
    dialogues: tuple[str, ...]


NPC_DIALOGUES = [
    (
        "Guarda da Estrada",
        (
            "A estrada esta estranha hoje. Fique perto da luz.",
            "Se ouvir corrente no mato, finja que nao ouviu.",
        ),
    ),
    (
        "Mercador Azul",
        (
            "Pedralume compra silencio, mas nao compra sorte.",
            "Tenho mapas que mentem menos que gente.",
        ),
    ),
    (
        "Velha do Brejo",
        (
            "Voce nao devia andar por aqui tao tarde.",
            "A Floresta do Avesso escuta quem fala sozinho.",
            "E essa corrente no seu braco... ela tambem escuta?",
        ),
    ),
]


def load_test_map() -> list[str]:
    return list(TEST_MAP)


def map_width(map_data: list[str]) -> int:
    return len(map_data[0]) if map_data else 0


def map_height(map_data: list[str]) -> int:
    return len(map_data)


def find_player_start(map_data: list[str]) -> tuple[int, int]:
    for y, row in enumerate(map_data):
        x = row.find("P")
        if x != -1:
            return x, y
    raise ValueError("Mapa sem posicao inicial do player.")


def find_npcs(map_data: list[str]) -> list[MapNpc]:
    npcs: list[MapNpc] = []
    npc_index = 0
    for y, row in enumerate(map_data):
        for x, tile in enumerate(row):
            if tile == "N":
                name, dialogues = NPC_DIALOGUES[npc_index % len(NPC_DIALOGUES)]
                npcs.append(MapNpc(x=x, y=y, name=name, dialogues=dialogues))
                npc_index += 1
    return npcs


def in_bounds(map_data: list[str], x: int, y: int) -> bool:
    return 0 <= y < map_height(map_data) and 0 <= x < map_width(map_data)


def tile_at(map_data: list[str], x: int, y: int) -> str:
    if not in_bounds(map_data, x, y):
        return "#"
    return map_data[y][x]


def is_obstacle(map_data: list[str], x: int, y: int) -> bool:
    return tile_at(map_data, x, y) in OBSTACLE_TILES


def is_walkable(map_data: list[str], x: int, y: int) -> bool:
    return in_bounds(map_data, x, y) and not is_obstacle(map_data, x, y)
