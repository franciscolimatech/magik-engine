from src.storage.json_storage import JSONStorage
from src.core.creatures import list_creatures
from src.core.npcs import list_npcs
from src.core.turn_combat import list_combats


def test_json_storage_creates_missing_file_with_default_data(tmp_path) -> None:
    storage = JSONStorage(tmp_path)

    data = storage.read_json("sessions.json", default=[])

    assert data == []
    assert storage.path_for("sessions.json").exists()


def test_creatures_json_is_created_automatically(tmp_path) -> None:
    storage = JSONStorage(tmp_path)

    assert list_creatures(storage) == []
    assert storage.path_for("creatures.json").exists()


def test_npcs_json_is_created_automatically(tmp_path) -> None:
    storage = JSONStorage(tmp_path)

    assert list_npcs(storage) == []
    assert storage.path_for("npcs.json").exists()


def test_combats_json_is_created_automatically(tmp_path) -> None:
    storage = JSONStorage(tmp_path)

    assert list_combats(storage) == []
    assert storage.path_for("combats.json").exists()
