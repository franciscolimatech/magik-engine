from src.ai.context_builder import build_narrative_context, summarize_narrative_context
from src.core.campaigns import (
    add_campaign_event,
    add_campaign_location,
    add_campaign_npc,
    add_campaign_pending_task,
    add_campaign_player_character,
    add_session_combat,
    add_session_consequence,
    add_session_created_pending_task,
    add_session_event,
    add_session_note,
    add_session_participant,
    create_campaign,
    create_campaign_session,
)
from src.storage.memory import MemoryStorage


def test_build_narrative_context_from_campaign() -> None:
    storage = MemoryStorage()
    campaign = create_campaign(storage, "Ecos de Ikisaki", "Sombras na cidade antiga")
    add_campaign_player_character(storage, campaign.id, "miko-meu")
    add_campaign_npc(storage, campaign.id, "nara")
    add_campaign_location(storage, campaign.id, "Templo das Correntes")
    add_campaign_event(storage, campaign.id, "A primeira corrente cantou.")
    add_campaign_pending_task(storage, campaign.id, "Descobrir quem abriu o selo.")

    context = build_narrative_context(storage, campaign_id=campaign.id, tone="sombrio")

    assert context["campanha"]["nome"] == "Ecos de Ikisaki"
    assert context["local_principal"] == "Templo das Correntes"
    assert context["personagens_participantes"] == ["miko-meu"]
    assert context["npcs_importantes"] == ["nara"]
    assert context["eventos_recentes"] == ["A primeira corrente cantou."]
    assert context["pendencias_abertas"] == ["Descobrir quem abriu o selo."]
    assert context["tom_desejado"] == "sombrio"


def test_build_narrative_context_from_session_includes_participants_events_and_mechanics() -> None:
    storage = MemoryStorage()
    campaign = create_campaign(storage, "Corrente Escura")
    session = create_campaign_session(storage, campaign.id, "A sala sem sol", number=3)
    session.main_location = "Arquivo Submerso"
    from src.core.campaigns import update_campaign_session

    update_campaign_session(storage, session)
    add_session_participant(storage, session.id, "miko-meu")
    add_session_participant(storage, session.id, "akio")
    add_session_event(storage, session.id, "Miko encontrou o simbolo quebrado.")
    add_session_combat(storage, session.id, "combate-sombra-1")
    add_session_consequence(storage, session.id, "O selo enfraqueceu.")
    add_session_created_pending_task(storage, session.id, "Interrogar o guardiao.")
    add_session_note(storage, session.id, "O tom deve ser tenso, mas contido.")

    context = build_narrative_context(
        storage,
        session_id=session.id,
        mechanical_result={"rolagem": "15", "resultado": "sucesso parcial"},
        tone="tenso",
    )

    assert context["sessao"]["titulo"] == "A sala sem sol"
    assert context["sessao"]["numero"] == 3
    assert context["local_principal"] == "Arquivo Submerso"
    assert context["personagens_participantes"] == ["miko-meu", "akio"]
    assert context["eventos_recentes"] == ["Miko encontrou o simbolo quebrado."]
    assert context["criaturas_ou_combate_ativo"] == ["combate-sombra-1"]
    assert context["resultado_mecanico"]["resultado"] == "sucesso parcial"
    assert "Interrogar o guardiao." in context["pendencias_abertas"]


def test_summarize_narrative_context_previews_relevant_data() -> None:
    storage = MemoryStorage()
    campaign = create_campaign(storage, "Ruas de Vidro")
    session = create_campaign_session(storage, campaign.id, "A voz no beco", number=1)
    add_session_participant(storage, session.id, "miko-meu")
    add_session_event(storage, session.id, "Uma figura deixou uma marca na parede.")

    context = build_narrative_context(
        storage,
        session_id=session.id,
        mechanical_result={"resultado": "falha sem dano"},
        tone="misterioso",
    )

    preview = summarize_narrative_context(context)

    assert "Campanha: Ruas de Vidro" in preview
    assert "Sessao 1: A voz no beco" in preview
    assert "Participantes: miko-meu" in preview
    assert "falha sem dano" in preview
