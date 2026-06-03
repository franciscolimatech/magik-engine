"""Session history records."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any

from src.storage.types import JsonStore


@dataclass(frozen=True)
class SessionEvent:
    timestamp: str
    character: str
    action: str
    result: str
    notes: str = ""
    campaign_id: str | None = None
    campaign_session_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SessionEvent":
        try:
            return cls(
                timestamp=str(data["timestamp"]),
                character=str(data["character"]),
                action=str(data["action"]),
                result=str(data["result"]),
                notes=str(data.get("notes", "")),
                campaign_id=data.get("campaign_id"),
                campaign_session_id=data.get("campaign_session_id"),
            )
        except KeyError as exc:
            raise ValueError(f"Acontecimento de sessao invalido: campo ausente {exc}.") from exc


def register_event(
    storage: JsonStore,
    character: str,
    action: str,
    result: str,
    notes: str = "",
    campaign_id: str | None = None,
    campaign_session_id: str | None = None,
) -> SessionEvent:
    event = SessionEvent(
        timestamp=datetime.now().astimezone().isoformat(timespec="seconds"),
        character=_required_text(character, "personagem"),
        action=_required_text(action, "acao"),
        result=_required_text(result, "resultado"),
        notes=notes.strip(),
        campaign_id=campaign_id,
        campaign_session_id=campaign_session_id,
    )
    events = storage.read_json("sessions.json", default=[])
    if not isinstance(events, list):
        raise ValueError("sessions.json deve conter uma lista de acontecimentos.")
    events.append(event.to_dict())
    storage.write_json("sessions.json", events)
    return event


def list_events(storage: JsonStore) -> list[SessionEvent]:
    events = storage.read_json("sessions.json", default=[])
    if not isinstance(events, list):
        raise ValueError("sessions.json deve conter uma lista de acontecimentos.")
    if not all(isinstance(event, dict) for event in events):
        raise ValueError("Cada acontecimento em sessions.json deve ser um objeto JSON.")
    return [SessionEvent.from_dict(event) for event in events]


def _required_text(value: str, field_name: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise ValueError(f"O campo {field_name} e obrigatorio.")
    return cleaned
