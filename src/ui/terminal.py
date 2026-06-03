"""Simple terminal interface."""

from __future__ import annotations

import json
from pathlib import Path

from src.core.abilities import (
    ABILITY_TYPES,
    ABILITY_USES,
    Ability,
    add_ability,
    get_ability,
    list_abilities,
    remove_ability,
    restore_ability_uses,
    update_ability,
    use_ability,
)
from src.core.combat import apply_physical_damage, roll_damage
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
    add_session_resolved_pending_task,
    add_session_reward,
    create_campaign,
    create_campaign_session,
    default_campaign_data,
    default_campaign_session_data,
    finish_campaign,
    finish_campaign_session,
    get_campaign,
    get_campaign_session,
    list_campaign_sessions,
    list_campaigns,
    pause_campaign,
    resolve_campaign_pending_task,
    start_campaign_session,
    update_session_summary,
)
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
from src.core.creatures import (
    CREATURE_TYPES,
    add_creature_note,
    add_creature_status,
    apply_magical_damage_to_creature,
    apply_physical_damage_to_creature,
    create_creature,
    default_creature_data,
    get_creature,
    heal_creature,
    list_creatures,
    remove_creature,
    remove_creature_status,
    update_creature_armor,
    update_creature_health,
)
from src.core.dice import roll_dice
from src.core.magic import apply_healing, apply_magic_damage
from src.core.npcs import (
    NPC_ATTITUDES,
    NPC_ROLES,
    add_npc_note,
    add_npc_rumor,
    add_npc_status,
    change_npc_attitude,
    create_npc,
    default_npc_data,
    get_npc,
    list_npcs,
    remove_npc,
    remove_npc_status,
)
from src.core.session import list_events, register_event
from src.core.skill_tests import list_test_types, perform_skill_test
from src.core.turn_combat import (
    add_character_to_combat,
    add_creature_to_combat,
    add_participant_status,
    advance_turn,
    apply_magical_damage_to_participant,
    apply_physical_damage_to_participant,
    create_combat,
    default_combat_data,
    finish_combat,
    get_combat,
    get_current_participant,
    heal_participant,
    list_combats,
    register_free_combat_action,
    remove_participant_status,
    roll_initiative,
    start_combat,
    use_participant_ability,
)
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
from src.ui.formatting import (
    format_character_list,
    format_character_sheet,
    format_campaign_list,
    format_campaign_session_list,
    format_campaign_session_summary,
    format_campaign_summary,
    format_combat_list,
    format_combat_summary,
    format_current_participant,
    format_creature_list,
    format_creature_sheet,
    format_history,
    format_manual_test_script,
    format_npc_list,
    format_npc_sheet,
    format_title,
)


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
            elif option == "19":
                show_manual_test_script()
            elif option == "20":
                manage_creatures_menu(storage)
            elif option == "21":
                manage_npcs_menu(storage)
            elif option == "22":
                manage_combats_menu(storage)
            elif option == "23":
                manage_campaigns_menu(storage)
            elif option == "0":
                print("Saindo do MAGIK Engine. Boa sessao.")
                break
            else:
                print("Opcao invalida. Digite um numero listado no menu.")
        except (ValueError, RuntimeError) as error:
            print(f"\nNao consegui concluir essa acao: {error}")


def print_menu() -> None:
    print(format_title("MAGIK Engine"))
    print("1 - Ver ficha do Miko (atalho)")
    print("2 - Rolar dado")
    print("3 - Usar Roleta Sombria da Ikisaki (especial do Miko)")
    print("4 - Usar Cajado Sombrio (especial do Miko)")
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
    print("19 - Roteiro de teste manual")
    print("20 - Gerenciar criaturas/inimigos")
    print("21 - Gerenciar NPCs")
    print("22 - Gerenciar combates")
    print("23 - Gerenciar campanhas e sessoes")
    print("0 - Sair")


def ensure_initial_data(storage: JSONStorage) -> None:
    if not storage.path_for("characters.json").exists():
        save_characters(storage, [create_miko_meu()])
    load_or_create_miko(storage)
    storage.read_json("sessions.json", default=[])
    storage.read_json("world_state.json", default=default_world_state())
    storage.read_json("creatures.json", default=default_creature_data())
    storage.read_json("npcs.json", default=default_npc_data())
    storage.read_json("combats.json", default=default_combat_data())
    storage.read_json("campaigns.json", default=default_campaign_data())
    storage.read_json("campaign_sessions.json", default=default_campaign_session_data())


