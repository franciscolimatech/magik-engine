from src.core.world import KNOWN_LOCATIONS, list_locations
from src.storage.json_storage import JSONStorage


def test_world_locations_are_loaded_from_storage(tmp_path) -> None:
    storage = JSONStorage(tmp_path)

    locations = list_locations(storage)

    assert len(locations) == len(KNOWN_LOCATIONS)
    assert "País de Magik" in {location.name for location in locations}
    assert "Vilarejo dos Gatos com TDAH" in {location.name for location in locations}


def test_world_locations_have_required_empty_fields(tmp_path) -> None:
    storage = JSONStorage(tmp_path)

    location = list_locations(storage)[0]

    assert location.notes == ""
    assert location.narrative_hooks == []
