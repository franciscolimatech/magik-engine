from fastapi.testclient import TestClient

from src.core.character import create_miko_meu, get_character
from src.storage.memory import MemoryStorage
from src.web.app import create_app


def make_client(storage: MemoryStorage | None = None) -> tuple[TestClient, MemoryStorage]:
    resolved_storage = storage or MemoryStorage({"characters.json": {"characters": [create_miko_meu().to_dict()]}})
    return TestClient(create_app(storage=resolved_storage)), resolved_storage


def advanced_character_form(**overrides: str) -> dict[str, str]:
    data = {
        "name": "Lia da Ponte",
        "character_class": "Guardia",
        "short_description": "Guardia de pontes antigas.",
        "tags": "aliada, investigadora",
        "max_health": "32",
        "current_health": "20",
        "armor": "4",
        "equipment": "Lanterna, Corda",
        "ability_name_1": "Luz de Vigia",
        "ability_description_1": "Revela detalhes proximos.",
        "ability_type_1": "utilidade",
        "ability_use_1": "1 vez por sessao",
        "ability_effect_1": "Ajuda a notar marcas escondidas.",
        "ability_cost_1": "Cansaco leve",
        "ability_usage_limit_1": "1",
        "ability_requires_test_1": "true",
        "ability_suggested_test_1": "Percepcao",
        "ability_notes_1": "O mestre decide o detalhe revelado.",
        "ability_name_2": "",
        "ability_type_2": "utilidade",
        "ability_use_2": "livre",
        "ability_name_3": "",
        "ability_type_3": "utilidade",
        "ability_use_3": "livre",
        "history": "Cresceu vigiando travessias perigosas.",
        "personality": "Calma, direta e protetora.",
        "catchphrases": "A ponte sempre cobra.",
        "notes": "Conhece as ruinas do norte.",
    }
    data.update(overrides)
    return data


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


def test_character_new_form_opens_advanced_creator() -> None:
    client, _storage = make_client()

    response = client.get("/characters/new")

    assert response.status_code == 200
    assert "Identidade" in response.text
    assert "Habilidades iniciais" in response.text
    assert "Historia e interpretacao" in response.text


def test_character_preview_displays_built_sheet() -> None:
    client, _storage = make_client()

    response = client.post("/characters/preview", data=advanced_character_form())

    assert response.status_code == 200
    assert "Revisar personagem" in response.text
    assert "Lia da Ponte" in response.text
    assert "Luz de Vigia" in response.text
    assert "Confirmar e salvar" in response.text


def test_character_confirm_creates_character_with_advanced_fields() -> None:
    client, storage = make_client()

    response = client.post("/characters/confirm", data=advanced_character_form(), follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/characters/lia-da-ponte"
    created = get_character(storage, "lia-da-ponte")
    assert created.equipment == ["Lanterna", "Corda"]
    assert created.tags == ["aliada", "investigadora"]
    assert len(created.abilities) == 1
    assert created.abilities[0]["name"] == "Luz de Vigia"
    assert created.abilities[0]["usage_limit"] == 1
    assert created.abilities[0]["remaining_uses"] == 1
    assert created.abilities[0]["requires_test"] is True
    assert "Historia: Cresceu vigiando travessias perigosas." in created.notes


def test_created_character_appears_in_listing() -> None:
    client, _storage = make_client()
    client.post("/characters/confirm", data=advanced_character_form())

    response = client.get("/characters")

    assert response.status_code == 200
    assert "Lia da Ponte" in response.text
    assert "Guardia" in response.text
    assert "20/32" in response.text
    assert "investigadora" in response.text


def test_empty_abilities_are_ignored() -> None:
    client, storage = make_client()

    response = client.post(
        "/characters/confirm",
        data=advanced_character_form(
            name="Nulo",
            ability_name_1="",
            ability_description_1="",
            ability_use_1="livre",
            ability_effect_1="",
            ability_cost_1="",
            ability_usage_limit_1="",
            ability_requires_test_1="",
            ability_suggested_test_1="",
            ability_notes_1="",
        ),
        follow_redirects=False,
    )

    assert response.status_code == 303
    created = get_character(storage, "nulo")
    assert created.abilities == []


def test_character_preview_rejects_empty_name() -> None:
    client, _storage = make_client()

    response = client.post("/characters/preview", data=advanced_character_form(name=""))

    assert response.status_code == 400
    assert "Nome do personagem e obrigatorio." in response.text


def test_character_preview_rejects_current_health_above_maximum() -> None:
    client, _storage = make_client()

    response = client.post("/characters/preview", data=advanced_character_form(max_health="10", current_health="11"))

    assert response.status_code == 400
    assert "Vida atual nao pode ultrapassar a vida maxima." in response.text


def test_character_preview_rejects_negative_ability_usage_limit() -> None:
    client, _storage = make_client()

    response = client.post("/characters/preview", data=advanced_character_form(ability_usage_limit_1="-1"))

    assert response.status_code == 400
    assert "Limite de uso da habilidade 1 nao pode ser negativo." in response.text


def test_character_detail_shows_created_abilities() -> None:
    client, _storage = make_client()
    client.post("/characters/confirm", data=advanced_character_form())

    response = client.get("/characters/lia-da-ponte")

    assert response.status_code == 200
    assert "Luz de Vigia" in response.text
    assert "Efeito:" in response.text
    assert "Percepcao" in response.text