def show_miko(storage: JSONStorage) -> None:
    miko = load_or_create_miko(storage)
    print(format_character_sheet(miko))


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
    print(format_title("Sistema especial do Miko Meu: Ikisaki"))
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
    print(format_title("Sistema especial do Miko Meu: Cajado Sombrio"))
    spells = list_staff_spells()
    print("\nMagias disponiveis")
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
    print(format_history([event], limit=1))


def show_history(storage: JSONStorage) -> None:
    events = list_events(storage)
    print(format_history(events, limit=10))


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
        print(format_title("Gerenciar personagens"))
        print("1 - Listar personagens")
        print("2 - Ver ficha de personagem")
        print("3 - Criar personagem")
        print("4 - Editar vida")
        print("5 - Editar armadura")
        print("6 - Adicionar equipamento")
        print("7 - Remover equipamento")
        print("8 - Adicionar observacao")
        print("9 - Gerenciar habilidades")
        print("0 - Voltar")

        try:
            option = input("Escolha uma opcao: ").strip()
            if option == "1":
                show_character_list(storage)
            elif option == "2":
                character = select_character(storage)
                print(format_character_sheet(character))
            elif option == "3":
                create_character_prompt(storage)
            elif option == "4":
                character = select_character(storage)
                new_health = read_int("Nova vida atual: ")
                print(format_character_sheet(update_character_health(storage, character.id, new_health)))
            elif option == "5":
                character = select_character(storage)
                new_armor = read_int("Nova armadura: ")
                print(format_character_sheet(update_character_armor(storage, character.id, new_armor)))
            elif option == "6":
                character = select_character(storage)
                item = input("Equipamento para adicionar: ").strip()
                print(format_character_sheet(add_equipment(storage, character.id, item)))
            elif option == "7":
                character = select_character(storage)
                item = input("Equipamento para remover: ").strip()
                print(format_character_sheet(remove_equipment(storage, character.id, item)))
            elif option == "8":
                character = select_character(storage)
                note = input("Observacao: ").strip()
                print(format_character_sheet(add_note(storage, character.id, note)))
            elif option == "9":
                manage_abilities_menu(storage)
            elif option == "0":
                break
            else:
                print("Opcao invalida. Digite um numero listado no menu.")
        except ValueError as error:
            print(f"\nNao consegui concluir essa acao: {error}")


def show_character_list(storage: JSONStorage) -> None:
    print(format_character_list(list_characters(storage)))


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
    print(format_character_sheet(character))


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


def manage_abilities_menu(storage: JSONStorage) -> None:
    character = select_character(storage)
    while True:
        print(format_title(f"Habilidades de {character.name}"))
        print("1 - Listar habilidades")
        print("2 - Adicionar habilidade")
        print("3 - Editar habilidade")
        print("4 - Remover habilidade")
        print("5 - Usar habilidade")
        print("6 - Restaurar usos de habilidades")
        print("0 - Voltar")

        try:
            option = input("Escolha uma opcao: ").strip()
            character = get_character(storage, character.id)
            if option == "1":
                show_abilities(character)
            elif option == "2":
                ability = read_ability_fields()
                update_character(storage, add_ability(character, ability))
                print("Habilidade adicionada.")
            elif option == "3":
                ability_id = input("Id da habilidade para editar: ").strip()
                current = get_ability(character, ability_id)
                ability = read_ability_fields(current)
                update_character(storage, update_ability(character, ability))
                print("Habilidade atualizada.")
            elif option == "4":
                ability_id = input("Id da habilidade para remover: ").strip()
                update_character(storage, remove_ability(character, ability_id))
                print("Habilidade removida.")
            elif option == "5":
                use_character_ability_prompt(storage, character)
            elif option == "6":
                scope = input("Restaurar por combate, sessao ou todos? [sessao]: ").strip() or "sessao"
                update_character(storage, restore_ability_uses(character, scope))
                print("Usos restaurados quando aplicavel.")
            elif option == "0":
                break
            else:
                print("Opcao invalida. Digite um numero listado no menu.")
        except ValueError as error:
            print(f"\nNao consegui concluir essa acao: {error}")


