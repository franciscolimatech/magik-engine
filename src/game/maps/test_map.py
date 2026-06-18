"""Small test map for the first 2D MAGIK Engine prototype."""

from __future__ import annotations

from dataclasses import dataclass

from src.game.dialogue import DialogueChoice, DialogueOption


TEST_MAP = [
    "################################",
    "#.....ggg.........N............#",
    "#..######....gggg..............#",
    "#...........###..C......www....#",
    "#....P...?gg.?....##....www....#",
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

OBSTACLE_TILES = {"#", "w", "C"}
FLOOR_TILES = {".", "g", "?", "P", "N", "C"}


@dataclass(frozen=True)
class MapNpc:
    x: int
    y: int
    name: str
    dialogues: tuple[str, ...]
    choice: DialogueChoice | None = None
    npc_id: str | None = None
    location_id: str | None = None


@dataclass(frozen=True)
class MapCreature:
    x: int
    y: int


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
        "Velho Nox",
        (
            "Velho Nox observa as arvores como se elas estivessem respirando.",
            "'Nem toda sombra pertence a quem a carrega.'",
        ),
        DialogueChoice(
            question="Vai mesmo seguir para a floresta?",
            options=(
                DialogueOption(
                    text="Sim, eu preciso ir.",
                    response="Entao leve cuidado. E nao prometa o que nao pode cumprir.",
                    tags=("coragem",),
                ),
                DialogueOption(
                    text="Nao hoje.",
                    response="Sabio. Ou covarde. As vezes e a mesma coisa.",
                    tags=("cautela",),
                ),
                DialogueOption(
                    text="Que floresta?",
                    response="Aquela que aparece quando decide que voce ja esta perdido.",
                    tags=("misterio",),
                ),
            ),
        ),
        "velho-nox",
        "floresta-do-avesso",
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
                npc_data = NPC_DIALOGUES[npc_index % len(NPC_DIALOGUES)]
                name, dialogues = npc_data[0], npc_data[1]
                choice = npc_data[2] if len(npc_data) > 2 else None
                npc_id = npc_data[3] if len(npc_data) > 3 else None
                location_id = npc_data[4] if len(npc_data) > 4 else None
                npcs.append(
                    MapNpc(
                        x=x,
                        y=y,
                        name=name,
                        dialogues=dialogues,
                        choice=choice,
                        npc_id=npc_id,
                        location_id=location_id,
                    )
                )
                npc_index += 1
    return npcs


def find_creatures(map_data: list[str]) -> list[MapCreature]:
    creatures: list[MapCreature] = []
    for y, row in enumerate(map_data):
        for x, tile in enumerate(row):
            if tile == "C":
                creatures.append(MapCreature(x=x, y=y))
    return creatures


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
