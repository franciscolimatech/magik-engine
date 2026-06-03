import pytest

from src.core.character import create_miko_meu, save_characters, get_character
from src.core.creatures import create_creature, get_creature
from src.core.turn_combat import (
    add_character_to_combat,
    add_creature_to_combat,
    add_participant_status,
    advance_round,
    advance_turn,
    apply_magical_damage_to_participant,
    apply_physical_damage_to_participant,
    create_combat,
    finish_combat,
    get_combat,
    get_current_participant,
    heal_participant,
    list_combats,
    order_participants,
    record_combat_action,
    register_free_combat_action,
    remove_participant_status,
    roll_initiative,
    start_combat,
)
from src.storage.memory import MemoryStorage


class FixedRng:
    def __init__(self, values: list[int]) -> None:
        self.values = values
        self.index = 0

    def randint(self, _start: int, _end: int) -> int:
        value = self.values[self.index]
        self.index += 1
        return value


def make_storage() -> MemoryStorage:
    storage = MemoryStorage(
        {
            "characters.json": {"characters": [create_miko_meu().to_dict()]},
            "creatures.json": {"creatures": []},
            "combats.json": {"combats": []},
            "sessions.json": [],
        }
    )
    create_creature(storage, "Kriot", "criatura", 20, armor=5)
    return storage


def make_combat_with_two_participants() -> tuple[MemoryStorage, str]:
    storage = make_storage()
    combat = create_combat(storage, "Teste")
    add_character_to_combat(storage, combat.id, "miko-meu")
    add_creature_to_combat(storage, combat.id, "kriot")
    return storage, combat.id


def test_create_combat() -> None:
    storage = make_storage()

    combat = create_combat(storage, "Emboscada")

    assert combat.id == "emboscada"
    assert combat.status == "em_andamento"
    assert combat.current_round == 1


def test_list_combats() -> None:
    storage = make_storage()
    create_combat(storage, "Emboscada")

    assert [combat.name for combat in list_combats(storage)] == ["Emboscada"]


def test_get_existing_combat() -> None:
    storage = make_storage()
    create_combat(storage, "Emboscada")

    assert get_combat(storage, "emboscada").name == "Emboscada"


def test_get_missing_combat_raises_error() -> None:
    storage = make_storage()

    with pytest.raises(ValueError):
        get_combat(storage, "nao-existe")


def test_add_character_to_combat() -> None:
    storage = make_storage()
    combat = create_combat(storage, "Teste")

    updated = add_character_to_combat(storage, combat.id, "miko-meu")

    assert updated.participants[0].id == "personagem:miko-meu"


def test_add_creature_to_combat() -> None:
    storage = make_storage()
    combat = create_combat(storage, "Teste")

    updated = add_creature_to_combat(storage, combat.id, "kriot")

    assert updated.participants[0].id == "criatura:kriot"


def test_prevent_duplicate_participant() -> None:
    storage = make_storage()
    combat = create_combat(storage, "Teste")
    add_character_to_combat(storage, combat.id, "miko-meu")

    with pytest.raises(ValueError):
        add_character_to_combat(storage, combat.id, "miko-meu")


def test_roll_initiative_and_order() -> None:
    storage, combat_id = make_combat_with_two_participants()

    combat = roll_initiative(storage, combat_id, rng=FixedRng([5, 18]))

    assert [participant.initiative for participant in combat.participants] == [18, 5]
    assert combat.participants[0].name == "Kriot"


def test_order_participants_by_initiative() -> None:
    storage, combat_id = make_combat_with_two_participants()
    combat = get_combat(storage, combat_id)
    combat.participants[0].initiative = 3
    combat.participants[1].initiative = 12

    order_participants(combat)

    assert combat.participants[0].initiative == 12


def test_start_combat_sets_current_turn() -> None:
    storage, combat_id = make_combat_with_two_participants()
    roll_initiative(storage, combat_id, rng=FixedRng([10, 1]))

    combat = start_combat(storage, combat_id)

    assert get_current_participant(combat).name == "Miko Meu"


