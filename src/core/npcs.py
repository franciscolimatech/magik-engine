"""NPC management."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import re
from typing import Any

from src.storage.types import JsonStore


NPC_ROLES = {
    "comerciante",
    "aldeao",
    "guia",
    "nobre",
    "guarda",
    "viajante",
    "informante",
    "vilao",
    "aliado",
    "neutro",
    "outro",
}

NPC_ATTITUDES = {
    "amigavel",
    "neutra",
    "desconfiada",
    "hostil",
    "assustada",
    "interesseira",
    "misteriosa",
}


@dataclass
class NPC:
    id: str
    name: str
    role: str
    location: str | None = None
    attitude: str = "neutra"
    description: str = ""
    rumors: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    status: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "NPC":
        try:
            npc = cls(
                id=str(data["id"]),
                name=str(data["name"]),
                role=str(data.get("role", "outro")),
                location=data.get("location"),
                attitude=str(data.get("attitude", "neutra")),
                description=str(data.get("description", "")),
                rumors=list(data.get("rumors", [])),
                notes=list(data.get("notes", [])),
                tags=list(data.get("tags", [])),
                status=list(data.get("status", [])),
            )
        except KeyError as exc:
            raise ValueError(f"NPC invalido: campo ausente {exc}.") from exc
        validate_npc(npc)
        return npc


def default_npc_data() -> dict[str, Any]:
    return {"npcs": []}


def list_npcs(storage: JsonStore) -> list[NPC]:
    data = storage.read_json("npcs.json", default=default_npc_data())
    if isinstance(data, dict):
        npcs_data = data.get("npcs", [])
    elif isinstance(data, list):
        npcs_data = data
    else:
        raise ValueError("npcs.json deve conter uma lista ou um objeto com a chave 'npcs'.")
    if not isinstance(npcs_data, list):
        raise ValueError("A chave 'npcs' deve conter uma lista.")
    return [NPC.from_dict(item) for item in npcs_data]


def save_npcs(storage: JsonStore, npcs: list[NPC]) -> None:
    _ensure_unique_ids(npcs)
    storage.write_json("npcs.json", {"npcs": [npc.to_dict() for npc in npcs]})


def get_npc(storage: JsonStore, npc_id: str) -> NPC:
    normalized = npc_id.strip().casefold()
    for npc in list_npcs(storage):
        if npc.id.casefold() == normalized:
            return npc
    raise ValueError(f"NPC nao encontrado: {npc_id}.")


def create_npc(
    storage: JsonStore,
    name: str,
    role: str,
    npc_id: str | None = None,
    location: str | None = None,
    attitude: str = "neutra",
    description: str = "",
    tags: list[str] | None = None,
) -> NPC:
    if not name.strip():
        raise ValueError("Nome do NPC e obrigatorio.")
    npcs = list_npcs(storage)
    new_id = _resolve_new_id(npcs, npc_id or name, explicit=npc_id is not None)
    npc = NPC(
        id=new_id,
        name=name.strip(),
        role=role.strip() or "outro",
        location=location.strip() if location else None,
        attitude=attitude.strip() or "neutra",
        description=description.strip(),
        tags=tags or [],
    )
    validate_npc(npc)
    npcs.append(npc)
    save_npcs(storage, npcs)
    return npc


def update_npc(storage: JsonStore, npc: NPC) -> NPC:
    validate_npc(npc)
    npcs = list_npcs(storage)
    for index, current in enumerate(npcs):
        if current.id.casefold() == npc.id.casefold():
            npcs[index] = npc
            save_npcs(storage, npcs)
            return npc
    raise ValueError(f"NPC nao encontrado: {npc.id}.")


def remove_npc(storage: JsonStore, npc_id: str) -> NPC:
    npc = get_npc(storage, npc_id)
    save_npcs(storage, [current for current in list_npcs(storage) if current.id != npc.id])
    return npc


def change_npc_attitude(storage: JsonStore, npc_id: str, attitude: str) -> NPC:
    npc = get_npc(storage, npc_id)
    npc.attitude = attitude.strip()
    return update_npc(storage, npc)


def add_npc_rumor(storage: JsonStore, npc_id: str, rumor: str) -> NPC:
    npc = get_npc(storage, npc_id)
    npc.rumors.append(_required_text(rumor, "rumor"))
    return update_npc(storage, npc)


def add_npc_note(storage: JsonStore, npc_id: str, note: str) -> NPC:
    npc = get_npc(storage, npc_id)
    npc.notes.append(_required_text(note, "observacao"))
    return update_npc(storage, npc)


def add_npc_status(storage: JsonStore, npc_id: str, status: str) -> NPC:
    npc = get_npc(storage, npc_id)
    cleaned = _required_text(status, "status")
    if cleaned not in npc.status:
        npc.status.append(cleaned)
    return update_npc(storage, npc)


def remove_npc_status(storage: JsonStore, npc_id: str, status: str) -> NPC:
    npc = get_npc(storage, npc_id)
    cleaned = _required_text(status, "status")
    try:
        npc.status.remove(cleaned)
    except ValueError as exc:
        raise ValueError(f"Status nao encontrado: {cleaned}.") from exc
    return update_npc(storage, npc)


def validate_npc(npc: NPC) -> None:
    if not npc.id.strip():
        raise ValueError("Id do NPC e obrigatorio.")
    if not npc.name.strip():
        raise ValueError("Nome do NPC e obrigatorio.")
    if npc.role not in NPC_ROLES:
        valid = ", ".join(sorted(NPC_ROLES))
        raise ValueError(f"Papel de NPC invalido. Use um destes: {valid}.")
    if npc.attitude not in NPC_ATTITUDES:
        valid = ", ".join(sorted(NPC_ATTITUDES))
        raise ValueError(f"Atitude de NPC invalida. Use uma destas: {valid}.")


def generate_npc_id(name: str) -> str:
    normalized = _normalize_ascii(name)
    slug = re.sub(r"[^a-z0-9]+", "-", normalized).strip("-")
    return slug or "npc"


def _resolve_new_id(npcs: list[NPC], value: str, explicit: bool) -> str:
    candidate = generate_npc_id(value)
    existing = {npc.id.casefold() for npc in npcs}
    if candidate.casefold() not in existing:
        return candidate
    if explicit:
        raise ValueError(f"Id de NPC duplicado: {candidate}.")
    suffix = 2
    while f"{candidate}-{suffix}".casefold() in existing:
        suffix += 1
    return f"{candidate}-{suffix}"


def _ensure_unique_ids(npcs: list[NPC]) -> None:
    seen: set[str] = set()
    for npc in npcs:
        normalized = npc.id.casefold()
        if normalized in seen:
            raise ValueError(f"Id de NPC duplicado: {npc.id}.")
        seen.add(normalized)


def _required_text(value: str, field_name: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise ValueError(f"O campo {field_name} e obrigatorio.")
    return cleaned


def _normalize_ascii(value: str) -> str:
    import unicodedata

    normalized = unicodedata.normalize("NFKD", value.strip().casefold())
    return "".join(character for character in normalized if not unicodedata.combining(character))