def show_abilities(character) -> None:
    abilities = list_abilities(character)
    if not abilities:
        print("Nenhuma habilidade cadastrada.")
        return
    for ability in abilities:
        print(format_title(ability.name))
        print(f"Id: {ability.id}")
        print(f"Tipo: {ability.type}")
        print(f"Uso: {ability.use}")
        print(f"Efeito: {ability.effect or 'sem efeito descrito'}")
        print(f"Custo: {ability.cost or 'sem custo descrito'}")
        if ability.usage_limit is not None:
            print(f"Usos: {ability.remaining_uses}/{ability.usage_limit}")
        print(f"Exige teste: {'sim' if ability.requires_test else 'nao'}")
        if ability.suggested_test:
            print(f"Teste sugerido: {ability.suggested_test}")
        if ability.notes:
            print(f"Observacoes: {ability.notes}")


def read_ability_fields(current: Ability | None = None) -> Ability:
    current = current or Ability(id="", name="")
    ability_id = input_with_default("Id", current.id)
    name = input_with_default("Nome", current.name)
    description = input_with_default("Descricao", current.description)
    ability_type = input_with_default(f"Tipo ({', '.join(sorted(ABILITY_TYPES))})", current.type)
    use = input_with_default(f"Uso ({', '.join(sorted(ABILITY_USES))})", current.use)
    effect = input_with_default("Efeito", current.effect)
    cost = input_with_default("Custo", current.cost)
    usage_limit = read_optional_int("Limite de uso", current.usage_limit)
    remaining_uses = read_optional_int("Usos restantes", current.remaining_uses)
    requires_test = read_bool("Exige teste?", current.requires_test)
    suggested_test = input_with_default("Teste sugerido", current.suggested_test or "") or None
    notes = input_with_default("Observacoes", current.notes)
    return Ability(
        id=ability_id,
        name=name,
        description=description,
        type=ability_type,
        use=use,
        effect=effect,
        cost=cost,
        usage_limit=usage_limit,
        remaining_uses=remaining_uses,
        requires_test=requires_test,
        suggested_test=suggested_test,
        notes=notes,
    )


def use_character_ability_prompt(storage: JSONStorage, character) -> None:
    show_abilities(character)
    ability_id = input("Id da habilidade para usar: ").strip()
    result = use_ability(character, ability_id)
    update_character(storage, character)
    ability = result.ability
    print(format_title(f"Habilidade usada: {ability.name}"))
    print(f"Efeito: {result.effect or 'sem efeito descrito'}")
    print(f"Custo: {result.cost or 'sem custo descrito'}")
    if ability.suggested_test:
        print(f"Teste sugerido: {ability.suggested_test}")
    if result.remaining_uses is not None:
        print(f"Usos restantes: {result.remaining_uses}")
    if character.id == "miko-meu" and ability.id in {"ikisaki_roulette", "shadow_staff"}:
        print("Aviso: esta habilidade tem um sistema proprio no menu principal.")
    register_event(
        storage,
        character=character.name,
        action=f"Usou habilidade: {ability.name}",
        result=result.effect or "Habilidade usada.",
        notes=(
            f"Custo: {result.cost or 'nenhum'}. "
            f"Usos restantes: {result.remaining_uses if result.remaining_uses is not None else 'livre'}. "
            f"Observacoes: {result.notes or 'nenhuma'}."
        ),
    )


def select_character(storage: JSONStorage, allow_skip: bool = False):
    characters = list_characters(storage)
    print(format_character_list(characters, allow_skip=allow_skip))

    selected = input("Opcao ou id: ").strip()
    if allow_skip and (not selected or selected == "0"):
        return None
    if selected.isdigit() and 1 <= int(selected) <= len(characters):
        return characters[int(selected) - 1]
    if selected.isdigit():
        raise ValueError("Numero de personagem fora da lista.")
    return get_character(storage, selected)


def ask_use_character() -> bool:
    answer = input("Associar a um personagem? [s/N]: ").strip().casefold()
    return answer in {"s", "sim", "y", "yes"}


def select_character_name_for_history(storage: JSONStorage) -> str:
    if not ask_use_character():
        return "Narrador"
    character = select_character(storage, allow_skip=True)
    return character.name if character is not None else "Narrador"


def show_manual_test_script() -> None:
    print(format_manual_test_script())


