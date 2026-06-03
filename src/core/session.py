"""Session history records."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any

from src.storage.json_storage import JSONStorage


@dataclass(frozen=True)
class SessionEvent:
    timestamp: str
    character: str
    action: str
    result: str
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SessionEvent":
        return cls(
            timestamp=str(data["timestamp"]),
            character=str(data["character"]),
            action=str(data["action"]),
            result=str(data["result"]),
            notes=str(data.get("notes", "")),
        )


def register_event(
    storage: JSONStorage,
    character: str,
    action: str,
    result: str,
    notes: str = "",
) -> SessionEvent:
    event = SessionEvent(
        timestamp=datetime.now().astimezone().isoformat(timespec="seconds"),
        character=character,
        action=action,
        result=result,
        notes=notes,
    )
    events = storage.read_json("sessions.json", default=[])
    events.append(event.to_dict())
    storage.write_json("sessions.json", events)
    return event


def list_events(storage: JSONStorage) -> list[SessionEvent]:
    events = storage.read_json("sessions.json", default=[])
    return [SessionEvent.from_dict(event) for event in events]
