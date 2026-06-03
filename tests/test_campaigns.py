import pytest

from src.core.campaigns import (
    add_campaign_event,
    add_campaign_location,
    add_campaign_npc,
    add_campaign_pending_task,
    add_campaign_player_character,
    add_session_combat,
    add_session_consequence,
    add_session_event,
    add_session_participant,
    add_session_reward,
    create_campaign,
    create_campaign_session,
    finish_campaign,
    finish_campaign_session,
    get_campaign,
    list_campaign_sessions,
    list_campaigns,
    pause_campaign,
    register_campaign_session_event,
    remove_campaign_player_character,
    resolve_campaign_pending_task,
    start_campaign_session,
    update_session_summary,
)
from src.core.session import list_events
from src.storage.memory import MemoryStorage
from src.ui.formatting import format_campaign_session_summary, format_history


def make_storage() -> MemoryStorage:
    return MemoryStorage(
        {
            "campaigns.json": {"campaigns": []},
            "campaign_sessions.json": {"campaign_sessions": []},
            "sessions.json": [],
        }
    )


def test_create_campaign() -> None:
    storage = make_storage()

    campaign = create_campaign(storage, "Sombras de Pedralume", "Campanha teste.")

    assert campaign.id == "sombras-de-pedralume"
    assert campaign.status == "ativa"


def test_list_campaigns() -> None:
    storage = make_storage()
    create_campaign(storage, "Sombras")

    assert [campaign.name for campaign in list_campaigns(storage)] == ["Sombras"]


def test_get_existing_campaign() -> None:
    storage = make_storage()
    create_campaign(storage, "Sombras")

    assert get_campaign(storage, "sombras").name == "Sombras"


def test_get_missing_campaign_raises_error() -> None:
    storage = make_storage()

    with pytest.raises(ValueError):
        get_campaign(storage, "nao-existe")


def test_add_and_remove_player_character() -> None:
    storage = make_storage()
    campaign = create_campaign(storage, "Sombras")

    with_character = add_campaign_player_character(storage, campaign.id, "miko-meu")
    without_character = remove_campaign_player_character(storage, campaign.id, "miko-meu")

    assert with_character.player_characters == ["miko-meu"]
    assert without_character.player_characters == []


def test_add_campaign_npc_location_and_event() -> None:
    storage = make_storage()
    campaign = create_campaign(storage, "Sombras")

    campaign = add_campaign_npc(storage, campaign.id, "nara")
    campaign = add_campaign_location(storage, campaign.id, "Estrada do Viajante")
    campaign = add_campaign_event(storage, campaign.id, "O grupo encontrou uma pista.")

    assert campaign.important_npcs == ["nara"]
    assert campaign.important_locations == ["Estrada do Viajante"]
    assert campaign.important_events == ["O grupo encontrou uma pista."]


def test_add_and_resolve_pending_task() -> None:
    storage = make_storage()
    campaign = create_campaign(storage, "Sombras")

    with_task = add_campaign_pending_task(storage, campaign.id, "Encontrar a chave.")
    resolved = resolve_campaign_pending_task(storage, campaign.id, "Encontrar a chave.")

    assert with_task.pending_tasks == ["Encontrar a chave."]
    assert resolved.pending_tasks == []
    assert resolved.resolved_tasks == ["Encontrar a chave."]


def test_pause_and_finish_campaign() -> None:
    storage = make_storage()
    campaign = create_campaign(storage, "Sombras")

    paused = pause_campaign(storage, campaign.id)
    finished = finish_campaign(storage, campaign.id)

    assert paused.status == "pausada"
    assert finished.status == "finalizada"


def test_create_campaign_session() -> None:
    storage = make_storage()
    campaign = create_campaign(storage, "Sombras")

    session = create_campaign_session(storage, campaign.id, "Inicio")

    assert session.campaign_id == campaign.id
    assert session.number == 1


def test_list_campaign_sessions() -> None:
    storage = make_storage()
    campaign = create_campaign(storage, "Sombras")
    create_campaign_session(storage, campaign.id, "Inicio")

    assert [session.title for session in list_campaign_sessions(storage, campaign.id)] == ["Inicio"]


def test_start_and_finish_campaign_session() -> None:
    storage = make_storage()
    campaign = create_campaign(storage, "Sombras")
    session = create_campaign_session(storage, campaign.id, "Inicio")

    started = start_campaign_session(storage, session.id)
    finished = finish_campaign_session(storage, session.id)

    assert started.status == "em_andamento"
    assert finished.status == "finalizada"


def test_add_event_to_session() -> None:
    storage = make_storage()
    campaign = create_campaign(storage, "Sombras")
    session = create_campaign_session(storage, campaign.id, "Inicio")

    updated = add_session_event(storage, session.id, "A porta abriu.")

    assert updated.events == ["A porta abriu."]


def test_associate_combat_to_session() -> None:
    storage = make_storage()
    campaign = create_campaign(storage, "Sombras")
    session = create_campaign_session(storage, campaign.id, "Inicio")

    updated = add_session_combat(storage, session.id, "emboscada")

    assert updated.combats == ["emboscada"]
    assert "Combates: emboscada" in format_campaign_session_summary(updated)


def test_add_participant_to_session() -> None:
    storage = make_storage()
    campaign = create_campaign(storage, "Sombras")
    session = create_campaign_session(storage, campaign.id, "Inicio")

    updated = add_session_participant(storage, session.id, "miko-meu")

    assert updated.participants == ["miko-meu"]


def test_register_general_history_event_linked_to_campaign_session() -> None:
    storage = make_storage()
    campaign = create_campaign(storage, "Sombras")
    session = create_campaign_session(storage, campaign.id, "Inicio")

    event = register_campaign_session_event(
        storage,
        session.id,
        character="Miko Meu",
        action="Investigou",
        result="Encontrou um sinal.",
    )
    events = list_events(storage)

    assert event.campaign_id == campaign.id
    assert event.campaign_session_id == session.id
    assert events[0].campaign_id == campaign.id
    assert "sessao=" in format_history(events)
    assert "Miko Meu: Investigou - Encontrou um sinal." in get_session_events(storage, session.id)


def test_add_reward_and_consequence() -> None:
    storage = make_storage()
    campaign = create_campaign(storage, "Sombras")
    session = create_campaign_session(storage, campaign.id, "Inicio")

    session = add_session_reward(storage, session.id, "10 Pedralumes Brutas")
    session = add_session_consequence(storage, session.id, "Um inimigo escapou.")

    assert session.rewards == ["10 Pedralumes Brutas"]
    assert session.consequences == ["Um inimigo escapou."]


def test_update_session_summary() -> None:
    storage = make_storage()
    campaign = create_campaign(storage, "Sombras")
    session = create_campaign_session(storage, campaign.id, "Inicio")

    updated = update_session_summary(storage, session.id, "Resumo atualizado.")

    assert updated.summary == "Resumo atualizado."


def get_session_events(storage: MemoryStorage, session_id: str) -> list[str]:
    from src.core.campaigns import get_campaign_session

    return get_campaign_session(storage, session_id).events