def manage_creatures_menu(storage: JSONStorage) -> None:
    while True:
        print(format_title("Gerenciar criaturas/inimigos"))
        print("1 - Listar criaturas")
        print("2 - Ver ficha de criatura")
        print("3 - Criar criatura")
        print("4 - Editar vida")
        print("5 - Editar armadura")
        print("6 - Aplicar dano fisico")
        print("7 - Aplicar dano magico")
        print("8 - Curar criatura")
        print("9 - Adicionar status")
        print("10 - Remover status")
        print("11 - Adicionar observacao")
        print("12 - Remover criatura")
        print("0 - Voltar")

        try:
            option = input("Escolha uma opcao: ").strip()
            if option == "1":
                print(format_creature_list(list_creatures(storage)))
            elif option == "2":
                print(format_creature_sheet(select_creature(storage)))
            elif option == "3":
                creature = create_creature_prompt(storage)
                register_event(storage, creature.name, "Criatura criada", creature.type, creature.description)
            elif option == "4":
                creature = select_creature(storage)
                updated = update_creature_health(storage, creature.id, read_int("Nova vida atual: "))
                print(format_creature_sheet(updated))
            elif option == "5":
                creature = select_creature(storage)
                updated = update_creature_armor(storage, creature.id, read_int("Nova armadura: "))
                print(format_creature_sheet(updated))
            elif option == "6":
                creature = select_creature(storage)
                damage = read_int("Dano fisico: ")
                updated, description = apply_physical_damage_to_creature(storage, creature.id, damage)
                print(format_creature_sheet(updated))
                register_event(storage, updated.name, "Dano fisico aplicado", f"{damage} de dano", description)
            elif option == "7":
                creature = select_creature(storage)
                damage = read_int("Dano magico: ")
                updated, description = apply_magical_damage_to_creature(storage, creature.id, damage)
                print(format_creature_sheet(updated))
                register_event(storage, updated.name, "Dano magico aplicado", f"{damage} de dano", description)
            elif option == "8":
                creature = select_creature(storage)
                amount = read_int("Cura: ")
                updated, description = heal_creature(storage, creature.id, amount)
                print(format_creature_sheet(updated))
                register_event(storage, updated.name, "Criatura curada", f"{amount} de cura", description)
            elif option == "9":
                creature = select_creature(storage)
                status = input("Status: ").strip()
                updated = add_creature_status(storage, creature.id, status)
                print(format_creature_sheet(updated))
                register_event(storage, updated.name, "Status de criatura adicionado", status)
            elif option == "10":
                creature = select_creature(storage)
                status = input("Status: ").strip()
                updated = remove_creature_status(storage, creature.id, status)
                print(format_creature_sheet(updated))
                register_event(storage, updated.name, "Status de criatura removido", status)
            elif option == "11":
                creature = select_creature(storage)
                note = input("Observacao: ").strip()
                updated = add_creature_note(storage, creature.id, note)
                print(format_creature_sheet(updated))
                register_event(storage, updated.name, "Observacao de criatura adicionada", note)
            elif option == "12":
                creature = select_creature(storage)
                removed = remove_creature(storage, creature.id)
                print(f"Criatura removida: {removed.name}")
                register_event(storage, removed.name, "Criatura removida", removed.id)
            elif option == "0":
                break
            else:
                print("Opcao invalida. Digite um numero listado no menu.")
        except ValueError as error:
            print(f"\nNao consegui concluir essa acao: {error}")


def create_creature_prompt(storage: JSONStorage):
    name = input("Nome: ").strip()
    creature_type = input_with_default(f"Tipo ({', '.join(sorted(CREATURE_TYPES))})", "criatura")
    max_health = read_int("Vida maxima: ")
    armor = read_int("Armadura: ")
    description = input("Descricao: ").strip()
    location = input("Localizacao opcional: ").strip() or None
    threat_level = input("Nivel de ameaca opcional: ").strip() or None
    creature = create_creature(
        storage,
        name=name,
        creature_type=creature_type,
        max_health=max_health,
        armor=armor,
        description=description,
        location=location,
        threat_level=threat_level,
    )
    print(format_creature_sheet(creature))
    return creature


def select_creature(storage: JSONStorage):
    creatures = list_creatures(storage)
    print(format_creature_list(creatures))
    selected = input("Opcao ou id: ").strip()
    if selected.isdigit() and 1 <= int(selected) <= len(creatures):
        return creatures[int(selected) - 1]
    if selected.isdigit():
        raise ValueError("Numero de criatura fora da lista.")
    return get_creature(storage, selected)


