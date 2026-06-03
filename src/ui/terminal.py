"""Simple terminal interface."""

from __future__ import annotations

import json
from pathlib import Path

from src.core.combat import apply_physical_damage, roll_damage
from src.core.character import (
    add_equipment,
    add_note,
    create_character,
    create_miko_meu,
    get_character,
    list_characters,
    load_or_create_miko,
    remove_equipment,
    save_character,
    save_characters,
    update_character,
    update_character_armor,
    update_character_health,
)
from src.core.currency import PedralumeMoney
from src.core.dice import roll_dice
from src.core.magic import apply_healing, apply_magic_damage
from src.core.session import list_events, register_event
from src.core.skill_tests import list_test_types, perform_skill_test
from src.core.world import default_world_state, list_locations
from src.storage.json_storage import JSONStorage
from src.systems.ikisaki import use_shadow_roulette
from src.systems.narrative import (
    generate_curse_omen,
    generate_ikisaki_line,
    generate_narrative_consequence,
    generate_random_event,
    generate_rumor,
    list_location_types,
    list_consequence_price_levels,
    list_ikisaki_line_categories,
    list_tones,
    maybe_record_narrative_result,
    narrate_ikisaki_roulette,
    record_narrative_result,
)
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
            elif option == "7":
                perform_skill_test_prompt(storage)
            elif option == "8":
                simulate_physical_damage_prompt(storage)
            elif option == "9":
                simulate_magical_damage_prompt(storage)
            elif option == "10":
                organize_pedralume_prompt()
            elif option == "11":
                show_world_locations(storage)
            elif option == "12":
                generate_ikisaki_line_prompt(storage)
            elif option == "13":
                generate_narrative_consequence_prompt(storage)
            elif option == "14":
                generate_random_event_prompt(storage)
            elif option == "15":
                generate_rumor_prompt(storage)
            elif option == "16":
                generate_curse_omen_prompt(storage)
            elif option == "17":
                manage_characters_menu(storage)
            elif option == "18":
                heal_character_prompt(storage)
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
    print("7 - Realizar teste 1d20")
    print("8 - Simular dano fisico")
    print("9 - Simular dano magico")
    print("10 - Ver/organizar moeda Pedralume")
    print("11 - Ver locais conhecidos do mundo")
    print("12 - Gerar fala da Ikisaki")
    print("13 - Gerar consequencia narrativa")
    print("14 - Gerar evento aleatorio")
    print("15 - Gerar rumor")
    print("16 - Gerar pressagio da maldicao")
    print("17 - Gerenciar personagens")
    print("18 - Curar personagem")
    print("0 - Sair")


def ensure_initial_data(storage: JSONStorage) -> None:
    if not storage.path_for("characters.json").exists():
        save_characters(storage, [create_miko_meu()])
    load_or_create_miko(storage)
    storage.read_json("sessions.json", default=[])
    storage.read_json("world_state.json", default=default_world_state())


def show_miko(storage: JSONStorage) -> None:
    miko = load_or_create_miko(storage)
    print_json(miko.to_dict())


def roll_dice_prompt(storage: JSONStorage) -> None:
    character = select_character(storage, allow_skip=True)
    expression = input("Digite o dado (ex.: 1d20, 2d6): ").strip()
    result = roll_dice(expression)
    print(f"Resultado: {result.total} | Rolagens: {result.rolls}")
    register_event(
        storage,
        character=character.name if character else "Narrador",
        action=f"Rolou {result.expression}",
        result=f"Total {result.total}; individuais {result.rolls}",
    )


