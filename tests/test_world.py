import pytest

from src.core.world import (
    KNOWN_LOCATIONS,
    OFFICIAL_MAGIK_LOCATION_IDS,
    get_location_by_id,
    list_locations,
    list_official_locations,
    list_regions,
    validate_unique_ids,
)
from src.storage.json_storage import JSONStorage
from src.storage.memory import MemoryStorage


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


def test_official_regions_load_with_default_data(tmp_path) -> None:
    storage = JSONStorage(tmp_path)

    regions = list_regions(storage)

    assert len(regions) == 1
    assert regions[0].id == "pais-de-magik"
    assert "oficial" in regions[0].tags
    assert "floresta-viridian" in regions[0].locations


def test_official_locations_load_with_unique_ids(tmp_path) -> None:
    storage = JSONStorage(tmp_path)

    locations = list_official_locations(storage)
    ids = [location.id for location in locations]

    assert len(ids) == len(set(ids))
    assert set(OFFICIAL_MAGIK_LOCATION_IDS).issubset(set(ids))
    assert all("oficial" in location.tags for location in locations)


def test_get_official_location_by_id(tmp_path) -> None:
    storage = JSONStorage(tmp_path)

    location = get_location_by_id(storage, "floresta-viridian")

    assert location.name == "Floresta Viridian"
    assert location.type == "bioma"
    assert "árvores" in location.description


def test_missing_or_empty_official_location_json_uses_safe_default(tmp_path) -> None:
    storage = JSONStorage(tmp_path)
    storage.write_json("locations.json", {})

    locations = list_official_locations(storage)

    assert get_location_by_id(storage, "cidade-de-pedralume").name == "Cidade de Pedralume"
    assert len(locations) == len(OFFICIAL_MAGIK_LOCATION_IDS)


def test_world_state_compatibility_is_preserved() -> None:
    storage = MemoryStorage(
        {
            "world_state.json": {
                "locations": [
                    {
                        "name": "Local Antigo",
                        "type": "cidade",
                        "notes": "Formato legado.",
                        "narrative_hooks": ["gancho"],
                    }
                ]
            }
        }
    )

    locations = list_locations(storage)

    assert any(location.name == "Local Antigo" for location in locations)
    assert any(location.name == "Cidade de Pedralume" for location in locations)


def test_duplicate_official_location_ids_are_rejected() -> None:
    storage = MemoryStorage(
        {
            "locations.json": {
                "locations": [
                    {
                        "id": "floresta-viridian",
                        "name": "Floresta Viridian",
                        "type": "bioma",
                    },
                    {
                        "id": "floresta-viridian",
                        "name": "Outra Floresta",
                        "type": "bioma",
                    },
                ]
            }
        }
    )

    with pytest.raises(ValueError, match="duplicado"):
        validate_unique_ids(list_official_locations(storage))
