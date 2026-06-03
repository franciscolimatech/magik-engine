import pytest

from src.core.character import create_character, create_miko_meu
from src.core.session import SessionEvent
from src.storage.memory import MemoryStorage
from src.ui.formatting import (
    format_character_list,
    format_character_sheet,
    format_history,
    format_manual_test_script,
)
from src.ui.terminal import select_character


def test_format_character_list_shows_number_name_class_and_id() -> None:
    miko = create_miko_meu()

    output = format_character_list([miko], allow_skip=True)

    assert "0 - Nenhum/Narrador" in output
    assert "1 - Miko Meu (Sombrio) [miko-meu]" in output


def test_format_character_sheet_is_readable() -> None:
    miko = create_miko_meu()

    output = format_character_sheet(miko)

    assert "Ficha: Miko Meu" in output
    assert "Vida: 25/25" in output
    assert "Armadura: 5" in output
    assert "Roleta Sombria: Dez Elos de Ikisaki" in output


def test_format_history_limits_latest_events() -> None:
    events = [
        SessionEvent(timestamp=f"2026-06-03T00:00:0{index}-03:00", character="Miko", action=f"Acao {index}", result="ok")
        for index in range(3)
    ]

    output = format_history(events, limit=2)

    assert "Acao 0" not in output
    assert "Acao 1" in output
    assert "Acao 2" in output


def test_format_history_rejects_invalid_limit() -> None:
    with pytest.raises(ValueError):
        format_history([], limit=0)


def test_manual_test_script_contains_recommended_steps() -> None:
    output = format_manual_test_script()

    assert "Roteiro de teste manual" in output
    assert "Usar Roleta Sombria da Ikisaki" in output
    assert "Ver historico" in output


def test_select_character_rejects_invalid_number(monkeypatch) -> None:
    storage = MemoryStorage({"characters.json": {"characters": [create_miko_meu().to_dict()]}})
    monkeypatch.setattr("builtins.input", lambda _prompt: "99")

    with pytest.raises(ValueError, match="Numero de personagem fora da lista"):
        select_character(storage)


def test_select_character_by_number(monkeypatch) -> None:
    storage = MemoryStorage({"characters.json": {"characters": [create_miko_meu().to_dict()]}})
    create_character(storage, name="Lia", character_class="Guardia", max_health=30)
    monkeypatch.setattr("builtins.input", lambda _prompt: "2")

    character = select_character(storage)

    assert character.name == "Lia"