def use_ikisaki_prompt(storage: JSONStorage) -> None:
    miko = load_or_create_miko(storage)
    result = use_shadow_roulette(miko)
    narrative = narrate_ikisaki_roulette(result)
    save_character(storage, miko)

    print_json(result.to_dict())
    print("\nCena sugerida:")
    print_json(narrative.to_dict())
    register_event(
        storage,
        character=miko.name,
        action="Usou Roleta Sombria: Dez Elos de Ikisaki",
        result=f"{result.number} - {result.link_name}; preco {result.price_level}",
        notes=result.consequence or narrative.texto,
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
    selected_character = select_character(storage, allow_skip=True)
    character = selected_character.name if selected_character else input("Personagem: ").strip() or "Narrador"
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


def perform_skill_test_prompt(storage: JSONStorage) -> None:
    character = select_character(storage, allow_skip=True)
    test_types = list_test_types()
    print("\nTestes oficiais 1d20")
    for index, test_type in enumerate(test_types, start=1):
        print(f"{index} - {test_type}")

    selected = input("Escolha um teste: ").strip()
    if not selected.isdigit() or not 1 <= int(selected) <= len(test_types):
        raise ValueError("Escolha um teste valido.")

    result = perform_skill_test(test_types[int(selected) - 1])
    print_json(result.to_dict())
    register_event(
        storage,
        character=character.name if character else "Narrador",
        action=f"Realizou teste de {result.test_type}",
        result=f"{result.roll}: {result.interpretation}",
    )


def simulate_physical_damage_prompt(storage: JSONStorage) -> None:
    character = select_character(storage)
    damage_roll = roll_damage(character.current_health)
    result = apply_physical_damage(
        current_health=character.current_health,
        armor=character.armor,
        damage=damage_roll.result,
    )
    character.current_health = result.current_health
    character.armor = result.armor
    update_character(storage, character)
    print_json({"damage_roll": damage_roll.to_dict(), "application": result.to_dict()})
    register_event(
        storage,
        character=character.name,
        action="Simulou dano fisico",
        result=f"d{damage_roll.die_sides}={damage_roll.result}; vida {result.current_health}; armadura {result.armor}",
        notes=result.description,
    )


def simulate_magical_damage_prompt(storage: JSONStorage) -> None:
    character = select_character(storage)
    damage_roll = roll_damage(character.current_health)
    result = apply_magic_damage(
        current_health=character.current_health,
        armor=character.armor,
        damage=damage_roll.result,
    )
    character.current_health = result.current_health
    update_character(storage, character)
    print_json({"damage_roll": damage_roll.to_dict(), "application": result.to_dict()})
    register_event(
        storage,
        character=character.name,
        action="Simulou dano magico",
        result=f"d{damage_roll.die_sides}={damage_roll.result}; vida {result.current_health}; armadura {result.armor}",
        notes=result.description,
    )


def organize_pedralume_prompt() -> None:
    print("\nConversao oficial:")
    print("10 Pedralumes Brutas = 1 Pedralume Refinada")
    print("10 Pedralumes Refinadas = 1 Pedralume Pura")
    print("10 Pedralumes Puras = 1 Pedralume Primordial")
    print("1 Pedralume Primordial = 1000 Pedralumes Brutas")

    money = PedralumeMoney.from_units(
        bruta=read_int("Pedralumes Brutas: "),
        refinada=read_int("Pedralumes Refinadas: "),
        pura=read_int("Pedralumes Puras: "),
        primordial=read_int("Pedralumes Primordiais: "),
    )
    print(f"Organizado: {money.display()}")
    print(f"Total em Pedralumes Brutas: {money.raw_amount}")


def show_world_locations(storage: JSONStorage) -> None:
    print("\nLocais conhecidos do mundo")
    for location in list_locations(storage):
        print(f"- {location.name} ({location.type})")


def generate_ikisaki_line_prompt(storage: JSONStorage) -> None:
    categories = list_ikisaki_line_categories()
    print("\nCategorias de fala da Ikisaki")
    for index, category in enumerate(categories, start=1):
        print(f"{index} - {category}")

    selected = input("Escolha uma categoria: ").strip()
    if not selected.isdigit() or not 1 <= int(selected) <= len(categories):
        raise ValueError("Escolha uma categoria valida.")

    line = generate_ikisaki_line(categories[int(selected) - 1])
    print_json(line.to_dict())
    record_narrative_result(
        storage,
        character="Ikisaki",
        action=f"Fala da Ikisaki: {line.category}",
        result=line.text,
    )


def generate_narrative_consequence_prompt(storage: JSONStorage) -> None:
    price_levels = list_consequence_price_levels()
    print("\nNiveis de preco narrativo")
    for index, price_level in enumerate(price_levels, start=1):
        print(f"{index} - {price_level}")

    selected = input("Escolha um nivel: ").strip()
    if not selected.isdigit() or not 1 <= int(selected) <= len(price_levels):
        raise ValueError("Escolha um nivel de preco valido.")

    tone = ask_optional_tone()
    consequence = generate_narrative_consequence(price_levels[int(selected) - 1], tone=tone)
    print_json(consequence.to_dict())
    maybe_record_generated_result(
        storage,
        consequence,
        character=select_character_name_for_history(storage),
        action=f"Consequencia narrativa: {consequence.price_level}",
    )


def generate_random_event_prompt(storage: JSONStorage) -> None:
    tone = ask_optional_tone()
    location_type = ask_optional_location_type()
    event = generate_random_event(tone=tone, location_type=location_type)
    print_json(event.to_dict())
    maybe_record_generated_result(
        storage,
        event,
        character=select_character_name_for_history(storage),
        action=f"Evento aleatorio: {event.category}",
    )


def generate_rumor_prompt(storage: JSONStorage) -> None:
    tone = ask_optional_tone()
    rumor = generate_rumor(tone=tone)
    print_json(rumor.to_dict())
    maybe_record_generated_result(
        storage,
        rumor,
        character=select_character_name_for_history(storage),
        action=f"Rumor: {rumor.level}",
    )


def generate_curse_omen_prompt(storage: JSONStorage) -> None:
    omen = generate_curse_omen()
    print_json(omen.to_dict())
    maybe_record_generated_result(
        storage,
        omen,
        character="Miko Meu",
        action="Pressagio da maldicao de Ikisaki",
        notes="Pressagio narrativo; nao aplica dano automaticamente.",
    )


def maybe_record_generated_result(
    storage: JSONStorage,
    result,
    character: str,
    action: str,
    notes: str = "",
) -> None:
    decision = input("Registrar no historico? [s/N]: ").strip().casefold()
    should_register = decision in {"s", "sim", "y", "yes"}
    event = maybe_record_narrative_result(
        storage,
        result,
        should_register=should_register,
        character=character,
        action=action,
        notes=notes,
    )
    if event is None:
        print("Resultado descartado; nada foi salvo no historico.")
    else:
        print("Resultado registrado no historico.")


def ask_optional_tone() -> str | None:
    tones = list_tones()
    print("\nTons narrativos")
    print("0 - neutro/sem preferencia")
    for index, tone in enumerate(tones, start=1):
        print(f"{index} - {tone}")

    selected = input("Escolha um tom opcional: ").strip()
    if not selected or selected == "0":
        return None
    if selected.isdigit() and 1 <= int(selected) <= len(tones):
        return tones[int(selected) - 1]
    return selected


def ask_optional_location_type() -> str | None:
    location_types = list_location_types()
    print("\nTipo de local para contexto do evento")
    print("0 - sem contexto")
    for index, location_type in enumerate(location_types, start=1):
        print(f"{index} - {location_type}")

    selected = input("Escolha um tipo de local opcional: ").strip()
    if not selected or selected == "0":
        return None
    if selected.isdigit() and 1 <= int(selected) <= len(location_types):
        return location_types[int(selected) - 1]
    return selected


def manage_characters_menu(storage: JSONStorage) -> None:
    while True:
        print("\nGerenciar personagens")
        print("1 - Listar personagens")
        print("2 - Ver ficha de personagem")
        print("3 - Criar personagem")
        print("4 - Editar vida")
        print("5 - Editar armadura")
        print("6 - Adicionar equipamento")
        print("7 - Remover equipamento")
        print("8 - Adicionar observacao")
        print("0 - Voltar")

        option = input("Escolha uma opcao: ").strip()
        if option == "1":
            show_character_list(storage)
        elif option == "2":
            character = select_character(storage)
            print_json(character.to_dict())
        elif option == "3":
            create_character_prompt(storage)
        elif option == "4":
            character = select_character(storage)
            new_health = read_int("Nova vida atual: ")
            print_json(update_character_health(storage, character.id, new_health).to_dict())
        elif option == "5":
            character = select_character(storage)
            new_armor = read_int("Nova armadura: ")
            print_json(update_character_armor(storage, character.id, new_armor).to_dict())
        elif option == "6":
            character = select_character(storage)
            item = input("Equipamento para adicionar: ").strip()
            print_json(add_equipment(storage, character.id, item).to_dict())
        elif option == "7":
            character = select_character(storage)
            item = input("Equipamento para remover: ").strip()
            print_json(remove_equipment(storage, character.id, item).to_dict())
        elif option == "8":
            character = select_character(storage)
            note = input("Observacao: ").strip()
            print_json(add_note(storage, character.id, note).to_dict())
        elif option == "0":
            break
        else:
            print("Opcao invalida.")


def show_character_list(storage: JSONStorage) -> None:
    print("\nPersonagens")
    for character in list_characters(storage):
        print(f"- {character.id}: {character.name} ({character.character_class})")


def create_character_prompt(storage: JSONStorage) -> None:
    name = input("Nome: ").strip()
    character_class = input("Classe: ").strip()
    max_health = read_int("Vida maxima: ")
    armor = read_int("Armadura inicial: ")
    character = create_character(
        storage,
        name=name,
        character_class=character_class,
        max_health=max_health,
        armor=armor,
    )
    print("Personagem criado:")
    print_json(character.to_dict())


def heal_character_prompt(storage: JSONStorage) -> None:
    character = select_character(storage)
    amount = read_int("Quantidade de cura: ")
    result = apply_healing(character.current_health, character.max_health, amount)
    character.current_health = result.current_health
    update_character(storage, character)
    print_json(result.to_dict())
    register_event(
        storage,
        character=character.name,
        action="Curou personagem",
        result=f"Vida {result.current_health}/{result.max_health}; cura efetiva {result.amount_healed}",
        notes=result.description,
    )


def select_character(storage: JSONStorage, allow_skip: bool = False):
    characters = list_characters(storage)
    print("\nEscolha um personagem")
    if allow_skip:
        print("0 - Nenhum/Narrador")
    for index, character in enumerate(characters, start=1):
        print(f"{index} - {character.name} [{character.id}]")

    selected = input("Opcao ou id: ").strip()
    if allow_skip and (not selected or selected == "0"):
        return None
    if selected.isdigit() and 1 <= int(selected) <= len(characters):
        return characters[int(selected) - 1]
    return get_character(storage, selected)


def ask_use_character() -> bool:
    answer = input("Associar a um personagem? [s/N]: ").strip().casefold()
    return answer in {"s", "sim", "y", "yes"}


def select_character_name_for_history(storage: JSONStorage) -> str:
    if not ask_use_character():
        return "Narrador"
    character = select_character(storage, allow_skip=True)
    return character.name if character is not None else "Narrador"


def read_int(prompt: str) -> int:
    value = input(prompt).strip()
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError("Digite um numero inteiro valido.") from exc


def print_json(data: dict) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))