def manage_npcs_menu(storage: JSONStorage) -> None:
    while True:
        print(format_title("Gerenciar NPCs"))
        print("1 - Listar NPCs")
        print("2 - Ver ficha de NPC")
        print("3 - Criar NPC")
        print("4 - Alterar atitude")
        print("5 - Adicionar rumor")
        print("6 - Adicionar status")
        print("7 - Remover status")
        print("8 - Adicionar observacao")
        print("9 - Remover NPC")
        print("0 - Voltar")

        try:
            option = input("Escolha uma opcao: ").strip()
            if option == "1":
                print(format_npc_list(list_npcs(storage)))
            elif option == "2":
                print(format_npc_sheet(select_npc(storage)))
            elif option == "3":
                npc = create_npc_prompt(storage)
                register_event(storage, npc.name, "NPC criado", npc.role, npc.description)
            elif option == "4":
                npc = select_npc(storage)
                attitude = input_with_default(f"Atitude ({', '.join(sorted(NPC_ATTITUDES))})", npc.attitude)
                updated = change_npc_attitude(storage, npc.id, attitude)
                print(format_npc_sheet(updated))
                register_event(storage, updated.name, "Atitude de NPC alterada", updated.attitude)
            elif option == "5":
                npc = select_npc(storage)
                rumor = input("Rumor: ").strip()
                updated = add_npc_rumor(storage, npc.id, rumor)
                print(format_npc_sheet(updated))
                register_event(storage, updated.name, "Rumor de NPC adicionado", rumor)
            elif option == "6":
                npc = select_npc(storage)
                status = input("Status: ").strip()
                updated = add_npc_status(storage, npc.id, status)
                print(format_npc_sheet(updated))
                register_event(storage, updated.name, "Status de NPC adicionado", status)
            elif option == "7":
                npc = select_npc(storage)
                status = input("Status: ").strip()
                updated = remove_npc_status(storage, npc.id, status)
                print(format_npc_sheet(updated))
                register_event(storage, updated.name, "Status de NPC removido", status)
            elif option == "8":
                npc = select_npc(storage)
                note = input("Observacao: ").strip()
                updated = add_npc_note(storage, npc.id, note)
                print(format_npc_sheet(updated))
                register_event(storage, updated.name, "Observacao de NPC adicionada", note)
            elif option == "9":
                npc = select_npc(storage)
                removed = remove_npc(storage, npc.id)
                print(f"NPC removido: {removed.name}")
                register_event(storage, removed.name, "NPC removido", removed.id)
            elif option == "0":
                break
            else:
                print("Opcao invalida. Digite um numero listado no menu.")
        except ValueError as error:
            print(f"\nNao consegui concluir essa acao: {error}")


def create_npc_prompt(storage: JSONStorage):
    name = input("Nome: ").strip()
    role = input_with_default(f"Papel ({', '.join(sorted(NPC_ROLES))})", "outro")
    attitude = input_with_default(f"Atitude ({', '.join(sorted(NPC_ATTITUDES))})", "neutra")
    location = input("Localizacao opcional: ").strip() or None
    description = input("Descricao: ").strip()
    npc = create_npc(
        storage,
        name=name,
        role=role,
        attitude=attitude,
        location=location,
        description=description,
    )
    print(format_npc_sheet(npc))
    return npc


def select_npc(storage: JSONStorage):
    npcs = list_npcs(storage)
    print(format_npc_list(npcs))
    selected = input("Opcao ou id: ").strip()
    if selected.isdigit() and 1 <= int(selected) <= len(npcs):
        return npcs[int(selected) - 1]
    if selected.isdigit():
        raise ValueError("Numero de NPC fora da lista.")
    return get_npc(storage, selected)


