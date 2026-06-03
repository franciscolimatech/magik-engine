"""In-memory storage useful for tests and future services."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


class MemoryStorage:
    def __init__(self, initial_data: dict[str, Any] | None = None) -> None:
        self._data = deepcopy(initial_data or {})

    def read_json(self, filename: str, default: Any) -> Any:
        return deepcopy(self._data.get(filename, default))

    def write_json(self, filename: str, data: Any) -> None:
        self._data[filename] = deepcopy(data)
