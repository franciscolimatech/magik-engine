"""Turn-based combat management."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
import random
import re
from typing import Any, Protocol

from src.core.abilities import use_ability
from src.core.character import get_character, update_character
from src.core.combat import apply_magical_damage, apply_physical_damage
from src.core.creatures import get_creature, update_creature
from src.core.magic import apply_healing
from src.core.session import register_event
from src.storage.types import JsonStore


COMBAT_STATUSES = {"em_andamento", "finalizado"}
PARTICIPANT_TYPES = {"personagem", "criatura"}


class RandomLike(Protocol):
    def randint(self, a: int, b: int) -> int:
        """Return a random integer N such that a <= N <= b."""


@dataclass
class CombatParticipant:
    id: str
    name: str
    type: str
    reference_id: str
    current_health: int
    max_health: int
    armor: int
    initiative: int = 0
    status: list[str] = field(default_factory=list)
    is_alive: bool = True
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CombatParticipant":
        return cls(
            id=str(data["id"]),
            name=str(data["name"]),
            type=str(data["type"]),
            reference_id=str(data["reference_id"]),
            current_health=int(data["current_health"]),
            max_health=int(data["max_health"]),
            armor=int(data["armor"]),
            initiative=int(data.get("initiative", 0)),
            status=list(data.get("status", [])),
            is_alive=bool(data.get("is_alive", int(data["current_health"]) > 0)),
            notes=list(data.get("notes", [])),
        )


@dataclass
class Combat:
    id: str
    name: str
    status: str = "em_andamento"
    current_round: int = 1
    current_turn: int = 0
    participants: list[CombatParticipant] = field(default_factory=list)
    combat_history: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().astimezone().isoformat(timespec="seconds"))
    finished_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["participants"] = [participant.to_dict() for participant in self.participants]
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Combat":
        combat = cls(
            id=str(data["id"]),
            name=str(data["name"]),
            status=str(data.get("status", "em_andamento")),
            current_round=int(data.get("current_round", 1)),
            current_turn=int(data.get("current_turn", 0)),
            participants=[
                CombatParticipant.from_dict(participant)
                for participant in data.get("participants", [])
            ],
            combat_history=list(data.get("combat_history", [])),
            created_at=str(data.get("created_at", datetime.now().astimezone().isoformat(timespec="seconds"))),
            finished_at=data.get("finished_at"),
        )
        validate_combat(combat)
        return combat


def default_combat_data() -> dict[str, Any]:
    return {"combats": []}


def list_combats(storage: JsonStore) -> list[Combat]:
    data = storage.read_json("combats.json", default=default_combat_data())
    if isinstance(data, dict):
        combats_data = data.get("combats", [])
    elif isinstance(data, list):
        combats_data = data
    else:
        raise ValueError("combats.json deve conter uma lista ou um objeto com a chave 'combats'.")
    if not isinstance(combats_data, list):
        raise ValueError("A chave 'combats' deve conter uma lista.")
    return [Combat.from_dict(item) for item in combats_data]


def save_combats(storage: JsonStore, combats: list[Combat]) -> None:
    _ensure_unique_combat_ids(combats)
    storage.write_json("combats.json", {"combats": [combat.to_dict() for combat in combats]})


def create_combat(storage: JsonStore, name: str, combat_id: str | None = None) -> Combat:
    if not name.strip():
        raise ValueError("Nome do combate e obrigatorio.")
    combats = list_combats(storage)
    new_id = _resolve_new_id(combats, combat_id or name, explicit=combat_id is not None)
    combat = Combat(id=new_id, name=name.strip())
    combats.append(combat)
    save_combats(storage, combats)
    return combat


def get_combat(storage: JsonStore, combat_id: str) -> Combat:
    normalized = combat_id.strip().casefold()
    for combat in list_combats(storage):
        if combat.id.casefold() == normalized:
            return combat
    raise ValueError(f"Combate nao encontrado: {combat_id}.")


def update_combat(storage: JsonStore, combat: Combat) -> Combat:
    validate_combat(combat)
    combats = list_combats(storage)
    for index, current in enumerate(combats):
        if current.id.casefold() == combat.id.casefold():
            combats[index] = combat
            save_combats(storage, combats)
            return combat
    raise ValueError(f"Combate nao encontrado: {combat.id}.")


def add_character_to_combat(storage: JsonStore, combat_id: str, character_id: str) -> Combat:
    combat = get_combat(storage, combat_id)
    character = get_character(storage, character_id)
    participant = CombatParticipant(
        id=f"personagem:{character.id}",
        name=character.name,
        type="personagem",
        reference_id=character.id,
        current_health=character.current_health,
        max_health=character.max_health,
        armor=character.armor,
        status=list(character.status),
        is_alive=character.current_health > 0,
        notes=list(character.notes),
    )
    _add_participant(combat, participant)
    record_combat_action(combat, f"Personagem entrou no combate: {character.name}.")
    return update_combat(storage, combat)


def add_creature_to_combat(storage: JsonStore, combat_id: str, creature_id: str) -> Combat:
    combat = get_combat(storage, combat_id)
    creature = get_creature(storage, creature_id)
    participant = CombatParticipant(
        id=f"criatura:{creature.id}",
        name=creature.name,
        type="criatura",
        reference_id=creature.id,
        current_health=creature.current_health,
        max_health=creature.max_health,
        armor=creature.armor,
        status=list(creature.status),
        is_alive=creature.current_health > 0,
        notes=list(creature.notes),
    )
    _add_participant(combat, participant)
    record_combat_action(combat, f"Criatura entrou no combate: {creature.name}.")
    return update_combat(storage, combat)


def remove_participant(storage: JsonStore, combat_id: str, participant_id: str) -> Combat:
    combat = get_combat(storage, combat_id)
    participant = get_participant(combat, participant_id)
    combat.participants = [current for current in combat.participants if current.id != participant.id]
    if combat.current_turn >= len(combat.participants):
        combat.current_turn = 0
    record_combat_action(combat, f"Participante removido: {participant.name}.")
    return update_combat(storage, combat)


def roll_initiative(storage: JsonStore, combat_id: str, rng: RandomLike | None = None) -> Combat:
    combat = get_combat(storage, combat_id)
    roller = rng or random
    for participant in combat.participants:
        participant.initiative = roller.randint(1, 20)
    order_participants(combat)
    record_combat_action(combat, "Iniciativa rolada e ordem de turnos atualizada.")
    return update_combat(storage, combat)


def order_participants(combat: Combat) -> Combat:
    combat.participants.sort(key=lambda participant: participant.initiative, reverse=True)
    combat.current_turn = _first_living_index(combat.participants)
    return combat


def start_combat(storage: JsonStore, combat_id: str) -> Combat:
    combat = get_combat(storage, combat_id)
    if not combat.participants:
        raise ValueError("Nao e possivel iniciar combate sem participantes.")
    order_participants(combat)
    combat.status = "em_andamento"
    combat.current_round = max(combat.current_round, 1)
    record_combat_action(combat, "Combate iniciado.")
    return update_combat(storage, combat)


def get_current_participant(combat: Combat) -> CombatParticipant:
    living = [participant for participant in combat.participants if participant.is_alive and participant.current_health > 0]
    if not living:
        raise ValueError("Nao ha participantes vivos no combate.")
    if not combat.participants:
        raise ValueError("Combate sem participantes.")
    if combat.current_turn >= len(combat.participants):
        combat.current_turn = 0
    current = combat.participants[combat.current_turn]
    if current.is_alive and current.current_health > 0:
        return current
    next_index, _wrapped = _next_living_index(combat.participants, combat.current_turn)
    combat.current_turn = next_index
    return combat.participants[next_index]


def advance_turn(storage: JsonStore, combat_id: str) -> Combat:
    combat = get_combat(storage, combat_id)
    if combat.status == "finalizado":
        raise ValueError("Combate ja finalizado.")
    next_index, wrapped = _next_living_index(combat.participants, combat.current_turn)
    combat.current_turn = next_index
    if wrapped:
        combat.current_round += 1
        record_combat_action(combat, f"Rodada {combat.current_round} iniciada.")
    record_combat_action(combat, f"Turno atual: {combat.participants[combat.current_turn].name}.")
    return update_combat(storage, combat)


def advance_round(storage: JsonStore, combat_id: str) -> Combat:
    combat = get_combat(storage, combat_id)
    combat.current_round += 1
    combat.current_turn = _first_living_index(combat.participants)
    record_combat_action(combat, f"Rodada {combat.current_round} iniciada manualmente.")
    return update_combat(storage, combat)


def finish_combat(storage: JsonStore, combat_id: str) -> Combat:
    combat = get_combat(storage, combat_id)
    combat.status = "finalizado"
    combat.finished_at = datetime.now().astimezone().isoformat(timespec="seconds")
    record_combat_action(combat, "Combate finalizado pelo mestre.")
    return update_combat(storage, combat)


def apply_physical_damage_to_participant(
    storage: JsonStore,
    combat_id: str,
    participant_id: str,
    damage: int,
) -> Combat:
    combat = get_combat(storage, combat_id)
    participant = get_participant(combat, participant_id)
    result = apply_physical_damage(participant.current_health, participant.armor, damage)
    participant.current_health = result.current_health
    participant.armor = result.armor
    _refresh_alive(participant)
    _sync_participant(storage, participant)
    record_combat_action(combat, f"{participant.name} recebeu {damage} de dano fisico. {result.description}")
    _record_session(storage, participant, "Dano fisico em combate", f"{damage} de dano", result.description)
    return update_combat(storage, combat)


def apply_magical_damage_to_participant(
    storage: JsonStore,
    combat_id: str,
    participant_id: str,
    damage: int,
) -> Combat:
    combat = get_combat(storage, combat_id)
    participant = get_participant(combat, participant_id)
    result = apply_magical_damage(participant.current_health, participant.armor, damage)
    participant.current_health = result.current_health
    _refresh_alive(participant)
    _sync_participant(storage, participant)
    record_combat_action(combat, f"{participant.name} recebeu {damage} de dano magico. {result.description}")
    _record_session(storage, participant, "Dano magico em combate", f"{damage} de dano", result.description)
    return update_combat(storage, combat)


def heal_participant(storage: JsonStore, combat_id: str, participant_id: str, amount: int) -> Combat:
    combat = get_combat(storage, combat_id)
    participant = get_participant(combat, participant_id)
    result = apply_healing(participant.current_health, participant.max_health, amount)
    participant.current_health = result.current_health
    _refresh_alive(participant)
    _sync_participant(storage, participant)
    record_combat_action(combat, f"{participant.name} recebeu {amount} de cura. {result.description}")
    _record_session(storage, participant, "Cura em combate", f"{amount} de cura", result.description)
    return update_combat(storage, combat)


def add_participant_status(storage: JsonStore, combat_id: str, participant_id: str, status: str) -> Combat:
    combat = get_combat(storage, combat_id)
    participant = get_participant(combat, participant_id)
    cleaned = _required_text(status, "status")
    if cleaned not in participant.status:
        participant.status.append(cleaned)
    _sync_participant(storage, participant)
    record_combat_action(combat, f"Status adicionado a {participant.name}: {cleaned}.")
    _record_session(storage, participant, "Status em combate adicionado", cleaned)
    return update_combat(storage, combat)


def remove_participant_status(storage: JsonStore, combat_id: str, participant_id: str, status: str) -> Combat:
    combat = get_combat(storage, combat_id)
    participant = get_participant(combat, participant_id)
    cleaned = _required_text(status, "status")
    try:
        participant.status.remove(cleaned)
    except ValueError as exc:
        raise ValueError(f"Status nao encontrado: {cleaned}.") from exc
    _sync_participant(storage, participant)
    record_combat_action(combat, f"Status removido de {participant.name}: {cleaned}.")
    _record_session(storage, participant, "Status em combate removido", cleaned)
    return update_combat(storage, combat)


def use_participant_ability(storage: JsonStore, combat_id: str, participant_id: str, ability_id: str) -> Combat:
    combat = get_combat(storage, combat_id)
    participant = get_participant(combat, participant_id)
    if participant.type != "personagem":
        raise ValueError("Uso de habilidade geral em combate esta disponivel para personagens nesta etapa.")
    character = get_character(storage, participant.reference_id)
    result = use_ability(character, ability_id)
    update_character(storage, character)
    record_combat_action(combat, f"{participant.name} usou habilidade: {result.ability.name}.")
    _record_session(
        storage,
        participant,
        f"Usou habilidade em combate: {result.ability.name}",
        result.effect or "Habilidade usada.",
        f"Custo: {result.cost or 'nenhum'}. Usos restantes: {result.remaining_uses if result.remaining_uses is not None else 'livre'}.",
    )
    return update_combat(storage, combat)


def register_free_combat_action(storage: JsonStore, combat_id: str, description: str) -> Combat:
    combat = get_combat(storage, combat_id)
    cleaned = _required_text(description, "acao narrativa")
    record_combat_action(combat, cleaned)
    register_event(storage, character="Combate", action="Acao narrativa em combate", result=cleaned)
    return update_combat(storage, combat)


def record_combat_action(combat: Combat, description: str) -> Combat:
    timestamp = datetime.now().astimezone().isoformat(timespec="seconds")
    combat.combat_history.append(f"[{timestamp}] {description}")
    return combat


def get_participant(combat: Combat, participant_id: str) -> CombatParticipant:
    normalized = participant_id.strip().casefold()
    for participant in combat.participants:
        if participant.id.casefold() == normalized or participant.reference_id.casefold() == normalized:
            return participant
    raise ValueError(f"Participante nao encontrado: {participant_id}.")


def validate_combat(combat: Combat) -> None:
    if not combat.id.strip():
        raise ValueError("Id do combate e obrigatorio.")
    if not combat.name.strip():
        raise ValueError("Nome do combate e obrigatorio.")
    if combat.status not in COMBAT_STATUSES:
        raise ValueError("Status de combate invalido.")
    seen: set[str] = set()
    for participant in combat.participants:
        if participant.type not in PARTICIPANT_TYPES:
            raise ValueError("Tipo de participante invalido.")
        if participant.id in seen:
            raise ValueError(f"Participante duplicado: {participant.id}.")
        seen.add(participant.id)


def generate_combat_id(name: str) -> str:
    normalized = _normalize_ascii(name)
    slug = re.sub(r"[^a-z0-9]+", "-", normalized).strip("-")
    return slug or "combate"


def _add_participant(combat: Combat, participant: CombatParticipant) -> None:
    if any(current.id == participant.id for current in combat.participants):
        raise ValueError(f"Participante duplicado: {participant.name}.")
    combat.participants.append(participant)


def _sync_participant(storage: JsonStore, participant: CombatParticipant) -> None:
    if participant.type == "personagem":
        character = get_character(storage, participant.reference_id)
        character.current_health = participant.current_health
        character.armor = participant.armor
        character.status = list(participant.status)
        update_character(storage, character)
    elif participant.type == "criatura":
        creature = get_creature(storage, participant.reference_id)
        creature.current_health = participant.current_health
        creature.armor = participant.armor
        creature.status = list(participant.status)
        update_creature(storage, creature)


def _record_session(storage: JsonStore, participant: CombatParticipant, action: str, result: str, notes: str = "") -> None:
    register_event(storage, character=participant.name, action=action, result=result, notes=notes)


def _refresh_alive(participant: CombatParticipant) -> None:
    participant.is_alive = participant.current_health > 0


def _first_living_index(participants: list[CombatParticipant]) -> int:
    for index, participant in enumerate(participants):
        if participant.is_alive and participant.current_health > 0:
            return index
    return 0


def _next_living_index(participants: list[CombatParticipant], current_index: int) -> tuple[int, bool]:
    if not participants:
        raise ValueError("Combate sem participantes.")
    living_count = sum(1 for participant in participants if participant.is_alive and participant.current_health > 0)
    if living_count == 0:
        raise ValueError("Nao ha participantes vivos no combate.")
    index = current_index
    wrapped = False
    while True:
        index += 1
        if index >= len(participants):
            index = 0
            wrapped = True
        participant = participants[index]
        if participant.is_alive and participant.current_health > 0:
            return index, wrapped


def _resolve_new_id(combats: list[Combat], value: str, explicit: bool) -> str:
    candidate = generate_combat_id(value)
    existing = {combat.id.casefold() for combat in combats}
    if candidate.casefold() not in existing:
        return candidate
    if explicit:
        raise ValueError(f"Id de combate duplicado: {candidate}.")
    suffix = 2
    while f"{candidate}-{suffix}".casefold() in existing:
        suffix += 1
    return f"{candidate}-{suffix}"


def _ensure_unique_combat_ids(combats: list[Combat]) -> None:
    seen: set[str] = set()
    for combat in combats:
        normalized = combat.id.casefold()
        if normalized in seen:
            raise ValueError(f"Id de combate duplicado: {combat.id}.")
        seen.add(normalized)


def _required_text(value: str, field_name: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise ValueError(f"O campo {field_name} e obrigatorio.")
    return cleaned


def _normalize_ascii(value: str) -> str:
    import unicodedata

    normalized = unicodedata.normalize("NFKD", value.strip().casefold())
    return "".join(character for character in normalized if not unicodedata.combining(character))
