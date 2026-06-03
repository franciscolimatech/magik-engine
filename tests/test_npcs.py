import pytest

from src.core.npcs import (
    add_npc_note,
    add_npc_rumor,
    add_npc_status,
    change_npc_attitude,
    create_npc,
    get_npc,
    list_npcs,
    remove_npc_status,
)
from src.storage.memory import MemoryStorage


def test_create_npc() -> None:
    storage = MemoryStorage({"npcs.json": {"npcs": []}})

    npc = create_npc(storage, "Nara", "comerciante", attitude="amigavel")

    assert npc.id == "nara"
    assert npc.role == "comerciante"
    assert npc.attitude == "amigavel"


def test_list_npcs() -> None:
    storage = MemoryStorage({"npcs.json": {"npcs": []}})
    create_npc(storage, "Nara", "comerciante")

    assert [npc.name for npc in list_npcs(storage)] == ["Nara"]


def test_get_existing_npc() -> None:
    storage = MemoryStorage({"npcs.json": {"npcs": []}})
    create_npc(storage, "Nara", "comerciante")

    assert get_npc(storage, "nara").name == "Nara"


def test_get_missing_npc_raises_error() -> None:
    storage = MemoryStorage({"npcs.json": {"npcs": []}})

    with pytest.raises(ValueError):
        get_npc(storage, "ninguem")


def test_change_npc_attitude() -> None:
    storage = MemoryStorage({"npcs.json": {"npcs": []}})
    create_npc(storage, "Nara", "comerciante")

    npc = change_npc_attitude(storage, "nara", "desconfiada")

    assert npc.attitude == "desconfiada"


def test_add_npc_rumor() -> None:
    storage = MemoryStorage({"npcs.json": {"npcs": []}})
    create_npc(storage, "Nara", "comerciante")

    npc = add_npc_rumor(storage, "nara", "Ouviu algo estranho.")

    assert npc.rumors == ["Ouviu algo estranho."]


def test_add_and_remove_npc_status() -> None:
    storage = MemoryStorage({"npcs.json": {"npcs": []}})
    create_npc(storage, "Nara", "comerciante")

    with_status = add_npc_status(storage, "nara", "ocupada")
    without_status = remove_npc_status(storage, "nara", "ocupada")

    assert "ocupada" in with_status.status
    assert "ocupada" not in without_status.status


def test_add_npc_note() -> None:
    storage = MemoryStorage({"npcs.json": {"npcs": []}})
    create_npc(storage, "Nara", "comerciante")

    npc = add_npc_note(storage, "nara", "Exemplo de NPC.")

    assert npc.notes == ["Exemplo de NPC."]