def test_advance_turn() -> None:
    storage, combat_id = make_combat_with_two_participants()
    roll_initiative(storage, combat_id, rng=FixedRng([10, 1]))

    combat = advance_turn(storage, combat_id)

    assert get_current_participant(combat).name == "Kriot"


def test_advance_round_when_turn_wraps() -> None:
    storage, combat_id = make_combat_with_two_participants()
    roll_initiative(storage, combat_id, rng=FixedRng([10, 1]))
    advance_turn(storage, combat_id)

    combat = advance_turn(storage, combat_id)

    assert combat.current_round == 2
    assert get_current_participant(combat).name == "Miko Meu"


def test_advance_round_manual() -> None:
    storage, combat_id = make_combat_with_two_participants()

    combat = advance_round(storage, combat_id)

    assert combat.current_round == 2


def test_skip_dead_participant() -> None:
    storage, combat_id = make_combat_with_two_participants()
    roll_initiative(storage, combat_id, rng=FixedRng([10, 1]))
    combat = get_combat(storage, combat_id)
    combat.participants[1].current_health = 0
    combat.participants[1].is_alive = False
    from src.core.turn_combat import update_combat

    update_combat(storage, combat)

    updated = advance_turn(storage, combat_id)

    assert get_current_participant(updated).name == "Miko Meu"


def test_apply_physical_damage_to_participant_syncs_creature() -> None:
    storage, combat_id = make_combat_with_two_participants()

    combat = apply_physical_damage_to_participant(storage, combat_id, "criatura:kriot", 8)

    participant = [item for item in combat.participants if item.id == "criatura:kriot"][0]
    assert participant.armor == 0
    assert participant.current_health == 20
    assert get_creature(storage, "kriot").armor == 0


def test_apply_magical_damage_to_participant_syncs_character() -> None:
    storage, combat_id = make_combat_with_two_participants()

    combat = apply_magical_damage_to_participant(storage, combat_id, "personagem:miko-meu", 5)

    participant = [item for item in combat.participants if item.id == "personagem:miko-meu"][0]
    assert participant.current_health == 20
    assert get_character(storage, "miko-meu").current_health == 20


def test_heal_participant() -> None:
    storage, combat_id = make_combat_with_two_participants()
    apply_magical_damage_to_participant(storage, combat_id, "personagem:miko-meu", 10)

    combat = heal_participant(storage, combat_id, "personagem:miko-meu", 20)

    participant = [item for item in combat.participants if item.id == "personagem:miko-meu"][0]
    assert participant.current_health == 25


def test_add_and_remove_participant_status() -> None:
    storage, combat_id = make_combat_with_two_participants()

    with_status = add_participant_status(storage, combat_id, "personagem:miko-meu", "caido")
    without_status = remove_participant_status(storage, combat_id, "personagem:miko-meu", "caido")

    participant = [item for item in with_status.participants if item.id == "personagem:miko-meu"][0]
    updated = [item for item in without_status.participants if item.id == "personagem:miko-meu"][0]
    assert "caido" in participant.status
    assert "caido" not in updated.status


def test_finish_combat() -> None:
    storage, combat_id = make_combat_with_two_participants()

    combat = finish_combat(storage, combat_id)

    assert combat.status == "finalizado"
    assert combat.finished_at is not None


def test_record_combat_action() -> None:
    storage = make_storage()
    combat = create_combat(storage, "Teste")

    record_combat_action(combat, "Mestre descreveu uma acao.")

    assert "Mestre descreveu uma acao." in combat.combat_history[-1]


def test_register_free_combat_action() -> None:
    storage = make_storage()
    combat = create_combat(storage, "Teste")

    updated = register_free_combat_action(storage, combat.id, "Miko observa o campo.")

    assert "Miko observa o campo." in updated.combat_history[-1]
