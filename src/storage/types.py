"""Shared storage protocols."""

from __future__ import annotations

from typing import Any, Protocol


class JsonStore(Protocol):
    """Minimal contract required by domain helpers that persist JSON data."""

    def read_json(self, filename: str, default: Any) -> Any:
        """Read a JSON document, creating it with default data when missing."""

    def write_json(self, filename: str, data: Any) -> None:
        """Persist a JSON document."""
