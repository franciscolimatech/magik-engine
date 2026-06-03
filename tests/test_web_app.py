from fastapi.testclient import TestClient

from src.core.character import create_miko_meu, get_character
from src.storage.memory import MemoryStorage
from src.web.app import create_app


def make_client(storage: MemoryStorage | None = None) -> tuple[TestClient, MemoryStorage]:
    resolved_storage = storage or MemoryStorage({"characters.json": {"characters": [create_miko_meu().to_dict()]}})
    return TestClient(create_app(storage=resolved_storage)), resolved_storage


def test_web_app_initializes() -> None:
    client, _storage = make_client()

    assert client.app.title == "MAGIK Engine"


def test_home_route_responds() -> None:
    client, _storage = make_client()

    response = client.get("/")

    assert response.status_code == 200
    assert "MAGIK Engine" in response.text
    assert "Personagens" in response.text


def test_characters_route_lists_characters() -> None:
    client, _storage = make_client()

    response = client.get("/characters")

    assert response.status_code == 200
    assert "Miko Meu" in response.text
    assert "Sombrio" in response.text
    assert "miko-meu" in response.text


def test_character_detail_shows_character_sheet() -> None:
    client, _storage = make_client()

    response = client.get("/characters/miko-meu")

    assert response.status_code == 200
    assert "Miko Meu" in response.text
    assert "25/25" in response.text
    assert "Ikisaki" in response.text


def test_character_create_saves_and_redirects_to_sheet() -> None:
    client, storage = make_client()

    response = client.post(
        "/characters/new",
        data={
            "name": "Lia da Ponte",
            "character_class": "Guardia",
            "max_health": "32",
            "current_health": "20",
            "armor": "4",
            "equipment": "Lanterna, Corda",
            "notes": "Conhece as ruinas do norte.",
            "tags": "aliada, investigadora",
        },
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/characters/lia-da-ponte"
    created = get_character(storage, "lia-da-ponte")
    assert created.name == "Lia da Ponte"
    assert created.current_health == 20
    assert created.equipment == ["Lanterna", "Corda"]
    assert created.notes == ["Conhece as ruinas do norte."]
    assert created.tags == ["aliada", "investigadora"]


def test_character_create_result_page_displays_saved_character() -> None:
    client, _storage = make_client()

    response = client.post(
        "/characters/new",
        data={
            "name": "Ari",
            "character_class": "Oraculo",
            "max_health": "18",
            "current_health": "18",
            "armor": "1",
            "equipment": "Mapa",
            "notes": "",
            "tags": "vidente",
        },
    )

    assert response.status_code == 200
    assert "Ari" in response.text
    assert "Oraculo" in response.text
    assert "Mapa" in response.text


def test_character_create_invalid_current_health_does_not_save_partial_character() -> None:
    client, storage = make_client()

    response = client.post(
        "/characters/new",
        data={
            "name": "Vida Errada",
            "character_class": "Teste",
            "max_health": "10",
            "current_health": "15",
            "armor": "0",
            "equipment": "",
            "notes": "",
            "tags": "",
        },
    )

    assert response.status_code == 400
    assert "Vida atual nao pode ultrapassar a vida maxima." in response.text
    try:
        get_character(storage, "vida-errada")
    except ValueError:
        pass
    else:
        raise AssertionError("Personagem invalido nao deveria ser salvo parcialmente.")
