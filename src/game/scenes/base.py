"""Base scene contract."""

from __future__ import annotations


class BaseScene:
    def handle_event(self, event) -> None:
        raise NotImplementedError

    def update(self) -> None:
        raise NotImplementedError

    def draw(self, surface) -> None:
        raise NotImplementedError
