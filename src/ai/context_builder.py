"""Narrative context builder for auxiliary AI prompts."""

from __future__ import annotations

from typing import Any

from src.core.campaigns import (
    Campaign,
    CampaignSession,
    get_campaign,
    get_campaign_session,
)
from src.storage.types import JsonStore


AI_LIMITS = [
    "Python decide regras, dados, vida, dano, armadura, rolagens, consequencias e estado.",
    "A IA apenas narra, sugere texto e melhora descricoes.",
    "Nao inventar dano, morte, mudanca permanente, regra ou resultado de dado.",
    "O mestre aprova, registra ou descarta o texto.",
]


def build_narrative_context(
    storage: JsonStore,
    campaign_id: str | None = None,
    session_id: str | None = None,
    *,
    mechanical_result: dict[str, Any] | None = None,
    tone: str | None = None,
    local: str | None = None,
    action: str | None = None,
    observations: str | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a compact, safe context for narration without mutating game state."""

    campaign: Campaign | None = None
    session: CampaignSession | None = None

    if session_id:
        session = get_campaign_session(storage, session_id)
        campaign = get_campaign(storage, session.campaign_id)
    elif campaign_id:
        campaign = get_campaign(storage, campaign_id)

    selected_local = _first_text(local, session.main_location if session else None)
    if not selected_local and campaign and campaign.important_locations:
        selected_local = campaign.important_locations[0]

    participants = _unique(
        (session.participants if session else [])
        + (campaign.player_characters if campaign else [])
    )
    recent_events = _last(session.events if session else [], 5)
    if not recent_events and campaign:
        recent_events = _last(campaign.important_events, 5)

    pending_tasks = list(campaign.pending_tasks if campaign else [])
    if session:
        pending_tasks.extend(session.created_pending_tasks)

    context: dict[str, Any] = {
        "campanha": _campaign_context(campaign),
        "sessao": _session_context(session),
        "local_principal": selected_local,
        "personagens_participantes": participants,
        "npcs_importantes": list(campaign.important_npcs if campaign else []),
        "criaturas_ou_combate_ativo": list(session.combats if session else []),
        "eventos_recentes": recent_events,
        "pendencias_abertas": _unique(pending_tasks),
        "pendencias_resolvidas": _unique(
            (campaign.resolved_tasks if campaign else [])
            + (session.resolved_pending_tasks if session else [])
        ),
        "resultado_mecanico": mechanical_result or {},
        "acao": action or "",
        "tom_desejado": tone or "",
        "tom": tone or "",
        "observacoes_do_mestre": observations or "",
        "limites_da_ia": list(AI_LIMITS),
    }
    if extra:
        context.update(_without_empty(extra))
    return _without_empty(context)


def summarize_narrative_context(context: dict[str, Any]) -> str:
    """Return a short terminal preview of the context sent to the AI."""

    lines = ["Contexto usado pela IA:"]
    campaign = context.get("campanha") if isinstance(context.get("campanha"), dict) else {}
    session = context.get("sessao") if isinstance(context.get("sessao"), dict) else {}
    if campaign and campaign.get("nome"):
        lines.append(f"- Campanha: {campaign['nome']}")
    if session and session.get("titulo"):
        number = session.get("numero")
        prefix = f"Sessao {number}: " if number else ""
        lines.append(f"- Sessao: {prefix}{session['titulo']}")
    if context.get("local_principal"):
        lines.append(f"- Local: {context['local_principal']}")
    _append_list(lines, "Participantes", context.get("personagens_participantes"))
    _append_list(lines, "NPCs importantes", context.get("npcs_importantes"))
    _append_list(lines, "Eventos recentes", context.get("eventos_recentes"))
    _append_list(lines, "Pendencias abertas", context.get("pendencias_abertas"))
    result = context.get("resultado_mecanico")
    if isinstance(result, dict) and result:
        result_text = "; ".join(f"{key}: {value}" for key, value in result.items() if value not in (None, ""))
        if result_text:
            lines.append(f"- Resultado mecanico: {result_text}")
    if context.get("tom_desejado") or context.get("tom"):
        lines.append(f"- Tom: {context.get('tom_desejado') or context.get('tom')}")
    return "\n".join(lines)


def _campaign_context(campaign: Campaign | None) -> dict[str, Any]:
    if campaign is None:
        return {}
    return _without_empty(
        {
            "id": campaign.id,
            "nome": campaign.name,
            "descricao": campaign.description,
            "status": campaign.status,
            "personagens_participantes": campaign.player_characters,
            "npcs_importantes": campaign.important_npcs,
            "locais_importantes": campaign.important_locations,
            "eventos_importantes": _last(campaign.important_events, 8),
            "pendencias_abertas": campaign.pending_tasks,
            "pendencias_resolvidas": campaign.resolved_tasks,
        }
    )


def _session_context(session: CampaignSession | None) -> dict[str, Any]:
    if session is None:
        return {}
    return _without_empty(
        {
            "id": session.id,
            "campanha_id": session.campaign_id,
            "numero": session.number,
            "titulo": session.title,
            "resumo": session.summary,
            "status": session.status,
            "local_principal": session.main_location,
            "participantes": session.participants,
            "eventos": _last(session.events, 10),
            "combates": session.combats,
            "recompensas": session.rewards,
            "consequencias": session.consequences,
            "pendencias_criadas": session.created_pending_tasks,
            "pendencias_resolvidas": session.resolved_pending_tasks,
            "observacoes": session.notes,
        }
    )


def _append_list(lines: list[str], label: str, values: Any) -> None:
    if not isinstance(values, list) or not values:
        return
    preview = ", ".join(str(value) for value in values[:4])
    suffix = "..." if len(values) > 4 else ""
    lines.append(f"- {label}: {preview}{suffix}")


def _without_empty(data: dict[str, Any]) -> dict[str, Any]:
    cleaned: dict[str, Any] = {}
    for key, value in data.items():
        if value in (None, "", [], {}):
            continue
        cleaned[key] = value
    return cleaned


def _first_text(*values: str | None) -> str:
    for value in values:
        if value and value.strip():
            return value.strip()
    return ""


def _last(values: list[str], limit: int) -> list[str]:
    return list(values[-limit:])


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        cleaned = str(value).strip()
        if not cleaned or cleaned in seen:
            continue
        seen.add(cleaned)
        result.append(cleaned)
    return result
