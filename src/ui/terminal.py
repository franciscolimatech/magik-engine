"""Simple terminal interface."""

from __future__ import annotations

import json
from pathlib import Path

from src.core.character import create_miko_meu, load_or_create_miko, save_characters
from src.core.dice import roll_dice
from src.core.session import list_events, register_event
from src.storage.json_storage import JSONStorage
from src.systems.ikisaki import use_shadow_roulette
from src.systems.staff import list_staff_spells


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = PROJECT_ROOT / "data"


def run_terminal() -> None:
    storage = JSONStorage(DATA_PATH)
    ensure_initial_data(storage)

    while True:
        print_menu()
        option = input("Escolha uma opcao: ").strip()

        try:
            if option == "1":
                show_miko(storage)
            elif option == "2":
                roll_dice_prompt(storage)
            elif option == "3":
                use_ikisaki_prompt(storage)
            elif option == "4":
                use_staff_prompt(storage)
            elif option == "5":
                register_event_prompt(storage)
            elif option == "6":
                show_history(storage)
            elif option == "0":
                print("Saindo do MAGIK Engine. Boa sessao.")
                break
            else:
                print("Opcao invalida.")
        except (ValueError, RuntimeError) as error:
            print(f"Erro: {error}")


def print_menu() -> None:
    print("\nMAGIK Engine")
    print("1 - Ver ficha do Miko")
    print("2 - Rolar dado")
    print("3 - Usar Roleta Sombria da Ikisaki")
    print("4 - Usar Cajado Sombrio")
    print("5 - Registrar acontecimento")
    print("6 - Ver historico")
    print("0 - Sair")


def ensure_initial_data(storage: JSONStorage) -> None:
    if not storage.path_for("characters.json").exists():
        save_characters(storage, [create_miko_meu()])
    storage.read_json("sessions.json", default=[])
    storage.read_json("world_state.json", default={"notes": [], "flags": {}})


def show_miko(storage: JSONStorage) -> None:
    miko = load_or_create_miko(storage)
    print_json(miko.to_dict())


def roll_dice_prompt(storage: JSONStorage) -> None:
    expression = input("Digite o dado (ex.: 1d20, 2d6): ").strip()
    result = roll_dice(expression)
    print(f"Resultado: {result.total} | Rolagens: {result.rolls}")
    register_event(
        storage,
        character="Miko Meu",
        action=f"Rolou {result.expression}",
        result=f"Total {result.total}; individuais {result.rolls}",
    )


def use_ikisaki_prompt(storage: JSONStorage) -> None:
    miko = load_or_create_miko(storage)
    result = use_shadow_roulette(miko)
    save_characters(storage, [miko])

    print_json(result.to_dict())
    register_event(
        storage,
        character=miko.name,
        action="Usou Roleta Sombria: Dez Elos de Ikisaki",
        result=f"{result.number} - {result.link_name}; preco {result.price_level}",
        notes=result.consequence or "",
    )


def use_staff_prompt(storage: JSONStorage) -> None:
    spells = list_staff_spells()
    print("\nMagias do Cajado Sombrio")
    for index, spell in enumerate(spells, start=1):
        print(f"{index} - {spell.name}")

    selected = input("Escolha uma magia: ").strip()
    if not selected.isdigit() or not 1 <= int(selected) <= len(spells):
        raise ValueError("Escolha uma magia valida.")

    spell = spells[int(selected) - 1]
    print_json(spell.to_dict())
    register_event(
        storage,
        character="Miko Meu",
        action=f"Usou Cajado Sombrio: {spell.name}",
        result=spell.effect,
        notes=f"Sugestao de teste: {spell.suggested_test}",
    )


def register_event_prompt(storage: JSONStorage) -> None:
    character = input("Personagem: ").strip() or "Miko Meu"
    action = input("Acao: ").strip()
    result = input("Resultado: ").strip()
    notes = input("Observacoes: ").strip()
    if not action or not result:
        raise ValueError("Acao e resultado sao obrigatorios.")

    event = register_event(storage, character, action, result, notes)
    print("Acontecimento registrado:")
    print_json(event.to_dict())


def show_history(storage: JSONStorage) -> None:
    events = list_events(storage)
    if not events:
        print("Nenhum acontecimento registrado ainda.")
        return

    for event in events:
        print(f"\n[{event.timestamp}] {event.character}")
        print(f"Acao: {event.action}")
        print(f"Resultado: {event.result}")
        if event.notes:
            print(f"Observacoes: {event.notes}")


def print_json(data: dict) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))
