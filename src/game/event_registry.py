"""Safe bridge from map events to campaign/session history."""

from __future__ import annotations

from collections.abc import Callable

from src.core.campaigns import get_campaign, get_campaign_session, register_campaign_session_event
from src.game.game_context import GameContext
from src.game.maps.events import MapEvent
from src.storage.types import JsonStore


CampaignEventRegistrar = Callable[[JsonStore, str, str, str, str, str], object]


def register_map_event(
    storage: JsonStore,
    context: GameContext,
    event: MapEvent,
    player_position: tuple[int, int],
    registrar: CampaignEventRegistrar = register_campaign_session_event,
) -> bool:
    if not event.registrar_no_historico or not context.has_campaign_session:
        return False

    try:
        campaign = get_campaign(storage, context.campaign_id or "")
        session = get_campaign_session(storage, context.campaign_session_id or "")
        if session.campaign_id.casefold() != campaign.id.casefold():
            raise ValueError("Sessao nao pertence a campanha informada.")

        notes = _build_notes(context, event, player_position)
        registrar(
            storage,
            session.id,
            context.player_name,
            "Evento de mapa",
            event.text,
            notes,
        )
        return True
    except Exception as exc:  # noqa: BLE001 - the game must not crash because persistence failed.
        print(f"[MAGIK Game] Nao foi possivel registrar evento de mapa: {exc}")
        return False


def _build_notes(context: GameContext, event: MapEvent, player_position: tuple[int, int]) -> str:
    x, y = player_position
    parts = [
        "origem=game",
        f"mapa={context.map_name}",
        f"posicao=({x},{y})",
        f"evento={event.id}",
        f"tipo={event.event_type}",
    ]
    if event.tags:
        parts.append(f"tags={','.join(event.tags)}")
    return "; ".join(parts)
