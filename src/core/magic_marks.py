"""Official MAGIK magic mark catalog helpers."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import unicodedata
from typing import Any

from src.storage.types import JsonStore


@dataclass(frozen=True)
class MagicMark:
    id: str
    name: str
    school: str
    location_on_body: str
    description: str = ""
    grants_basic_spells: bool = True
    tags: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MagicMark":
        try:
            mark = cls(
                id=str(data["id"]),
                name=str(data["name"]),
                school=str(data["school"]),
                location_on_body=str(data["location_on_body"]),
                description=str(data.get("description", "")),
                grants_basic_spells=bool(data.get("grants_basic_spells", True)),
                tags=list(data.get("tags", [])),
                notes=list(data.get("notes", [])),
            )
        except KeyError as exc:
            raise ValueError(f"Marca magica invalida: campo ausente {exc}.") from exc
        validate_magic_mark(mark)
        return mark


def default_magic_mark_catalog_data() -> dict[str, Any]:
    return {"magic_marks": []}


def list_magic_marks(storage: JsonStore) -> list[MagicMark]:
    data = storage.read_json("magic_marks.json", default=default_magic_mark_catalog_data())
    marks_data = _read_collection(data, "magic_marks", "magic_marks.json")
    marks = [MagicMark.from_dict(item) for item in marks_data]
    validate_unique_magic_mark_ids(marks)
    return marks


def get_magic_mark(storage: JsonStore, mark_id: str) -> MagicMark:
    normalized = mark_id.strip().casefold()
    for mark in list_magic_marks(storage):
        if mark.id.casefold() == normalized:
            return mark
    raise ValueError(f"Marca magica nao encontrada: {mark_id}.")


def filter_magic_marks_by_school(marks: list[MagicMark], school: str) -> list[MagicMark]:
    normalized = _normalize_text(school)
    return [mark for mark in marks if _normalize_text(mark.school) == normalized]


def validate_unique_magic_mark_ids(marks: list[MagicMark]) -> None:
    seen: set[str] = set()
    for mark in marks:
        normalized = mark.id.strip().casefold()
        if not normalized:
            raise ValueError("Id da marca magica e obrigatorio.")
        if normalized in seen:
            raise ValueError(f"Id de marca magica duplicado: {mark.id}.")
        seen.add(normalized)


def validate_magic_mark(mark: MagicMark) -> None:
    if not mark.id.strip():
        raise ValueError("Id da marca magica e obrigatorio.")
    if not mark.name.strip():
        raise ValueError("Nome da marca magica e obrigatorio.")
    if not mark.school.strip():
        raise ValueError("Escola da marca magica e obrigatoria.")
    if not mark.location_on_body.strip():
        raise ValueError("Localizacao corporal da marca magica e obrigatoria.")
    if not all(isinstance(tag, str) for tag in mark.tags):
        raise ValueError("tags deve conter apenas strings.")
    if not all(isinstance(note, str) for note in mark.notes):
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