def manage_combats_menu(storage: JSONStorage) -> None:
    while True:
        print(format_title("Gerenciar combates"))
        print("1 - Listar combates")
        print("2 - Criar combate")
        print("3 - Ver combate")
        print("4 - Adicionar personagem")
        print("5 - Adicionar criatura")
        print("6 - Rolar iniciativa")
        print("7 - Iniciar combate")
        print("8 - Ver turno atual")
        print("9 - Avancar turno")
        print("10 - Aplicar dano fisico")
        print("11 - Aplicar dano magico")
        print("12 - Curar participante")
        print("13 - Adicionar status")
        print("14 - Remover status")
        print("15 - Usar habilidade")
        print("16 - Registrar acao narrativa")
        print("17 - Finalizar combate")
        print("0 - Voltar")

        try:
            option = input("Escolha uma opcao: ").strip()
            if option == "1":
                print(format_combat_list(list_combats(storage)))
            elif option == "2":
                combat = create_combat(storage, input("Nome do combate: ").strip())
                print(format_combat_summary(combat))
            elif option == "3":
                print(format_combat_summary(select_combat(storage)))
            elif option == "4":
                combat = select_combat(storage)
                character = select_character(storage)
                print(format_combat_summary(add_character_to_combat(storage, combat.id, character.id)))
            elif option == "5":
                combat = select_combat(storage)
                creature = select_creature(storage)
                print(format_combat_summary(add_creature_to_combat(storage, combat.id, creature.id)))
            elif option == "6":
                combat = select_combat(storage)
                print(format_combat_summary(roll_initiative(storage, combat.id)))
            elif option == "7":
                combat = select_combat(storage)
                print(format_combat_summary(start_combat(storage, combat.id)))
            elif option == "8":
                combat = select_combat(storage)
                current = get_current_participant(combat)
                print(format_title("Turno atual"))
                print(format_current_participant(combat))
                print(f"Participante: {current.name}")
            elif option == "9":
                combat = select_combat(storage)
                print(format_combat_summary(advance_turn(storage, combat.id)))
            elif option == "10":
                combat, participant_id = select_combat_participant(storage)
                damage = read_int("Dano fisico: ")
                print(format_combat_summary(apply_physical_damage_to_participant(storage, combat.id, participant_id, damage)))
            elif option == "11":
                combat, participant_id = select_combat_participant(storage)
                damage = read_int("Dano magico: ")
                print(format_combat_summary(apply_magical_damage_to_participant(storage, combat.id, participant_id, damage)))
            elif option == "12":
                combat, participant_id = select_combat_participant(storage)
                amount = read_int("Cura: ")
                print(format_combat_summary(heal_participant(storage, combat.id, participant_id, amount)))
            elif option == "13":
                combat, participant_id = select_combat_participant(storage)
                status = input("Status: ").strip()
                print(format_combat_summary(add_participant_status(storage, combat.id, participant_id, status)))
            elif option == "14":
                combat, participant_id = select_combat_participant(storage)
                status = input("Status: ").strip()
                print(format_combat_summary(remove_participant_status(storage, combat.id, participant_id, status)))
            elif option == "15":
                combat, participant_id = select_combat_participant(storage)
                ability_id = input("Id da habilidade: ").strip()
                print(format_combat_summary(use_participant_ability(storage, combat.id, participant_id, ability_id)))
            elif option == "16":
                combat = select_combat(storage)
                description = input("Acao narrativa: ").strip()
                print(format_combat_summary(register_free_combat_action(storage, combat.id, description)))
            elif option == "17":
                combat = select_combat(storage)
                print(format_combat_summary(finish_combat(storage, combat.id)))
            elif option == "0":
                break
            else:
                print("Opcao invalida. Digite um numero listado no menu.")
        except ValueError as error:
            print(f"\nNao consegui concluir essa acao: {error}")


def select_combat(storage: JSONStorage):
    combats = list_combats(storage)
    print(format_combat_list(combats))
    selected = input("Opcao ou id: ").strip()
    if selected.isdigit() and 1 <= int(selected) <= len(combats):
        return combats[int(selected) - 1]
    if selected.isdigit():
        raise ValueError("Numero de combate fora da lista.")
    return get_combat(storage, selected)


def select_combat_participant(storage: JSONStorage):
    combat = select_combat(storage)
    print(format_combat_summary(combat, history_limit=2))
    selected = input("Participante por numero, id ou referencia: ").strip()
    if selected.isdigit() and 1 <= int(selected) <= len(combat.participants):
        participant_id = combat.participants[int(selected) - 1].id
    elif selected.isdigit():
        raise ValueError("Numero de participante fora da lista.")
    else:
        participant_id = selected
    return combat, participant_id


