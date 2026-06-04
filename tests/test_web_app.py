from fastapi.testclient import TestClient

from src.core.character import create_character, create_miko_meu, get_character
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
    assert "character-list-card" in response.text
    assert "stat-bar health compact" in response.text


def test_character_detail_shows_character_sheet() -> None:
    client, _storage = make_client()

    response = client.get("/characters/miko-meu")

    assert response.status_code == 200
    assert "Miko Meu" in response.text
    assert "Sombrio" in response.text
    assert "25/25" in response.text
    assert "Armadura/Escudo" in response.text
    assert "stat-bar health" in response.text
    assert "stat-bar armor" in response.text
    assert "Ikisaki" in response.text
    assert "Cajado Sombrio" in response.text
    assert "Switch Sombrio" in response.text
    assert "Editar personagem" in response.text
    assert "Editar habilidades" in response.text


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
    assert "character-list-card" in response.text


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
    assert "ability-card" in response.text
    assert "Efeito:" in response.text
    assert "Percepcao" in response.text
    assert "Historia" in response.text
    assert "Cresceu vigiando travessias perigosas." in response.text
    assert "Personalidade" in response.text


def test_character_detail_handles_empty_equipment_and_abilities() -> None:
    client, storage = make_client()
    create_character(
        storage,
        name="Sem Bagagem",
        character_class="Viajante",
        max_health=12,
        armor=0,
        equipment=[],
        abilities=[],
        tags=[],
        notes=[],
    )

    response = client.get("/characters/sem-bagagem")

    assert response.status_code == 200
    assert "Sem Bagagem" in response.text
    assert "Nenhum equipamento cadastrado ainda." in response.text
    assert "Nenhuma habilidade cadastrada." in response.text
    assert "Nenhum sistema especial cadastrado." in response.text


def test_character_edit_form_opens() -> None:
    client, _storage = make_client()

    response = client.get("/characters/miko-meu/edit")

    assert response.status_code == 200
    assert "Editar personagem" in response.text
    assert "Miko Meu" in response.text
    assert "Status separados por virgula" in response.text


def test_character_edit_updates_character() -> None:
    client, storage = make_client()

    response = client.post(
        "/characters/miko-meu/edit",
        data={
            "name": "Miko Meu Revisado",
            "character_class": "Sombrio",
            "max_health": "30",
            "current_health": "22",
            "armor": "7",
            "tags": "sombrio, revisado",
            "equipment": "Cajado, Corrente de Ferro, Amuleto",
            "status": "alerta",
            "notes": "Observacao revisada.",
        },
        follow_redirects=False,
    )

    assert response.status_code == 303
    updated = get_character(storage, "miko-meu")
    assert updated.name == "Miko Meu Revisado"
    assert updated.max_health == 30
    assert updated.current_health == 22
    assert updated.armor == 7
    assert updated.equipment == ["Cajado", "Corrente de Ferro", "Amuleto"]
    assert updated.status == ["alerta"]
    assert updated.notes == ["Observacao revisada."]


def test_character_edit_rejects_current_health_above_maximum() -> None:
    client, _storage = make_client()

    response = client.post(
        "/characters/miko-meu/edit",
        data={
            "name": "Miko Meu",
            "character_class": "Sombrio",
            "max_health": "10",
            "current_health": "11",
            "armor": "5",
            "tags": "",
            "equipment": "",
            "status": "",
            "notes": "",
        },
    )

    assert response.status_code == 400
    assert "Vida atual nao pode ultrapassar a vida maxima." in response.text


def test_character_equipment_add_and_remove() -> None:
    client, storage = make_client()

    add_response = client.post(
        "/characters/miko-meu/equipment/add",
        data={"equipment_item": "Amuleto"},
        follow_redirects=False,
    )
    assert add_response.status_code == 303
    assert "Amuleto" in get_character(storage, "miko-meu").equipment

    remove_response = client.post(
        "/characters/miko-meu/equipment/remove",
        data={"equipment_item": "Amuleto"},
        follow_redirects=False,
    )
    assert remove_response.status_code == 303
    assert "Amuleto" not in get_character(storage, "miko-meu").equipment


def test_character_status_add_and_remove() -> None:
    client, storage = make_client()

    add_response = client.post(
        "/characters/miko-meu/status/add",
        data={"status_item": "alerta"},
        follow_redirects=False,
    )
    assert add_response.status_code == 303
    assert "alerta" in get_character(storage, "miko-meu").status

    remove_response = client.post(
        "/characters/miko-meu/status/remove",
        data={"status_item": "alerta"},
        follow_redirects=False,
    )
    assert remove_response.status_code == 303
    assert "alerta" not in get_character(storage, "miko-meu").status


def test_character_abilities_page_lists_abilities() -> None:
    client, _storage = make_client()

    response = client.get("/characters/miko-meu/abilities")

    assert response.status_code == 200
    assert "Editar habilidades" in response.text
    assert "Roleta Sombria" in response.text
    assert "Adicionar habilidade" in response.text


def test_character_ability_add_edit_restore_and_remove() -> None:
    client, storage = make_client()

    add_response = client.post(
        "/characters/miko-meu/abilities/add",
        data={
            "name": "Lampejo Frio",
            "description": "Um brilho curto.",
            "type": "magia",
            "use": "limitado",
            "effect": "Ilumina uma pista.",
            "cost": "Foco",
            "usage_limit": "2",
            "remaining_uses": "1",
            "requires_test": "true",
            "suggested_test": "Conhecimento",
            "notes": "Nao decide resultado sozinho.",
        },
        follow_redirects=False,
    )
    assert add_response.status_code == 303
    character = get_character(storage, "miko-meu")
    added = next(ability for ability in character.abilities if ability["id"] == "lampejo-frio")
    assert added["name"] == "Lampejo Frio"
    assert added["remaining_uses"] == 1

    edit_response = client.post(
        "/characters/miko-meu/abilities/lampejo-frio/edit",
        data={
            "name": "Lampejo Gelado",
            "description": "Um brilho curto e frio.",
            "type": "magia",
            "use": "limitado",
            "effect": "Ilumina duas pistas.",
            "cost": "Foco",
            "usage_limit": "2",
            "remaining_uses": "0",
            "requires_test": "",
            "suggested_test": "Conhecimento",
            "notes": "Editada pela web.",
        },
        follow_redirects=False,
    )
    assert edit_response.status_code == 303
    edited = next(ability for ability in get_character(storage, "miko-meu").abilities if ability["id"] == "lampejo-frio")
    assert edited["name"] == "Lampejo Gelado"
    assert edited["remaining_uses"] == 0

    restore_response = client.post(
        "/characters/miko-meu/abilities/lampejo-frio/restore",
        follow_redirects=False,
    )
    assert restore_response.status_code == 303
    restored = next(ability for ability in get_character(storage, "miko-meu").abilities if ability["id"] == "lampejo-frio")
    assert restored["remaining_uses"] == 2

    remove_response = client.post(
        "/characters/miko-meu/abilities/lampejo-frio/remove",
        follow_redirects=False,
    )
    assert remove_response.status_code == 303
    assert all(ability["id"] != "lampejo-frio" for ability in get_character(storage, "miko-meu").abilities)
