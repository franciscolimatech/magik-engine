"""Formatting helpers for the terminal UI."""

from __future__ import annotations

from src.core.character import Character
from src.core.campaigns import Campaign, CampaignSession
from src.core.creatures import Creature
from src.core.npcs import NPC
from src.core.session import SessionEvent
from src.core.turn_combat import Combat, CombatParticipant


LINE = "-" * 48


def format_title(title: str) -> str:
    return f"\n{LINE}\n{title}\n{LINE}"


def format_character_list(characters: list[Character], allow_skip: bool = False) -> str:
    lines = [format_title("Personagens disponiveis")]
    if allow_skip:
        lines.append("0 - Nenhum/Narrador")
    for index, character in enumerate(characters, start=1):
        lines.append(f"{index} - {character.name} ({character.character_class}) [{character.id}]")
    return "\n".join(lines)


def format_character_sheet(character: Character) -> str:
    lines = [
        format_title(f"Ficha: {character.name}"),
        f"Id: {character.id}",
        f"Classe: {character.character_class}",
        f"Vida: {character.current_health}/{character.max_health}",
        f"Armadura: {character.armor}",
        f"Equipamentos: {_format_list(character.equipment)}",
        f"Habilidades: {_format_abilities(character.abilities)}",
        f"Sistemas especiais: {_format_list(character.special_systems)}",
        f"Status: {_format_list(character.status)}",
        f"Tags: {_format_list(character.tags)}",
        f"Observacoes: {_format_list(character.notes)}",
    ]
    if character.living_weapon:
        lines.append(f"Arma viva: {character.living_weapon}")
    return "\n".join(lines)


def format_history(events: list[SessionEvent], limit: int = 10) -> str:
    if limit <= 0:
        raise ValueError("O limite do historico deve ser maior que zero.")
    if not events:
        return "Nenhum acontecimento registrado ainda."

    selected_events = events[-limit:]
    lines = [format_title(f"Historico da sessao - ultimos {len(selected_events)} eventos")]
    for event in selected_events:
        lines.extend(
            [
                f"[{event.timestamp}] {event.character}",
                f"Acao: {event.action}",
                f"Resultado: {event.result}",
            ]
        )
        if event.notes:
            lines.append(f"Observacoes: {event.notes}")
        if event.campaign_id or event.campaign_session_id:
            lines.append(
                "Vinculos: "
                f"campanha={event.campaign_id or 'nenhuma'}, "
                f"sessao={event.campaign_session_id or 'nenhuma'}"
            )
        lines.append(LINE)
    return "\n".join(lines).rstrip()


def format_manual_test_script() -> str:
    steps = [
        "1 - Ver ficha de um personagem.",
        "2 - Rolar 1d20.",
        "3 - Fazer teste de Vontade.",
        "4 - Usar Roleta Sombria da Ikisaki.",
        "5 - Gerar consequencia narrativa.",
        "6 - Registrar no historico.",
        "7 - Aplicar dano fisico.",
        "8 - Aplicar dano magico.",
        "9 - Curar personagem.",
        "10 - Ver historico.",
    ]
    return "\n".join([format_title("Roteiro de teste manual"), *steps])


def format_creature_list(creatures: list[Creature]) -> str:
    lines = [format_title("Criaturas e inimigos")]
    if not creatures:
        lines.append("Nenhuma criatura cadastrada.")
        return "\n".join(lines)
    for index, creature in enumerate(creatures, start=1):
        lines.append(f"{index} - {creature.name} ({creature.type}) [{creature.id}]")
    return "\n".join(lines)


def format_creature_sheet(creature: Creature) -> str:
    return "\n".join(
        [
            format_title(f"Criatura: {creature.name}"),
            f"Id: {creature.id}",
            f"Tipo: {creature.type}",
            f"Vida: {creature.current_health}/{creature.max_health}",
            f"Armadura: {creature.armor}",
            f"Localizacao: {creature.location or 'nao informada'}",
            f"Nivel de ameaca: {creature.threat_level or 'nao informado'}",
            f"Descricao: {creature.description or 'sem descricao'}",
            f"Habilidades: {_format_abilities(creature.abilities)}",
            f"Status: {_format_list(creature.status)}",
            f"Tags: {_format_list(creature.tags)}",
            f"Observacoes: {_format_list(creature.notes)}",
        ]
    )


def format_npc_list(npcs: list[NPC]) -> str:
    lines = [format_title("NPCs")]
    if not npcs:
        lines.append("Nenhum NPC cadastrado.")
        return "\n".join(lines)
    for index, npc in enumerate(npcs, start=1):
        lines.append(f"{index} - {npc.name} ({npc.role}, {npc.attitude}) [{npc.id}]")
    return "\n".join(lines)


def format_npc_sheet(npc: NPC) -> str:
    return "\n".join(
        [
            format_title(f"NPC: {npc.name}"),
            f"Id: {npc.id}",
            f"Papel: {npc.role}",
            f"Atitude: {npc.attitude}",
            f"Localizacao: {npc.location or 'nao informada'}",
            f"Descricao: {npc.description or 'sem descricao'}",
            f"Rumores: {_format_list(npc.rumors)}",
            f"Status: {_format_list(npc.status)}",
            f"Tags: {_format_list(npc.tags)}",
            f"Observacoes: {_format_list(npc.notes)}",
        ]
    )