def manage_campaigns_menu(storage: JSONStorage) -> None:
    while True:
        print(format_title("Gerenciar campanhas e sessoes"))
        print("1 - Listar campanhas")
        print("2 - Criar campanha")
        print("3 - Ver campanha")
        print("4 - Adicionar personagem participante")
        print("5 - Adicionar NPC importante")
        print("6 - Adicionar local importante")
        print("7 - Adicionar evento importante")
        print("8 - Adicionar pendencia")
        print("9 - Resolver pendencia")
        print("10 - Pausar campanha")
        print("11 - Finalizar campanha")
        print("12 - Gerenciar sessoes da campanha")
        print("0 - Voltar")

        try:
            option = input("Escolha uma opcao: ").strip()
            if option == "1":
                print(format_campaign_list(list_campaigns(storage)))
            elif option == "2":
                campaign = create_campaign_prompt(storage)
                register_event(storage, "Campanha", "Campanha criada", campaign.name, campaign.description)
            elif option == "3":
                print(format_campaign_summary(select_campaign(storage)))
            elif option == "4":
                campaign = select_campaign(storage)
                character = select_character(storage)
                updated = add_campaign_player_character(storage, campaign.id, character.id)
                print(format_campaign_summary(updated))
                register_event(storage, "Campanha", "Personagem adicionado a campanha", character.name)
            elif option == "5":
                campaign = select_campaign(storage)
                npc = select_npc(storage)
                updated = add_campaign_npc(storage, campaign.id, npc.id)
                print(format_campaign_summary(updated))
                register_event(storage, "Campanha", "NPC importante adicionado", npc.name)
            elif option == "6":
                campaign = select_campaign(storage)
                location = input("Local importante: ").strip()
                updated = add_campaign_location(storage, campaign.id, location)
                print(format_campaign_summary(updated))
                register_event(storage, "Campanha", "Local importante adicionado", location)
            elif option == "7":
                campaign = select_campaign(storage)
                event = input("Evento importante: ").strip()
                updated = add_campaign_event(storage, campaign.id, event)
                print(format_campaign_summary(updated))
                register_event(storage, "Campanha", "Evento importante adicionado", event)
            elif option == "8":
                campaign = select_campaign(storage)
                task = input("Pendencia: ").strip()
                updated = add_campaign_pending_task(storage, campaign.id, task)
                print(format_campaign_summary(updated))
                register_event(storage, "Campanha", "Pendencia adicionada", task)
            elif option == "9":
                campaign = select_campaign(storage)
                task = input("Pendencia resolvida: ").strip()
                updated = resolve_campaign_pending_task(storage, campaign.id, task)
                print(format_campaign_summary(updated))
                register_event(storage, "Campanha", "Pendencia resolvida", task)
            elif option == "10":
                campaign = select_campaign(storage)
                updated = pause_campaign(storage, campaign.id)
                print(format_campaign_summary(updated))
                register_event(storage, "Campanha", "Campanha pausada", updated.name)
            elif option == "11":
                campaign = select_campaign(storage)
                updated = finish_campaign(storage, campaign.id)
                print(format_campaign_summary(updated))
                register_event(storage, "Campanha", "Campanha finalizada", updated.name)
            elif option == "12":
                campaign = select_campaign(storage)
                manage_campaign_sessions_menu(storage, campaign.id)
            elif option == "0":
                break
            else:
                print("Opcao invalida. Digite um numero listado no menu.")
        except ValueError as error:
            print(f"\nNao consegui concluir essa acao: {error}")


def create_campaign_prompt(storage: JSONStorage):
    name = input("Nome da campanha: ").strip()
    description = input("Descricao: ").strip()
    campaign = create_campaign(storage, name, description)
    print(format_campaign_summary(campaign))
    return campaign


def select_campaign(storage: JSONStorage):
    campaigns = list_campaigns(storage)
    print(format_campaign_list(campaigns))
    selected = input("Opcao ou id: ").strip()
    if selected.isdigit() and 1 <= int(selected) <= len(campaigns):
        return campaigns[int(selected) - 1]
    if selected.isdigit():
        raise ValueError("Numero de campanha fora da lista.")
    return get_campaign(storage, selected)


