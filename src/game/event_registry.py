"""Safe bridge from map events to campaign/session history."""

from __future__ import annotations

from collections.abc import Callable

from src.core.campaigns import get_campaign, get_campaign_session, register_campaign_session_event
from src.game.dialogue import DialogueOption
from src.game.entities.creature import Creature
from src.game.game_context import GameContext
from src.game.maps.events import MapEvent
from src.storage.types import JsonStore


CampaignEventRegistrar = Callable[[JsonStore, str, str, str, str, str], object]


def register_map_event(
    storage: JsonStore,
    context: GameContext,
    event: MapEvent,
    player_position: tuple[int, int],
    selected_option: DialogueOption | None = None,
    registrar: CampaignEventRegistrar = register_campaign_session_event,
) -> bool:
    if not event.registrar_no_historico or not context.has_campaign_session:
        return False

    try:
        campaign = get_campaign(storage, context.campaign_id or "")
        session = get_campaign_session(storage, context.campaign_session_id or "")
        if session.campaign_id.casefold() != campaign.id.casefold():
            raise ValueError("Sessao nao pertence a campanha informada.")

        notes = _build_notes(context, event, player_position, selected_option)
        registrar(
            storage,
            session.id,
            context.player_name,
            "Evento de mapa",
            _build_result(event, selected_option),
            notes,
        )
        return True
    except Exception as exc:  # noqa: BLE001 - the game must not crash because persistence failed.
        print(f"[MAGIK Game] Nao foi possivel registrar evento de mapa: {exc}")
        return False


def register_creature_encounter(
    storage: JsonStore,
    context: GameContext,
    creature: Creature,
    player_position: tuple[int, int],
    selected_option: DialogueOption | None = None,
    registrar: CampaignEventRegistrar = register_campaign_session_event,
) -> bool:
    if not context.has_campaign_session:
        return False

    try:
        campaign = get_campaign(storage, context.campaign_id or "")
        session = get_campaign_session(storage, context.campaign_session_id or "")
        if session.campaign_id.casefold() != campaign.id.casefold():
            raise ValueError("Sessao nao pertence a campanha informada.")

        notes = _build_creature_notes(context, creature, player_position, selected_option)
        registrar(
            storage,
            session.id,
            context.player_name,
            "Encontro com criatura",
            _build_creature_result(creature, selected_option),
            notes,
        )
        return True
    except Exception as exc:  # noqa: BLE001 - the game must not crash because persistence failed.
        print(f"[MAGIK Game] Nao foi possivel registrar encontro com criatura: {exc}")
        return False


def _build_result(event: MapEvent, selected_option: DialogueOption | None) -> str:
    if selected_option is None:
        return event.text
    return f"{event.text} Escolha: {selected_option.text}. Resposta: {selected_option.response}"


def _build_creature_result(creature: Creature, selected_option: DialogueOption | None) -> str:
    base = f"{creature.name} encontrado. Vida: {creature.current_health}/{creature.max_health}. Armadura: {creature.armor}."
    if selected_option is None:
        return base
    return f"{base} Escolha: {selected_option.text}. Resposta: {selected_option.response}"


def _build_notes(
    context: GameContext,
    event: MapEvent,
    player_position: tuple[int, int],
    selected_option: DialogueOption | None,
) -> str:
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
    if selected_option is not None:
        parts.append(f"opcao={selected_option.text}")
        if selected_option.tags:
            parts.append(f"opcao_tags={','.join(selected_option.tags)}")
        if selected_option.event:
            parts.append(f"opcao_evento={selected_option.event}")
    return "; ".join(parts)


def _build_creature_notes(
    context: GameContext,
    creature: Creature,
    player_position: tuple[int, int],
    selected_option: DialogueOption | None,
) -> str:
    x, y = player_position
    parts = [
        "origem=game",
        "tipo=creature_encounter",
        f"mapa={context.map_name}",
        f"posicao=({x},{y})",
        f"criatura={creature.id}",
    ]
    if selected_option is not None:
        parts.append(f"opcao={selected_option.text}")
        if selected_option.tags:
            parts.append(f"opcao_tags={','.join(selected_option.tags)}")
        if selected_option.event:
            parts.append(f"opcao_evento={selected_option.event}")
    return "; ".join(parts)