def format_combat_list(combats: list[Combat]) -> str:
    lines = [format_title("Combates")]
    if not combats:
        lines.append("Nenhum combate cadastrado.")
        return "\n".join(lines)
    for index, combat in enumerate(combats, start=1):
        lines.append(
            f"{index} - {combat.name} ({combat.status}) [{combat.id}] "
            f"rodada {combat.current_round}, participantes {len(combat.participants)}"
        )
    return "\n".join(lines)


def format_combat_summary(combat: Combat, history_limit: int = 5) -> str:
    lines = [
        format_title(f"Combate: {combat.name}"),
        f"Id: {combat.id}",
        f"Status: {combat.status}",
        f"Rodada atual: {combat.current_round}",
        f"Turno atual: {format_current_participant(combat)}",
        format_title("Ordem de turnos"),
    ]
    if combat.participants:
        lines.extend(format_participant_line(participant) for participant in combat.participants)
    else:
        lines.append("Nenhum participante.")

    lines.append(format_title(f"Historico do combate - ultimos {min(history_limit, len(combat.combat_history))} eventos"))
    if combat.combat_history:
        lines.extend(combat.combat_history[-history_limit:])
    else:
        lines.append("Nenhum evento de combate registrado.")
    return "\n".join(lines)


def format_current_participant(combat: Combat) -> str:
    if not combat.participants:
        return "nenhum participante"
    if combat.current_turn >= len(combat.participants):
        return "turno fora da lista"
    participant = combat.participants[combat.current_turn]
    return format_participant_line(participant)


def format_participant_line(participant: CombatParticipant) -> str:
    alive = "vivo" if participant.is_alive and participant.current_health > 0 else "fora de combate"
    status = _format_list(participant.status)
    return (
        f"{participant.name} [{participant.id}] - {participant.type}, "
        f"vida {participant.current_health}/{participant.max_health}, armadura {participant.armor}, "
        f"iniciativa {participant.initiative}, {alive}, status: {status}"
    )


def format_campaign_list(campaigns: list[Campaign]) -> str:
    lines = [format_title("Campanhas")]
    if not campaigns:
        lines.append("Nenhuma campanha cadastrada.")
        return "\n".join(lines)
    for index, campaign in enumerate(campaigns, start=1):
        lines.append(f"{index} - {campaign.name} ({campaign.status}) [{campaign.id}]")
    return "\n".join(lines)


def format_campaign_summary(campaign: Campaign) -> str:
    return "\n".join(
        [
            format_title(f"Campanha: {campaign.name}"),
            f"Id: {campaign.id}",
            f"Status: {campaign.status}",
            f"Descricao: {campaign.description or 'sem descricao'}",
            f"Personagens: {_format_list(campaign.player_characters)}",
            f"NPCs importantes: {_format_list(campaign.important_npcs)}",
            f"Locais importantes: {_format_list(campaign.important_locations)}",
            f"Eventos importantes: {_format_list(campaign.important_events)}",
            f"Pendencias abertas: {_format_list(campaign.pending_tasks)}",
            f"Pendencias resolvidas: {_format_list(campaign.resolved_tasks)}",
            f"Criado em: {campaign.created_at}",
            f"Atualizado em: {campaign.updated_at}",
        ]
    )


def format_campaign_session_list(sessions: list[CampaignSession]) -> str:
    lines = [format_title("Sessoes da campanha")]
    if not sessions:
        lines.append("Nenhuma sessao cadastrada.")
        return "\n".join(lines)
    for session in sorted(sessions, key=lambda item: item.number):
        lines.append(f"{session.number} - {session.title} ({session.status}) [{session.id}]")
    return "\n".join(lines)


def format_campaign_session_summary(session: CampaignSession) -> str:
    return "\n".join(
        [
            format_title(f"Sessao {session.number}: {session.title}"),
            f"Id: {session.id}",
            f"Campanha: {session.campaign_id}",
            f"Status: {session.status}",
            f"Data: {session.date}",
            f"Resumo: {session.summary or 'sem resumo'}",
            f"Participantes: {_format_list(session.participants)}",
            f"Local principal: {session.main_location or 'nao informado'}",
            f"Eventos: {_format_list(session.events)}",
            f"Combates: {_format_list(session.combats)}",
            f"Recompensas: {_format_list(session.rewards)}",
            f"Consequencias: {_format_list(session.consequences)}",
            f"Pendencias criadas: {_format_list(session.created_pending_tasks)}",
            f"Pendencias resolvidas: {_format_list(session.resolved_pending_tasks)}",
            f"Observacoes: {_format_list(session.notes)}",
        ]
    )


def _format_list(values: list[str]) -> str:
    return ", ".join(values) if values else "nenhum"


def _format_abilities(abilities: list[dict]) -> str:
    if not abilities:
        return "nenhuma"
    names = []
    for ability in abilities:
        uses = ability.get("remaining_uses")
        limit = ability.get("usage_limit")
        suffix = f" ({uses}/{limit})" if uses is not None and limit is not None else ""
        names.append(f"{ability.get('name', ability.get('id', 'habilidade sem nome'))}{suffix}")
    return ", ".join(names)
