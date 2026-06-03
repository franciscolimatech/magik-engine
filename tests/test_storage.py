from src.storage.json_storage import JSONStorage


def test_json_storage_creates_missing_file_with_default_data(tmp_path) -> None:
    storage = JSONStorage(tmp_path)

    data = storage.read_json("sessions.json", default=[])

    assert data == []
    assert storage.path_for("sessions.json").exists()
