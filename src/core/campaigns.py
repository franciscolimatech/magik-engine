"""Campaign and organized campaign session management."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
import re
from typing import Any

from src.storage.types import JsonStore


CAMPAIGN_STATUSES = {"ativa", "pausada", "finalizada"}
SESSION_STATUSES = {"planejada", "em_andamento", "finalizada"}


@dataclass
class Campaign:
    id: str
    name: str
    description: str = ""
    status: str = "ativa"
    player_characters: list[str] = field(default_factory=list)
    important_npcs: list[str] = field(default_factory=list)
    important_locations: list[str] = field(default_factory=list)
    important_events: list[str] = field(default_factory=list)
    pending_tasks: list[str] = field(default_factory=list)
    resolved_tasks: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: _now())
    updated_at: str = field(default_factory=lambda: _now())

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Campaign":
        campaign = cls(
            id=str(data["id"]),
            name=str(data["name"]),
            description=str(data.get("description", "")),
            status=str(data.get("status", "ativa")),
            player_characters=list(data.get("player_characters", data.get("personagens_participantes", []))),
            important_npcs=list(data.get("important_npcs", data.get("npcs_importantes", []))),
            important_locations=list(data.get("important_locations", data.get("locais_importantes", []))),
            important_events=list(data.get("important_events", data.get("eventos_importantes", []))),
            pending_tasks=list(data.get("pending_tasks", data.get("pendencias", []))),
            resolved_tasks=list(data.get("resolved_tasks", [])),
            created_at=str(data.get("created_at", data.get("criado_em", _now()))),
            updated_at=str(data.get("updated_at", data.get("atualizado_em", _now()))),
        )
        validate_campaign(campaign)
        return campaign


@dataclass
class CampaignSession:
    id: str
    campaign_id: str
    number: int
    title: str
    summary: str = ""
    date: str = field(default_factory=lambda: _now())
    participants: list[str] = field(default_factory=list)
    main_location: str | None = None
    events: list[str] = field(default_factory=list)
    combats: list[str] = field(default_factory=list)
    rewards: list[str] = field(default_factory=list)
    consequences: list[str] = field(default_factory=list)
    created_pending_tasks: list[str] = field(default_factory=list)
    resolved_pending_tasks: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    status: str = "planejada"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CampaignSession":
        session = cls(
            id=str(data["id"]),
            campaign_id=str(data["campaign_id"]),
            number=int(data["number"]),
            title=str(data["title"]),
            summary=str(data.get("summary", data.get("resumo", ""))),
            date=str(data.get("date", data.get("data", _now()))),
            participants=list(data.get("participants", data.get("participantes", []))),
            main_location=data.get("main_location", data.get("local_principal")),
            events=list(data.get("events", data.get("eventos", []))),
            combats=list(data.get("combats", data.get("combates", []))),
            rewards=list(data.get("rewards", data.get("recompensas", []))),
            consequences=list(data.get("consequences", data.get("consequencias", []))),
            created_pending_tasks=list(data.get("created_pending_tasks", data.get("pendencias_criadas", []))),
            resolved_pending_tasks=list(data.get("resolved_pending_tasks", data.get("pendencias_resolvidas", []))),
            notes=list(data.get("notes", data.get("observacoes", []))),
            status=str(data.get("status", "planejada")),
        )
        validate_campaign_session(session)
        return session


def default_campaign_data() -> dict[str, Any]:
    return {"campaigns": []}


def default_campaign_session_data() -> dict[str, Any]:
    return {"campaign_sessions": []}


def list_campaigns(storage: JsonStore) -> list[Campaign]:
    data = storage.read_json("campaigns.json", default=default_campaign_data())
    items = _read_collection(data, "campaigns", "campaigns.json")
    return [Campaign.from_dict(item) for item in items]


def save_campaigns(storage: JsonStore, campaigns: list[Campaign]) -> None:
    _ensure_unique_ids(campaigns, "campanha")
    storage.write_json("campaigns.json", {"campaigns": [campaign.to_dict() for campaign in campaigns]})


def create_campaign(storage: JsonStore, name: str, description: str = "", campaign_id: str | None = None) -> Campaign:
    if not name.strip():
        raise ValueError("Nome da campanha e obrigatorio.")
    campaigns = list_campaigns(storage)
    new_id = _resolve_new_id(campaigns, campaign_id or name, explicit=campaign_id is not None, label="campanha")
    campaign = Campaign(id=new_id, name=name.strip(), description=description.strip())
    campaigns.append(campaign)
    save_campaigns(storage, campaigns)
    return campaign


def get_campaign(storage: JsonStore, campaign_id: str) -> Campaign:
    normalized = campaign_id.strip().casefold()
    for campaign in list_campaigns(storage):
        if campaign.id.casefold() == normalized:
            return campaign
    raise ValueError(f"Campanha nao encontrada: {campaign_id}.")


def update_campaign(storage: JsonStore, campaign: Campaign) -> Campaign:
    campaign.updated_at = _now()
    validate_campaign(campaign)
    campaigns = list_campaigns(storage)
    for index, current in enumerate(campaigns):
        if current.id.casefold() == campaign.id.casefold():
            campaigns[index] = campaign
            save_campaigns(storage, campaigns)
            return campaign
    raise ValueError(f"Campanha nao encontrada: {campaign.id}.")


def pause_campaign(storage: JsonStore, campaign_id: str) -> Campaign:
    campaign = get_campaign(storage, campaign_id)
    campaign.status = "pausada"
    return update_campaign(storage, campaign)


def finish_campaign(storage: JsonStore, campaign_id: str) -> Campaign:
    campaign = get_campaign(storage, campaign_id)
    campaign.status = "finalizada"
    return update_campaign(storage, campaign)


def add_campaign_player_character(storage: JsonStore, campaign_id: str, character_id: str) -> Campaign:
    campaign = get_campaign(storage, campaign_id)
    _add_unique(campaign.player_characters, character_id)
    return update_campaign(storage, campaign)


def remove_campaign_player_character(storage: JsonStore, campaign_id: str, character_id: str) -> Campaign:
    campaign = get_campaign(storage, campaign_id)
    _remove_existing(campaign.player_characters, character_id, "personagem")
    return update_campaign(storage, campaign)


def add_campaign_npc(storage: JsonStore, campaign_id: str, npc_id: str) -> Campaign:
    campaign = get_campaign(storage, campaign_id)
    _add_unique(campaign.important_npcs, npc_id)
    return update_campaign(storage, campaign)


def add_campaign_location(storage: JsonStore, campaign_id: str, location: str) -> Campaign:
    campaign = get_campaign(storage, campaign_id)
    _add_unique(campaign.important_locations, _required_text(location, "local"))
    return update_campaign(storage, campaign)


def add_campaign_event(storage: JsonStore, campaign_id: str, event: str) -> Campaign:
    campaign = get_campaign(storage, campaign_id)
    campaign.important_events.append(_required_text(event, "evento"))
    return update_campaign(storage, campaign)


def add_campaign_pending_task(storage: JsonStore, campaign_id: str, task: str) -> Campaign:
    campaign = get_campaign(storage, campaign_id)
    campaign.pending_tasks.append(_required_text(task, "pendencia"))
    return update_campaign(storage, campaign)


def resolve_campaign_pending_task(storage: JsonStore, campaign_id: str, task: str) -> Campaign:
    campaign = get_campaign(storage, campaign_id)
    cleaned = _required_text(task, "pendencia")
    _remove_existing(campaign.pending_tasks, cleaned, "pendencia")
    campaign.resolved_tasks.append(cleaned)
    return update_campaign(storage, campaign)


def list_campaign_sessions(storage: JsonStore, campaign_id: str | None = None) -> list[CampaignSession]:
    data = storage.read_json("campaign_sessions.json", default=default_campaign_session_data())
    items = _read_collection(data, "campaign_sessions", "campaign_sessions.json")
    sessions = [CampaignSession.from_dict(item) for item in items]
    if campaign_id is None:
        return sessions
    normalized = campaign_id.strip().casefold()
    return [session for session in sessions if session.campaign_id.casefold() == normalized]


def save_campaign_sessions(storage: JsonStore, sessions: list[CampaignSession]) -> None:
    _ensure_unique_ids(sessions, "sessao")
    storage.write_json("campaign_sessions.json", {"campaign_sessions": [session.to_dict() for session in sessions]})


def create_campaign_session(
    storage: JsonStore,
    campaign_id: str,
    title: str,
    number: int | None = None,
    summary: str = "",
) -> CampaignSession:
    get_campaign(storage, campaign_id)
    if not title.strip():
        raise ValueError("Titulo da sessao e obrigatorio.")
    sessions = list_campaign_sessions(storage)
    campaign_sessions = [session for session in sessions if session.campaign_id == campaign_id]
    session_number = number if number is not None else len(campaign_sessions) + 1
    if session_number <= 0:
        raise ValueError("Numero da sessao deve ser maior que zero.")
    session_id = _resolve_new_id(sessions, f"{campaign_id}-sessao-{session_number}", explicit=False, label="sessao")
    session = CampaignSession(
        id=session_id,
        campaign_id=campaign_id,
        number=session_number,
        title=title.strip(),
        summary=summary.strip(),
    )
    sessions.append(session)
    save_campaign_sessions(storage, sessions)
    return session


def get_campaign_session(storage: JsonStore, session_id: str) -> CampaignSession:
    normalized = session_id.strip().casefold()
    for session in list_campaign_sessions(storage):
        if session.id.casefold() == normalized:
            return session
    raise ValueError(f"Sessao de campanha nao encontrada: {session_id}.")


def update_campaign_session(storage: JsonStore, session: CampaignSession) -> CampaignSession:
    validate_campaign_session(session)
    sessions = list_campaign_sessions(storage)
    for index, current in enumerate(sessions):
        if current.id.casefold() == session.id.casefold():
            sessions[index] = session
            save_campaign_sessions(storage, sessions)
            return session
    raise ValueError(f"Sessao de campanha nao encontrada: {session.id}.")


def start_campaign_session(storage: JsonStore, session_id: str) -> CampaignSession:
    session = get_campaign_session(storage, session_id)
    session.status = "em_andamento"
    return update_campaign_session(storage, session)


def finish_campaign_session(storage: JsonStore, session_id: str) -> CampaignSession:
    session = get_campaign_session(storage, session_id)
    session.status = "finalizada"
    return update_campaign_session(storage, session)


def add_session_event(storage: JsonStore, session_id: str, event: str) -> CampaignSession:
    session = get_campaign_session(storage, session_id)
    session.events.append(_required_text(event, "evento"))
    return update_campaign_session(storage, session)


def add_session_combat(storage: JsonStore, session_id: str, combat_id: str) -> CampaignSession:
    session = get_campaign_session(storage, session_id)
    _add_unique(session.combats, combat_id)
    return update_campaign_session(storage, session)


def add_session_reward(storage: JsonStore, session_id: str, reward: str) -> CampaignSession:
    session = get_campaign_session(storage, session_id)
    session.rewards.append(_required_text(reward, "recompensa"))
    return update_campaign_session(storage, session)


def add_session_consequence(storage: JsonStore, session_id: str, consequence: str) -> CampaignSession:
    session = get_campaign_session(storage, session_id)
    session.consequences.append(_required_text(consequence, "consequencia"))
    return update_campaign_session(storage, session)


def add_session_created_pending_task(storage: JsonStore, session_id: str, task: str) -> CampaignSession:
    session = get_campaign_session(storage, session_id)
    session.created_pending_tasks.append(_required_text(task, "pendencia criada"))
    return update_campaign_session(storage, session)


def add_session_resolved_pending_task(storage: JsonStore, session_id: str, task: str) -> CampaignSession:
    session = get_campaign_session(storage, session_id)
    session.resolved_pending_tasks.append(_required_text(task, "pendencia resolvida"))
    return update_campaign_session(storage, session)


def add_session_note(storage: JsonStore, session_id: str, note: str) -> CampaignSession:
    session = get_campaign_session(storage, session_id)
    session.notes.append(_required_text(note, "observacao"))
    return update_campaign_session(storage, session)


def update_session_summary(storage: JsonStore, session_id: str, summary: str) -> CampaignSession:
    session = get_campaign_session(storage, session_id)
    session.summary = summary.strip()
    return update_campaign_session(storage, session)


def validate_campaign(campaign: Campaign) -> None:
    if not campaign.id.strip():
        raise ValueError("Id da campanha e obrigatorio.")
    if not campaign.name.strip():
        raise ValueError("Nome da campanha e obrigatorio.")
    if campaign.status not in CAMPAIGN_STATUSES:
        raise ValueError("Status de campanha invalido.")


def validate_campaign_session(session: CampaignSession) -> None:
    if not session.id.strip():
        raise ValueError("Id da sessao e obrigatorio.")
    if not session.campaign_id.strip():
        raise ValueError("Campanha da sessao e obrigatoria.")
    if session.number <= 0:
        raise ValueError("Numero da sessao deve ser maior que zero.")
    if not session.title.strip():
        raise ValueError("Titulo da sessao e obrigatorio.")
    if session.status not in SESSION_STATUSES:
        raise ValueError("Status de sessao invalido.")


def _read_collection(data: Any, key: str, filename: str) -> list[dict[str, Any]]:
    if isinstance(data, dict):
        items = data.get(key, [])
    elif isinstance(data, list):
        items = data
    else:
        raise ValueError(f"{filename} deve conter uma lista ou um objeto com a chave '{key}'.")
    if not isinstance(items, list):
        raise ValueError(f"A chave '{key}' deve conter uma lista.")
    if not all(isinstance(item, dict) for item in items):
        raise ValueError(f"Cada item em {filename} deve ser um objeto JSON.")
    return items


def _add_unique(values: list[str], value: str) -> None:
    cleaned = _required_text(value, "valor")
    if cleaned not in values:
        values.append(cleaned)


def _remove_existing(values: list[str], value: str, label: str) -> None:
    cleaned = _required_text(value, label)
    try:
        values.remove(cleaned)
    except ValueError as exc:
        raise ValueError(f"{label.capitalize()} nao encontrado: {cleaned}.") from exc


def _resolve_new_id(items: list[Any], value: str, explicit: bool, label: str) -> str:
    candidate = _slug(value)
    existing = {item.id.casefold() for item in items}
    if candidate.casefold() not in existing:
        return candidate
    if explicit:
        raise ValueError(f"Id de {label} duplicado: {candidate}.")
    suffix = 2
    while f"{candidate}-{suffix}".casefold() in existing:
        suffix += 1
    return f"{candidate}-{suffix}"


def _ensure_unique_ids(items: list[Any], label: str) -> None:
    seen: set[str] = set()
    for item in items:
        normalized = item.id.casefold()
        if normalized in seen:
            raise ValueError(f"Id de {label} duplicado: {item.id}.")
        seen.add(normalized)


def _required_text(value: str, field_name: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise ValueError(f"O campo {field_name} e obrigatorio.")
    return cleaned


def _slug(value: str) -> str:
    import unicodedata

    normalized = unicodedata.normalize("NFKD", value.strip().casefold())
    ascii_only = "".join(character for character in normalized if not unicodedata.combining(character))
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_only).strip("-")
    return slug or "item"


def _now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")
