"""JSON file storage adapter."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class JSONStorage:
    def __init__(self, base_path: str | Path) -> None:
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def path_for(self, filename: str) -> Path:
        return self.base_path / filename

    def read_json(self, filename: str, default: Any) -> Any:
        path = self.path_for(filename)
        if not path.exists():
            self.write_json(filename, default)
            return default
        if path.stat().st_size == 0:
            return default

        with path.open("r", encoding="utf-8") as file:
            return json.load(file)

    def write_json(self, filename: str, data: Any) -> None:
        path = self.path_for(filename)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)
            file.write("\n")
