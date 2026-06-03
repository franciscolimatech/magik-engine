"""Formatting helpers for the terminal UI."""

from __future__ import annotations

from src.core.character import Character
from src.core.session import SessionEvent


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


def _format_list(values: list[str]) -> str:
    return ", ".join(values) if values else "nenhum"


def _format_abilities(abilities: list[dict]) -> str:
    if not abilities:
        return "nenhuma"
    names = [str(ability.get("name", ability.get("id", "habilidade sem nome"))) for ability in abilities]
    return ", ".join(names)
