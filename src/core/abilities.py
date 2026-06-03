"""General character ability model and helpers."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


ABILITY_TYPES = {
    "ataque",
    "defesa",
    "suporte",
    "cura",
    "magia",
    "controle",
    "utilidade",
    "transformacao",
    "passiva",
    "unica",
}

ABILITY_USES = {
    "livre",
    "1 vez por combate",
    "1 vez por sessao",
    "limitado",
    "passivo",
}


@dataclass
class Ability:
    id: str
    name: str
    description: str = ""
    type: str = "utilidade"
    use: str = "livre"
    effect: str = ""
    cost: str = ""
    usage_limit: int | None = None
    remaining_uses: int | None = None
    requires_test: bool = False
    suggested_test: str | None = None
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Ability":
        try:
            payload = {
                "id": str(data["id"]),
                "name": str(data["name"]),
                "description": str(data.get("description", data.get("descrição", ""))),
                "type": str(data.get("type", data.get("tipo", "utilidade"))),
                "use": str(data.get("use", data.get("uso", "livre"))),
                "effect": str(data.get("effect", data.get("efeito", ""))),
                "cost": str(data.get("cost", data.get("custo", ""))),
                "usage_limit": data.get("usage_limit", data.get("limite_de_uso")),
                "remaining_uses": data.get("remaining_uses", data.get("usos_restantes")),
                "requires_test": bool(data.get("requires_test", data.get("exige_teste", False))),
                "suggested_test": data.get("suggested_test", data.get("teste_sugerido")),
                "notes": str(data.get("notes", data.get("observações", data.get("observacoes", "")))),
            }
        except KeyError as exc:
            raise ValueError(f"Habilidade invalida: campo ausente {exc}.") from exc

        ability = cls(**payload)
        validate_ability(ability)
        return ability


@dataclass(frozen=True)
class AbilityUseResult:
    ability: Ability
    effect: str
    cost: str
    remaining_uses: int | None
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "ability": self.ability.to_dict(),
            "effect": self.effect,
            "cost": self.cost,
            "remaining_uses": self.remaining_uses,
            "notes": self.notes,
        }


def validate_ability(ability: Ability) -> None:
    if not ability.id.strip():
        raise ValueError("Id da habilidade e obrigatorio.")
    if not ability.name.strip():
        raise ValueError("Nome da habilidade e obrigatorio.")
    if ability.type not in ABILITY_TYPES:
        valid = ", ".join(sorted(ABILITY_TYPES))
        raise ValueError(f"Tipo de habilidade invalido. Use um destes: {valid}.")
    if ability.use not in ABILITY_USES:
        valid = ", ".join(sorted(ABILITY_USES))
        raise ValueError(f"Uso de habilidade invalido. Use um destes: {valid}.")
    if ability.usage_limit is not None and ability.usage_limit < 0:
        raise ValueError("Limite de uso nao pode ser negativo.")
    if ability.remaining_uses is not None and ability.remaining_uses < 0:
        raise ValueError("Usos restantes nao podem ser negativos.")


def list_abilities(character: Any) -> list[Ability]:
    return [_coerce_ability(ability) for ability in character.abilities]


def get_ability(character: Any, ability_id: str) -> Ability:
    normalized = ability_id.strip().casefold()
    for ability in list_abilities(character):
        if ability.id.casefold() == normalized:
            return ability
    raise ValueError(f"Habilidade nao encontrada: {ability_id}.")


def add_ability(character: Any, ability: Ability | dict[str, Any]) -> Any:
    new_ability = _coerce_ability(ability)
    if any(current.id.casefold() == new_ability.id.casefold() for current in list_abilities(character)):
        raise ValueError(f"Habilidade duplicada: {new_ability.id}.")
    character.abilities.append(new_ability.to_dict())
    return character


def update_ability(character: Any, ability: Ability | dict[str, Any]) -> Any:
    updated = _coerce_ability(ability)
    for index, current in enumerate(list_abilities(character)):
        if current.id.casefold() == updated.id.casefold():
            character.abilities[index] = updated.to_dict()
            return character
    raise ValueError(f"Habilidade nao encontrada: {updated.id}.")


def remove_ability(character: Any, ability_id: str) -> Any:
    ability = get_ability(character, ability_id)
    character.abilities = [
        current.to_dict()
        for current in list_abilities(character)
        if current.id.casefold() != ability.id.casefold()
    ]
    return character


def use_ability(character: Any, ability_id: str) -> AbilityUseResult:
    ability = get_ability(character, ability_id)
    if ability.use == "passivo":
        return AbilityUseResult(
            ability=ability,
            effect=ability.effect,
            cost=ability.cost,
            remaining_uses=ability.remaining_uses,
            notes="Habilidade passiva consultada; nenhum uso foi consumido.",
        )
    if ability.remaining_uses is not None:
        if ability.remaining_uses <= 0:
            raise ValueError(f"Habilidade sem usos restantes: {ability.name}.")
        ability.remaining_uses -= 1
        update_ability(character, ability)
    return AbilityUseResult(
        ability=ability,
        effect=ability.effect,
        cost=ability.cost,
        remaining_uses=ability.remaining_uses,
        notes=ability.notes,
    )


def restore_ability_uses(character: Any, scope: str = "sessao") -> Any:
    normalized_scope = scope.strip().casefold()
    restored: list[dict[str, Any]] = []
    for ability in list_abilities(character):
        should_restore = (
            ability.use == "limitado"
            or normalized_scope == "todos"
            or (normalized_scope == "combate" and ability.use == "1 vez por combate")
            or (normalized_scope == "sessao" and ability.use == "1 vez por sessao")
        )
        if should_restore and ability.usage_limit is not None:
            ability.remaining_uses = ability.usage_limit
        restored.append(ability.to_dict())
    character.abilities = restored
    return character


def _coerce_ability(ability: Ability | dict[str, Any]) -> Ability:
    if isinstance(ability, Ability):
        validate_ability(ability)
        return ability
    if isinstance(ability, dict):
        return Ability.from_dict(ability)
    raise ValueError("Habilidade deve ser Ability ou dict.")
