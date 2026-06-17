"""World state helpers for known MAGIK locations."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from src.storage.types import JsonStore


@dataclass(frozen=True)
class WorldLocation:
    name: str
    type: str
    notes: str = ""
    narrative_hooks: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WorldLocation":
        try:
            return cls(
                name=str(data["name"]),
                type=str(data["type"]),
                notes=str(data.get("notes", "")),
                narrative_hooks=list(data.get("narrative_hooks", [])),
            )
        except KeyError as exc:
            raise ValueError(f"Local do mundo invalido: campo ausente {exc}.") from exc


@dataclass(frozen=True)
class OfficialRegion:
    id: str
    name: str
    description: str = ""
    tags: list[str] = field(default_factory=list)
    locations: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "OfficialRegion":
        try:
            region = cls(
                id=str(data["id"]),
                name=str(data["name"]),
                description=str(data.get("description", "")),
                tags=list(data.get("tags", [])),
                locations=list(data.get("locations", [])),
                notes=list(data.get("notes", [])),
            )
        except KeyError as exc:
            raise ValueError(f"Regiao oficial invalida: campo ausente {exc}.") from exc
        validate_unique_ids([region])
        return region


@dataclass(frozen=True)
class OfficialLocation:
    id: str
    name: str
    type: str
    description: str = ""
    tags: list[str] = field(default_factory=list)
    connections: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    region_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "OfficialLocation":
        try:
            location = cls(
                id=str(data["id"]),
                name=str(data["name"]),
                type=str(data["type"]),
                description=str(data.get("description", "")),
                tags=list(data.get("tags", [])),
                connections=list(data.get("connections", [])),
                notes=list(data.get("notes", [])),
                region_id=data.get("region_id"),
            )
        except KeyError as exc:
            raise ValueError(f"Local oficial invalido: campo ausente {exc}.") from exc
        validate_unique_ids([location])
        return location


KNOWN_LOCATIONS: tuple[WorldLocation, ...] = (
    WorldLocation("País de Magik", "região"),
    WorldLocation("Cidade de Pedralume", "capital"),
    WorldLocation("Floresta Viridian", "floresta"),
    WorldLocation("Campos dos Kriots", "regiao"),
    WorldLocation("Lago das Carpas Profetas", "lago"),
    WorldLocation("Estrada do Viajante", "estrada"),
    WorldLocation("Floresta do Avesso", "floresta"),
    WorldLocation("Brejo do Esquecimento", "brejo"),
    WorldLocation("Montanhas Trippi", "montanha"),
    WorldLocation("Vale Vermilion", "vale"),
    WorldLocation("Penhascos do Último Passo", "penhasco"),
    WorldLocation("Avelgard", "cidade"),
    WorldLocation("Varnhollow", "cidade"),
    WorldLocation("Corvenn", "cidade"),
    WorldLocation("Dunwall", "cidade"),
    WorldLocation("Brisvale", "cidade"),
    WorldLocation("Norwick", "cidade"),
    WorldLocation("Eldermor", "cidade"),
    WorldLocation("Arkenfor", "cidade"),
    WorldLocation("Velharth", "cidade"),
    WorldLocation("Stonewatch", "cidade"),
    WorldLocation("Redmoor", "cidade"),
    WorldLocation("Thornwich", "cidade"),
    WorldLocation("Vilarejo dos Gatos Autistas", "mini vilarejo"),
    WorldLocation("Vilarejo dos Gatos com TDAH", "mini vilarejo"),
)

OFFICIAL_MAGIK_LOCATION_IDS: tuple[str, ...] = (
    "montanhas-trippi",
    "floresta-viridian",
    "vale-vermilion",
    "brejo-do-esquecimento",
    "cidade-de-pedralume",
    "campos-dos-kriots",
    "lago-das-carpas-profetas",
    "floresta-do-avesso",
    "penhascos-do-ultimo-passo",
    "estrada-do-viajante",
    "avelgard",
    "brisvale",
    "velharth",
    "varnhollow",
    "corvenn",
    "dunwall",
    "eldermoor",
    "arkenford",
    "norwick",
    "stonewatch",
    "redmoor",
    "thornwick",
    "vilarejo-dos-gatos-autistas",
    "vilarejo-dos-gatos-com-tdah",
)

OFFICIAL_LOCATION_CONNECTIONS: dict[str, tuple[str, ...]] = {
    "montanhas-trippi": (
        "vilarejo-dos-gatos-autistas",
        "vilarejo-dos-gatos-com-tdah",
        "cidade-de-pedralume",
        "brejo-do-esquecimento",
    ),
    "floresta-viridian": (
        "avelgard",
        "varnhollow",
        "cidade-de-pedralume",
    ),
    "vale-vermilion": (
        "thornwick",
        "redmoor",
        "brejo-do-esquecimento",
    ),
    "brejo-do-esquecimento": (
        "cidade-de-pedralume",
        "eldermoor",
        "vale-vermilion",
        "floresta-do-avesso",
        "montanhas-trippi",
    ),
    "cidade-de-pedralume": (
        "estrada-do-viajante",
        "floresta-viridian",
        "montanhas-trippi",
        "brejo-do-esquecimento",
        "varnhollow",
        "brisvale",
    ),
    "campos-dos-kriots": (
        "varnhollow",
        "corvenn",
        "floresta-viridian",
    ),
    "lago-das-carpas-profetas": (
        "brisvale",
        "corvenn",
        "dunwall",
    ),
    "floresta-do-avesso": (
        "brisvale",
        "norwick",
        "arkenford",
        "brejo-do-esquecimento",
    ),
    "penhascos-do-ultimo-passo": (
        "velharth",
        "stonewatch",
        "redmoor",
        "arkenford",
    ),
    "estrada-do-viajante": (
        "cidade-de-pedralume",
        "brisvale",
        "norwick",
        "varnhollow",
    ),
    "avelgard": (
        "floresta-viridian",
        "varnhollow",
        "cidade-de-pedralume",
    ),
    "brisvale": (
        "lago-das-carpas-profetas",
        "cidade-de-pedralume",
        "estrada-do-viajante",
        "floresta-do-avesso",
        "norwick",
    ),
    "velharth": (
        "penhascos-do-ultimo-passo",
        "stonewatch",
        "arkenford",
    ),
    "varnhollow": (
        "cidade-de-pedralume",
        "campos-dos-kriots",
        "floresta-viridian",
        "avelgard",
        "corvenn",
        "estrada-do-viajante",
    ),
    "corvenn": (
        "campos-dos-kriots",
        "lago-das-carpas-profetas",
        "varnhollow",
        "dunwall",
    ),
    "dunwall": (
        "lago-das-carpas-profetas",
        "corvenn",
    ),
    "eldermoor": (
        "brejo-do-esquecimento",
        "cidade-de-pedralume",
    ),
    "arkenford": (
        "floresta-do-avesso",
        "penhascos-do-ultimo-passo",
        "velharth",
    ),
    "norwick": (
        "estrada-do-viajante",
        "brisvale",
        "floresta-do-avesso",
    ),
    "stonewatch": (
        "penhascos-do-ultimo-passo",
        "velharth",
        "redmoor",
    ),
    "redmoor": (
        "vale-vermilion",
        "penhascos-do-ultimo-passo",
        "stonewatch",
        "thornwick",
    ),
    "thornwick": (
        "vale-vermilion",
        "redmoor",
        "brejo-do-esquecimento",
    ),
    "vilarejo-dos-gatos-autistas": (
        "montanhas-trippi",
    ),
    "vilarejo-dos-gatos-com-tdah": (
        "montanhas-trippi",
    ),
}

OFFICIAL_REGIONS: tuple[OfficialRegion, ...] = (
    OfficialRegion(
        id="pais-de-magik",
        name="País de Magik",
        description="País conhecido do cenário oficial atual do RPG MAGIK.",
        tags=["oficial", "lore"],
        locations=list(OFFICIAL_MAGIK_LOCATION_IDS),
    ),
)

OFFICIAL_LOCATIONS: tuple[OfficialLocation, ...] = (
    OfficialLocation(
        id="montanhas-trippi",
        name="Montanhas Trippi",
        type="bioma",
        description="Gigantesca cadeia de montanhas ao norte do país conhecido, tomada por cavernas, túneis naturais e passagens estreitas. É associada aos vilarejos dos gatos, a tesouros lendários e a ventos que parecem produzir vozes, assobios e risadas distantes.",
        tags=["oficial", "lore"],
        region_id="pais-de-magik",
    ),
    OfficialLocation(
        id="floresta-viridian",
        name="Floresta Viridian",
        type="bioma",
        description="Floresta ancestral de árvores enormes, musgo verde-esmeralda e copas que bloqueiam a luz. Viajantes relatam sensação de observação constante, galhos que apontam caminhos e uma ligação antiga com os Wrym Viridian.",
        tags=["oficial", "lore"],
        region_id="pais-de-magik",
    ),
    OfficialLocation(
        id="vale-vermilion",
        name="Vale Vermilion",
        type="bioma",
        description="Vale silencioso coberto por flores vermelhas que crescem onde alguém morreu. Ao anoitecer, as flores se fecham e produzem sussurros quase imperceptíveis.",
        tags=["oficial", "lore"],
        region_id="pais-de-magik",
    ),
    OfficialLocation(
        id="brejo-do-esquecimento",
        name="Brejo do Esquecimento",
        type="bioma",
        description="Região pantanosa envolta por névoa permanente. Quanto mais tempo alguém permanece ali, mais difícil se torna lembrar nomes, datas ou o motivo da viagem.",
        tags=["oficial", "lore"],
        region_id="pais-de-magik",
    ),
    OfficialLocation(
        id="cidade-de-pedralume",
        name="Cidade de Pedralume",
        type="capital",
        description="Maior cidade do país conhecido e principal centro de comércio, conhecimento e política. Foi construída sobre cristais luminosos que iluminam ruas, casas e estabelecimentos.",
        tags=["oficial", "lore"],
        region_id="pais-de-magik",
    ),
    OfficialLocation(
        id="campos-dos-kriots",
        name="Campos dos Kriots",
        type="bioma",
        description="Planície vasta com pequenas construções de pedra espalhadas. Algumas são casas ou ruínas; outras podem ser Kriots Terrosos aguardando vítimas.",
        tags=["oficial", "lore"],
        region_id="pais-de-magik",
    ),
    OfficialLocation(
        id="lago-das-carpas-profetas",
        name="Lago das Carpas Profetas",
        type="bioma",
        description="Lago de águas cristalinas e superfície estranhamente calma, conhecido pelas Carpas Profetas que respondem perguntas de viajantes, nem sempre com a verdade.",
        tags=["oficial", "lore"],
        region_id="pais-de-magik",
    ),
    OfficialLocation(
        id="floresta-do-avesso",
        name="Floresta do Avesso",
        type="bioma",
        description="Floresta onde sombras apontam para direções erradas, ficam imóveis ou se separam de seus donos. Muitos acreditam que seja uma rachadura entre realidades.",
        tags=["oficial", "lore"],
        region_id="pais-de-magik",
    ),
    OfficialLocation(
        id="penhascos-do-ultimo-passo",
        name="Penhascos do Último Passo",
        type="bioma",
        description="Falésias gigantescas no limite entre a terra firme e um oceano inexplorado. Quem permanece perto da borda sente uma curiosidade crescente pelo horizonte e pode ouvir vozes vindas do mar.",
        tags=["oficial", "lore"],
        region_id="pais-de-magik",
    ),
    OfficialLocation(
        id="estrada-do-viajante",
        name="Estrada do Viajante",
        type="estrada",
        description="Antiga estrada de pedra que atravessa as regiões do mapa. É associada ao misterioso Viajante, que oferece artefatos e conhecimento em troca de favores ou escolhas difíceis.",
        tags=["oficial", "lore"],
        region_id="pais-de-magik",
    ),
    OfficialLocation(
        id="avelgard",
        name="Avelgard",
        type="cidade",
        description="Cidade cercada pelas bordas da Floresta Viridian, marcada por madeira, caça, comércio com viajantes e histórias sobre árvores que mudam de lugar.",
        tags=["oficial", "lore"],
        region_id="pais-de-magik",
    ),
    OfficialLocation(
        id="brisvale",
        name="Brisvale",
        type="cidade",
        description="Cidade próxima ao Lago das Carpas Profetas, conhecida por pescadores, estudiosos e viajantes em busca de respostas das carpas.",
        tags=["oficial", "lore"],
        region_id="pais-de-magik",
    ),
    OfficialLocation(
        id="velharth",
        name="Velharth",
        type="cidade",
        description="Maior cidade dos Penhascos do Último Passo, construída sobre a borda das falésias e sustentada pelo comércio marítimo.",
        tags=["oficial", "lore"],
        region_id="pais-de-magik",
    ),
    OfficialLocation(
        id="varnhollow",
        name="Varnhollow",
        type="vila",
        description="Vila agrícola entre Pedralume e os Campos dos Kriots, conhecida por casas resistentes e pela cautela com o que pode caminhar por perto.",
        tags=["oficial", "lore"],
        region_id="pais-de-magik",
    ),
    OfficialLocation(
        id="corvenn",
        name="Corvenn",
        type="vila",
        description="Pequena vila de pescadores ao oeste do Lago das Carpas Profetas. Seus moradores evitam fazer perguntas às carpas.",
        tags=["oficial", "lore"],
        region_id="pais-de-magik",
    ),
    OfficialLocation(
        id="dunwall",
        name="Dunwall",
        type="vila",
        description="Vila costeira isolada de vida simples, onde navios desaparecidos às vezes surgem encalhados nas praias durante a madrugada.",
        tags=["oficial", "lore"],
        region_id="pais-de-magik",
    ),
    OfficialLocation(
        id="eldermoor",
        name="Eldermoor",
        type="vila",
        description="Vila fundada na fronteira do Brejo do Esquecimento, onde habitantes registram tudo em diários, placas e anotações para não depender apenas da memória.",
        tags=["oficial", "lore"],
        region_id="pais-de-magik",
    ),
    OfficialLocation(
        id="arkenford",
        name="Arkenford",
        type="vila",
        description="Vila entre a Floresta do Avesso e os Penhascos do Último Passo. Seus moradores evitam sair após o anoitecer por medo das sombras da floresta.",
        tags=["oficial", "lore"],
        region_id="pais-de-magik",
    ),
    OfficialLocation(
        id="norwick",
        name="Norwick",
        type="vila",
        description="Comunidade ao longo da Estrada do Viajante, conhecida por estalagens e por ser um ótimo lugar para ouvir rumores, histórias e mentiras.",
        tags=["oficial", "lore"],
        region_id="pais-de-magik",
    ),
    OfficialLocation(
        id="stonewatch",
        name="Stonewatch",
        type="vila",
        description="Vila-fortaleza sobre os penhascos, onde habitantes observam o oceano e mantêm fogueiras acesas durante tempestades.",
        tags=["oficial", "lore"],
        region_id="pais-de-magik",
    ),
    OfficialLocation(
        id="redmoor",
        name="Redmoor",
        type="vila",
        description="Vila entre o Vale Vermilion e os Penhascos do Último Passo, ligada à coleta das flores vermelhas do vale.",
        tags=["oficial", "lore"],
        region_id="pais-de-magik",
    ),
    OfficialLocation(
        id="thornwick",
        name="Thornwick",
        type="vila",
        description="Vila nas fronteiras do Vale Vermilion. Apesar da proximidade com uma região considerada amaldiçoada, seus habitantes são acolhedores.",
        tags=["oficial", "lore"],
        region_id="pais-de-magik",
    ),
    OfficialLocation(
        id="vilarejo-dos-gatos-autistas",
        name="Vilarejo dos Gatos Autistas",
        type="mini vilarejo",
        description="Assentamento escondido na zona oeste das Montanhas Trippi, formado por estruturas simples entre pedras e cavernas antigas.",
        tags=["oficial", "lore"],
        region_id="pais-de-magik",
    ),
    OfficialLocation(
        id="vilarejo-dos-gatos-com-tdah",
        name="Vilarejo dos Gatos com TDAH",
        type="mini vilarejo",
        description="Vilarejo na zona leste das Montanhas Trippi, em constante reforma e marcado por criatividade, projetos inacabados e soluções inesperadas.",
        tags=["oficial", "lore"],
        region_id="pais-de-magik",
    ),
)


def default_world_state() -> dict[str, Any]:
    return {"locations": [location.to_dict() for location in KNOWN_LOCATIONS]}


def default_regions_data() -> dict[str, Any]:
    return {"regions": [region.to_dict() for region in OFFICIAL_REGIONS]}


def default_locations_data() -> dict[str, Any]:
    return {"locations": [_with_default_connections(location).to_dict() for location in OFFICIAL_LOCATIONS]}


def ensure_world_state(storage: JsonStore) -> dict[str, Any]:
    data = storage.read_json("world_state.json", default=default_world_state())
    if not isinstance(data, dict):
        raise ValueError("world_state.json deve conter um objeto JSON.")

    locations = data.get("locations")
    if not isinstance(locations, list):
        data["locations"] = [location.to_dict() for location in KNOWN_LOCATIONS]
        storage.write_json("world_state.json", data)
        return data

    known_by_name = {location.name: location for location in KNOWN_LOCATIONS}
    existing_names = {str(location.get("name")) for location in locations if isinstance(location, dict)}
    missing_locations = [
        location.to_dict()
        for name, location in known_by_name.items()
        if name not in existing_names
    ]
    if missing_locations:
        data["locations"] = locations + missing_locations
        storage.write_json("world_state.json", data)
    return data


def list_locations(storage: JsonStore) -> list[WorldLocation]:
    data = ensure_world_state(storage)
    locations = data["locations"]
    if not all(isinstance(location, dict) for location in locations):
        raise ValueError("Cada local em world_state.json deve ser um objeto JSON.")
    return [WorldLocation.from_dict(location) for location in locations]


def list_regions(storage: JsonStore) -> list[OfficialRegion]:
    data = storage.read_json("regions.json", default=default_regions_data())
    regions_data = _read_collection(data, "regions", "regions.json")
    if not regions_data:
        data = default_regions_data()
        storage.write_json("regions.json", data)
        regions_data = data["regions"]
    regions = [OfficialRegion.from_dict(region) for region in regions_data]
    validate_unique_ids(regions)
    return regions


def list_official_locations(storage: JsonStore) -> list[OfficialLocation]:
    data = storage.read_json("locations.json", default=default_locations_data())
    locations_data = _read_collection(data, "locations", "locations.json")
    if not locations_data:
        data = default_locations_data()
        storage.write_json("locations.json", data)
        locations_data = data["locations"]
    locations = [OfficialLocation.from_dict(location) for location in locations_data]
    validate_unique_ids(locations)
    validate_location_connections(locations)
    return locations


def get_location_by_id(storage: JsonStore, location_id: str) -> OfficialLocation:
    normalized = location_id.strip().casefold()
    for location in list_official_locations(storage):
        if location.id.casefold() == normalized:
            return location
    raise ValueError(f"Local oficial nao encontrado: {location_id}.")


def validate_unique_ids(items: list[OfficialRegion] | list[OfficialLocation]) -> None:
    seen: set[str] = set()
    for item in items:
        item_id = item.id.strip()
        if not item_id:
            raise ValueError("Id oficial e obrigatorio.")
        normalized = item_id.casefold()
        if normalized in seen:
            raise ValueError(f"Id oficial duplicado: {item.id}.")
        seen.add(normalized)


def validate_location_connections(locations: list[OfficialLocation]) -> None:
    valid_ids = {location.id for location in locations}
    for location in locations:
        for connection_id in location.connections:
            if connection_id not in valid_ids:
                raise ValueError(f"Conexao invalida em {location.id}: {connection_id}.")


def _with_default_connections(location: OfficialLocation) -> OfficialLocation:
    if location.connections:
        return location
    return OfficialLocation(
        id=location.id,
        name=location.name,
        type=location.type,
        description=location.description,
        tags=list(location.tags),
        connections=list(OFFICIAL_LOCATION_CONNECTIONS.get(location.id, ())),
        notes=list(location.notes),
        region_id=location.region_id,
    )


def _read_collection(data: Any, key: str, filename: str) -> list[dict[str, Any]]:
    if isinstance(data, dict):
        collection = data.get(key, [])
    elif isinstance(data, list):
        collection = data
    else:
        raise ValueError(f"{filename} deve conter uma lista ou um objeto com a chave '{key}'.")
    if not isinstance(collection, list):
        raise ValueError(f"A chave '{key}' em {filename} deve conter uma lista.")
    if not all(isinstance(item, dict) for item in collection):
        raise ValueError(f"Cada item em {filename} deve ser um objeto JSON.")
    return collection
