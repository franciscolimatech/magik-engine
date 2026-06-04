"""Basic generated appearance data for 2D player sprites."""

from __future__ import annotations

import json
from typing import Any


HAIR_STYLES = ("curto", "medio", "longo", "preso", "careca/coberto")
HAIR_COLORS = {
    "preto": (22, 20, 28),
    "castanho": (92, 55, 34),
    "loiro": (214, 184, 92),
    "branco": (226, 226, 218),
    "vermelho": (164, 54, 48),
    "azul escuro": (30, 54, 112),
}
EYE_COLORS = {
    "castanho": (97, 65, 43),
    "verde": (75, 156, 94),
    "azul": (74, 134, 196),
    "cinza": (156, 164, 172),
    "roxo": (146, 104, 210),
}
OUTFIT_STYLES = ("viajante", "aprendiz", "guerreiro leve", "manto", "roupa simples")
OUTFIT_COLORS = {
    "preto": (36, 34, 44),
    "branco": (218, 222, 226),
    "azul": (54, 96, 176),
    "vermelho": (170, 58, 62),
    "verde": (58, 130, 82),
    "roxo": (124, 76, 176),
    "marrom": (112, 72, 44),
}
DEFAULT_APPEARANCE = {
    "hair_style": "curto",
    "hair_color": "preto",
    "eye_color": "castanho",
    "outfit_style": "viajante",
    "outfit_color": "azul",
}
APPEARANCE_NOTE_PREFIX = "appearance: "


def normalize_appearance(appearance: dict[str, Any] | None = None) -> dict[str, str]:
    data = dict(DEFAULT_APPEARANCE)
    if appearance:
        data.update({key: str(value) for key, value in appearance.items() if value})
    if data["hair_style"] not in HAIR_STYLES:
        data["hair_style"] = DEFAULT_APPEARANCE["hair_style"]
    if data["hair_color"] not in HAIR_COLORS:
        data["hair_color"] = DEFAULT_APPEARANCE["hair_color"]
    if data["eye_color"] not in EYE_COLORS:
        data["eye_color"] = DEFAULT_APPEARANCE["eye_color"]
    if data["outfit_style"] not in OUTFIT_STYLES:
        data["outfit_style"] = DEFAULT_APPEARANCE["outfit_style"]
    if data["outfit_color"] not in OUTFIT_COLORS:
        data["outfit_color"] = DEFAULT_APPEARANCE["outfit_color"]
    return data


def appearance_to_note(appearance: dict[str, Any]) -> str:
    return APPEARANCE_NOTE_PREFIX + json.dumps(normalize_appearance(appearance), ensure_ascii=False)


def appearance_from_notes(notes: list[str] | None) -> dict[str, str] | None:
    for note in notes or []:
        if not isinstance(note, str) or not note.startswith(APPEARANCE_NOTE_PREFIX):
            continue
        payload = note.removeprefix(APPEARANCE_NOTE_PREFIX)
        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            return None
        if isinstance(data, dict):
            return normalize_appearance(data)
    return None


def appearance_summary(appearance: dict[str, Any]) -> str:
    data = normalize_appearance(appearance)
    return (
        f"Cabelo: {data['hair_style']} / {data['hair_color']}; "
        f"Olhos: {data['eye_color']}; "
        f"Roupa: {data['outfit_style']} / {data['outfit_color']}"
    )
