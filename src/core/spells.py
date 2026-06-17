"""Official MAGIK spell catalog helpers.

The spell catalog is descriptive reference data. It does not teach spells to
characters, roll damage, apply effects, or evolve spells automatically.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import unicodedata
from typing import Any

from src.storage.types import JsonStore


@dataclass(frozen=True)
class OfficialSpell:
    id: str
    name: str
    school: str
    domain: int
    region: str
    description: str
    effect: str
    evolves_to: str | None = None
    evolution_requirements: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "OfficialSpell":
        try:
            spell = cls(
                id=str(data["id"]),
                name=str(data["name"]),
                school=str(data["school"]),
                domain=int(data.get("domain", 1)),
                region=str(data.get("region", "")),
                description=str(data.get("description", "")),
                effect=str(data.get("effect", "")),
                evolves_to=data.get("evolves_to"),
                evolution_requirements=list(data.get("evolution_requirements", [])),
                tags=list(data.get("tags", [])),
                notes=list(data.get("notes", [])),
            )
        except KeyError as exc:
            raise ValueError(f"Magia oficial invalida: campo ausente {exc}.") from exc
        validate_spell(spell)
        return spell


def default_spell_catalog_data() -> dict[str, Any]:
    return {"spells": []}


def list_official_spells(storage: JsonStore) -> list[OfficialSpell]:
    data = storage.read_json("spells.json", default=default_spell_catalog_data())
    spells_data = _read_collection(data, "spells", "spells.json")
    spells = [OfficialSpell.from_dict(item) for item in spells_data]
    validate_unique_spell_ids(spells)
    validate_spell_evolutions(spells)
    return spells


def get_official_spell(storage: JsonStore, spell_id: str) -> OfficialSpell:
    normalized = spell_id.strip().casefold()
    for spell in list_official_spells(storage):
        if spell.id.casefold() == normalized:
            return spell
    raise ValueError(f"Magia oficial nao encontrada: {spell_id}.")


def filter_spells_by_school(spells: list[OfficialSpell], school: str) -> list[OfficialSpell]:
    normalized = _normalize_text(school)
    return [spell for spell in spells if _normalize_text(spell.school) == normalized]


def filter_spells_by_domain(spells: list[OfficialSpell], domain: int) -> list[OfficialSpell]:
    return [spell for spell in spells if spell.domain == domain]


def list_spells_by_school(storage: JsonStore, school: str) -> list[OfficialSpell]:
    return filter_spells_by_school(list_official_spells(storage), school)


def list_spells_by_domain(storage: JsonStore, domain: int) -> list[OfficialSpell]:
    return filter_spells_by_domain(list_official_spells(storage), domain)


def validate_unique_spell_ids(spells: list[OfficialSpell]) -> None:
    seen: set[str] = set()
    for spell in spells:
        normalized = spell.id.strip().casefold()
        if not normalized:
            raise ValueError("Id da magia oficial e obrigatorio.")
        if normalized in seen:
            raise ValueError(f"Id de magia oficial duplicado: {spell.id}.")
        seen.add(normalized)


def validate_spell_evolutions(spells: list[OfficialSpell]) -> None:
    valid_ids = {spell.id for spell in spells}
    for spell in spells:
        if spell.evolves_to and spell.evolves_to not in valid_ids:
            raise ValueError(f"Evolucao invalida em {spell.id}: {spell.evolves_to}.")


def validate_spell(spell: OfficialSpell) -> None:
    if not spell.id.strip():
        raise ValueError("Id da magia oficial e obrigatorio.")
    if not spell.name.strip():
        raise ValueError("Nome da magia oficial e obrigatorio.")
    if not spell.school.strip():
        raise ValueError("Escola da magia oficial e obrigatoria.")
    if spell.domain not in {1, 2, 3}:
        raise ValueError("Dominio da magia oficial deve ser 1, 2 ou 3.")
    if not spell.region.strip():
        raise ValueError("Regiao da magia oficial e obrigatoria.")
    if not spell.description.strip():
        raise ValueError("Descricao da magia oficial e obrigatoria.")
    if not spell.effect.strip():
        raise ValueError("Efeito da magia oficial e obrigatorio.")
    if not all(isinstance(requirement, str) for requirement in spell.evolution_requirements):
        raise ValueError("Requisitos de evolucao devem conter apenas strings.")
    if not all(isinstance(tag, str) for tag in spell.tags):
        raise ValueError("tags deve conter apenas strings.")
    if not all(isinstance(note, str) for note in spell.notes):
        raise ValueError("notes deve conter apenas strings.")


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


def _normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.strip().casefold())
    return "".join(character for character in normalized if not unicodedata.combining(character))