def manage_campaign_sessions_menu(storage: JSONStorage, campaign_id: str) -> None:
    while True:
        print(format_title(f"Sessoes da campanha {campaign_id}"))
        print("1 - Listar sessoes")
        print("2 - Criar sessao")
        print("3 - Ver sessao")
        print("4 - Iniciar sessao")
        print("5 - Finalizar sessao")
        print("6 - Adicionar evento")
        print("7 - Associar combate")
        print("8 - Adicionar recompensa")
        print("9 - Adicionar consequencia")
        print("10 - Adicionar pendencia criada")
        print("11 - Adicionar pendencia resolvida")
        print("12 - Adicionar observacao")
        print("13 - Atualizar resumo")
        print("0 - Voltar")

        try:
            option = input("Escolha uma opcao: ").strip()
            if option == "1":
                print(format_campaign_session_list(list_campaign_sessions(storage, campaign_id)))
            elif option == "2":
                session = create_campaign_session_prompt(storage, campaign_id)
                register_event(storage, "Sessao", "Sessao de campanha criada", session.title)
            elif option == "3":
                print(format_campaign_session_summary(select_campaign_session(storage, campaign_id)))
            elif option == "4":
                session = select_campaign_session(storage, campaign_id)
                updated = start_campaign_session(storage, session.id)
                print(format_campaign_session_summary(updated))
                register_event(storage, "Sessao", "Sessao iniciada", updated.title)
            elif option == "5":
                session = select_campaign_session(storage, campaign_id)
                updated = finish_campaign_session(storage, session.id)
                print(format_campaign_session_summary(updated))
                register_event(storage, "Sessao", "Sessao finalizada", updated.title)
            elif option == "6":
                session = select_campaign_session(storage, campaign_id)
                event = input("Evento: ").strip()
                updated = add_session_event(storage, session.id, event)
                print(format_campaign_session_summary(updated))
                register_event(storage, "Sessao", "Evento adicionado a sessao", event)
            elif option == "7":
                session = select_campaign_session(storage, campaign_id)
                combat = select_combat(storage)
                updated = add_session_combat(storage, session.id, combat.id)
                print(format_campaign_session_summary(updated))
                register_event(storage, "Sessao", "Combate associado a sessao", combat.name)
            elif option == "8":
                session = select_campaign_session(storage, campaign_id)
                reward = input("Recompensa: ").strip()
                updated = add_session_reward(storage, session.id, reward)
                print(format_campaign_session_summary(updated))
                register_event(storage, "Sessao", "Recompensa adicionada", reward)
            elif option == "9":
                session = select_campaign_session(storage, campaign_id)
                consequence = input("Consequencia: ").strip()
                updated = add_session_consequence(storage, session.id, consequence)
                print(format_campaign_session_summary(updated))
                register_event(storage, "Sessao", "Consequencia adicionada", consequence)
            elif option == "10":
                session = select_campaign_session(storage, campaign_id)
                task = input("Pendencia criada: ").strip()
                updated = add_session_created_pending_task(storage, session.id, task)
                print(format_campaign_session_summary(updated))
                register_event(storage, "Sessao", "Pendencia criada na sessao", task)
            elif option == "11":
                session = select_campaign_session(storage, campaign_id)
                task = input("Pendencia resolvida: ").strip()
                updated = add_session_resolved_pending_task(storage, session.id, task)
                print(format_campaign_session_summary(updated))
                register_event(storage, "Sessao", "Pendencia resolvida na sessao", task)
            elif option == "12":
                session = select_campaign_session(storage, campaign_id)
                note = input("Observacao: ").strip()
                updated = add_session_note(storage, session.id, note)
                print(format_campaign_session_summary(updated))
                register_event(storage, "Sessao", "Observacao adicionada a sessao", note)
            elif option == "13":
                session = select_campaign_session(storage, campaign_id)
                summary = input("Resumo: ").strip()
                updated = update_session_summary(storage, session.id, summary)
                print(format_campaign_session_summary(updated))
                register_event(storage, "Sessao", "Resumo atualizado", updated.title)
            elif option == "0":
                break
            else:
                print("Opcao invalida. Digite um numero listado no menu.")
        except ValueError as error:
            print(f"\nNao consegui concluir essa acao: {error}")


def create_campaign_session_prompt(storage: JSONStorage, campaign_id: str):
    title = input("Titulo da sessao: ").strip()
    number_text = input("Numero opcional da sessao: ").strip()
    number = int(number_text) if number_text else None
    summary = input("Resumo inicial: ").strip()
    session = create_campaign_session(storage, campaign_id, title, number=number, summary=summary)
    print(format_campaign_session_summary(session))
    return session


def select_campaign_session(storage: JSONStorage, campaign_id: str):
    sessions = list_campaign_sessions(storage, campaign_id)
    print(format_campaign_session_list(sessions))
    selected = input("Opcao ou id: ").strip()
    if selected.isdigit() and 1 <= int(selected) <= len(sessions):
        return sorted(sessions, key=lambda item: item.number)[int(selected) - 1]
    if selected.isdigit():
        raise ValueError("Numero de sessao fora da lista.")
    return get_campaign_session(storage, selected)


def read_int(prompt: str) -> int:
    value = input(prompt).strip()
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError("Digite um numero inteiro valido.") from exc


def read_optional_int(prompt: str, default: int | None = None) -> int | None:
    default_text = "" if default is None else str(default)
    value = input_with_default(prompt, default_text)
    if not value:
        return None
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError("Digite um numero inteiro valido.") from exc


def read_bool(prompt: str, default: bool = False) -> bool:
    suffix = "S/n" if default else "s/N"
    value = input(f"{prompt} [{suffix}]: ").strip().casefold()
    if not value:
        return default
    return value in {"s", "sim", "y", "yes"}


def input_with_default(prompt: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    value = input(f"{prompt}{suffix}: ").strip()
    return value if value else default


def print_json(data: dict) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))
