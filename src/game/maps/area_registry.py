"""Small registry for playable 2D areas.

Areas are visual/gameplay slices of an official lore location. They do not
create quests, rewards, encounters, or combat rules by themselves.
"""

from __future__ import annotations

from dataclasses import dataclass

from src.game.dialogue import DialogueChoice
from src.game.maps.events import MapEvent, load_test_events
from src.game.maps.test_map import TEST_MAP, is_walkable


DEFAULT_AREA_ID = "floresta-do-avesso-entrada"
DEFAULT_SPAWN_ID = "entrada"


@dataclass(frozen=True)
class AreaSpawn:
    id: str
    x: int
    y: int

    @property
    def position(self) -> tuple[int, int]:
        return self.x, self.y


@dataclass(frozen=True)
class AreaTransition:
    id: str
    x: int
    y: int
    target_area_id: str
    target_spawn_id: str = DEFAULT_SPAWN_ID
    target_location_id: str | None = None
    label: str = "Atravessar"

    @property
    def position(self) -> tuple[int, int]:
        return self.x, self.y


@dataclass(frozen=True)
class AreaNpc:
    x: int
    y: int
    name: str
    dialogues: tuple[str, ...]
    choice: DialogueChoice | None = None
    npc_id: str | None = None
    location_id: str | None = None

    @property
    def position(self) -> tuple[int, int]:
        return self.x, self.y


@dataclass(frozen=True)
class GameArea:
    id: str
    name: str
    location_id: str
    map_data: tuple[str, ...]
    spawns: tuple[AreaSpawn, ...]
    transitions: tuple[AreaTransition, ...] = ()
    events: tuple[MapEvent, ...] = ()
    npcs: tuple[AreaNpc, ...] = ()


FOREST_CLEARING_MAP = (
    "########################",
    "#..P....ggg............#",
    "#........ggg...........#",
    "#....####..............#",
    "#......................#",
    "#.......?..............#",
    "#...................ggg#",
    "#..ggg.................#",
    "#...............####...#",
    "#......................#",
    "#...####..........####.#",
    "#......................#",
    "#......................#",
    "########################",
)


NOX_CABIN_MAP = (
    "##################",
    "#......####......#",
    "#....##....##....#",
    "#...#........#...#",
    "#...#........#...#",
    "#......?.........#",
    "#....####........#",
    "#................#",
    "#..P.............#",
    "#................#",
    "#................#",
    "##################",
)


AREAS = (
    GameArea(
        id=DEFAULT_AREA_ID,
        name="Entrada da Floresta do Avesso",
        location_id="floresta-do-avesso",
        map_data=tuple(TEST_MAP),
        spawns=(
            AreaSpawn("entrada", 5, 4),
            AreaSpawn("volta-da-clareira", 29, 20),
        ),
        transitions=(
            AreaTransition(
                id="entrada-para-clareira",
                x=30,
                y=20,
                target_area_id="floresta-do-avesso-clareira",
                target_spawn_id="entrada-da-clareira",
                label="Ir para Clareira",
            ),
        ),
        events=tuple(load_test_events()),
    ),
    GameArea(
        id="floresta-do-avesso-clareira",
        name="Clareira da Floresta do Avesso",
        location_id="floresta-do-avesso",
        map_data=FOREST_CLEARING_MAP,
        spawns=(
            AreaSpawn("entrada-da-clareira", 2, 2),
            AreaSpawn("volta-da-cabana", 21, 12),
        ),
        transitions=(
            AreaTransition(
                id="clareira-para-entrada",
                x=1,
                y=2,
                target_area_id=DEFAULT_AREA_ID,
                target_spawn_id="volta-da-clareira",
                label="Voltar para Entrada",
            ),
            AreaTransition(
                id="clareira-para-cabana-nox",
                x=22,
                y=12,
                target_area_id="floresta-do-avesso-cabana-nox",
                target_spawn_id="entrada-cabana",
                label="Ir para Cabana do Nox",
            ),
        ),
    ),
    GameArea(
        id="floresta-do-avesso-cabana-nox",
        name="Cabana do Nox",
        location_id="floresta-do-avesso",
        map_data=NOX_CABIN_MAP,
        spawns=(
            AreaSpawn("entrada-cabana", 2, 8),
            AreaSpawn("retorno-clareira", 1, 9),
        ),
        transitions=(
            AreaTransition(
                id="cabana-nox-para-clareira",
                x=1,
                y=9,
                target_area_id="floresta-do-avesso-clareira",
                target_spawn_id="volta-da-cabana",
                label="Voltar para Clareira",
            ),
        ),
        npcs=(
            AreaNpc(
                x=8,
                y=5,
                name="Velho Nox",
                dialogues=(
                    "A floresta nao gosta de passos apressados.",
                    "Ela devolve caminhos... mas raramente devolve pessoas inteiras.",
                ),
                npc_id="velho-nox",
                location_id="floresta-do-avesso",
            ),
        ),
    ),
)


def list_areas() -> list[GameArea]:
    return list(AREAS)


def get_area(area_id: str) -> GameArea:
    normalized = area_id.strip().casefold()
    for area in AREAS:
        if area.id.casefold() == normalized:
            return area
    raise ValueError(f"Area do jogo nao encontrada: {area_id}.")


def get_default_area() -> GameArea:
    return get_area(DEFAULT_AREA_ID)


def get_spawn(area: GameArea, spawn_id: str = DEFAULT_SPAWN_ID) -> AreaSpawn:
    normalized = spawn_id.strip().casefold()
    for spawn in area.spawns:
        if spawn.id.casefold() == normalized:
            return spawn
    raise ValueError(f"Spawn nao encontrado na area {area.id}: {spawn_id}.")


def resolve_area(area_id: str | None) -> GameArea:
    try:
        return get_area(area_id or DEFAULT_AREA_ID)
    except ValueError:
        return get_default_area()


def find_transition_at(area: GameArea, x: int, y: int) -> AreaTransition | None:
    return next((transition for transition in area.transitions if transition.position == (x, y)), None)


def validate_area_registry() -> None:
    area_ids: set[str] = set()
    for area in AREAS:
        if not area.id.strip():
            raise ValueError("Area precisa de id.")
        if area.id in area_ids:
            raise ValueError(f"Area duplicada: {area.id}.")
        area_ids.add(area.id)
        spawn_ids = {spawn.id for spawn in area.spawns}
        if not spawn_ids:
            raise ValueError(f"Area sem spawn: {area.id}.")
        for transition in area.transitions:
            if not is_walkable(list(area.map_data), transition.x, transition.y):
                raise ValueError(f"Transicao em tile bloqueado: {transition.id}.")
            target = get_area(transition.target_area_id)
            get_spawn(target, transition.target_spawn_id)
        for npc in area.npcs:
            if not is_walkable(list(area.map_data), npc.x, npc.y):
                raise ValueError(f"NPC em tile bloqueado: {npc.name}.")
