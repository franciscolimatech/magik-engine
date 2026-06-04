"""Character routes for the MAGIK Engine web interface."""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from urllib.parse import quote

from src.core.abilities import (
    ABILITY_TYPES,
    ABILITY_USES,
    Ability,
    add_ability,
    get_ability,
    list_abilities,
    remove_ability,
    update_ability,
    validate_ability,
)
from src.core.character import (
    Character,
    add_equipment,
    create_character,
    generate_character_id,
    get_character,
    list_characters,
    remove_character,
    remove_equipment,
    update_character,
    update_character_health,
)


router = APIRouter(prefix="/characters", tags=["characters"])


@router.get("")
def character_list(request: Request):
    characters = list_characters(request.app.state.storage)
    character_cards = [_character_card_view(character) for character in characters]
    return request.app.state.templates.TemplateResponse(
        request,
        "characters/list.html",
        {
            "request": request,
            "title": "Personagens",
            "characters": characters,
            "character_cards": character_cards,
        },
    )


@router.get("/new")
def character_create_form(request: Request):
    return _render_create_form(request)


@router.post("/new")
async def character_create(request: Request):
    form = await request.form()
    data = _clean_form(form)
    try:
        character = _save_character_from_form(request, data)
    except ValueError as error:
        return _render_create_form(request, error=str(error), form=data, status_code=400)

    return RedirectResponse(url=f"/characters/{character.id}", status_code=303)


@router.post("/preview")
async def character_preview(request: Request):
    form = await request.form()
    data = _clean_form(form)
    try:
        preview = _build_character_preview(data)
    except ValueError as error:
        return _render_create_form(request, error=str(error), form=data, status_code=400)

    return request.app.state.templates.TemplateResponse(
        request,
        "characters/preview.html",
        {
            "request": request,
            "title": "Revisar personagem",
            "form": data,
            "character": preview,
            "ability_slots": ABILITY_SLOTS,
        },
    )


@router.post("/confirm")
async def character_confirm(request: Request):
    form = await request.form()
    data = _clean_form(form)
    try:
        character = _save_character_from_form(request, data)
    except ValueError as error:
        return _render_create_form(request, error=str(error), form=data, status_code=400)

    return RedirectResponse(url=f"/characters/{character.id}", status_code=303)


@router.get("/{character_id}/edit")
def character_edit_form(request: Request, character_id: str):
    try:
        character = get_character(request.app.state.storage, character_id)
    except ValueError as error:
        return _render_not_found(request, str(error))
    return _render_edit_form(request, character)


@router.post("/{character_id}/edit")
async def character_edit(request: Request, character_id: str):
    form = await request.form()
    data = _clean_form(form)
    try:
        character = get_character(request.app.state.storage, character_id)
        character = _update_character_from_edit_form(request, character, data)
    except ValueError as error:
        try:
            character = get_character(request.app.state.storage, character_id)
        except ValueError:
            return _render_not_found(request, str(error))
        return _render_edit_form(request, character, error=str(error), form=data, status_code=400)

    return RedirectResponse(url=f"/characters/{character.id}?success=character-updated", status_code=303)


@router.post("/{character_id}/equipment/add")
async def character_equipment_add(request: Request, character_id: str):
    form = await request.form()
    data = _clean_form(form)
    try:
        add_equipment(request.app.state.storage, character_id, data.get("equipment_item", ""))
    except ValueError as error:
        return RedirectResponse(url=f"/characters/{character_id}/edit?error={quote(str(error))}", status_code=303)
    return RedirectResponse(url=f"/characters/{character_id}/edit?success=equipment-added", status_code=303)


@router.post("/{character_id}/equipment/remove")
async def character_equipment_remove(request: Request, character_id: str):
    form = await request.form()
    data = _clean_form(form)
    try:
        remove_equipment(request.app.state.storage, character_id, data.get("equipment_item", ""))
    except ValueError as error:
        return RedirectResponse(url=f"/characters/{character_id}/edit?error={quote(str(error))}", status_code=303)
    return RedirectResponse(url=f"/characters/{character_id}/edit?success=equipment-removed", status_code=303)


@router.post("/{character_id}/status/add")
async def character_status_add(request: Request, character_id: str):
    form = await request.form()
    data = _clean_form(form)
    try:
        character = get_character(request.app.state.storage, character_id)
        status = data.get("status_item", "").strip()
        if not status:
            raise ValueError("Status nao pode ser vazio.")
        if status not in character.status:
            character.status.append(status)
            update_character(request.app.state.storage, character)
    except ValueError as error:
        return RedirectResponse(url=f"/characters/{character_id}/edit?error={quote(str(error))}", status_code=303)
    return RedirectResponse(url=f"/characters/{character_id}/edit?success=status-added", status_code=303)


@router.post("/{character_id}/status/remove")
async def character_status_remove(request: Request, character_id: str):
    form = await request.form()
    data = _clean_form(form)
    try:
        character = get_character(request.app.state.storage, character_id)
        status = data.get("status_item", "").strip()
        if status not in character.status:
            raise ValueError(f"Status nao encontrado: {status}.")
        character.status.remove(status)
        update_character(request.app.state.storage, character)
    except ValueError as error:
        return RedirectResponse(url=f"/characters/{character_id}/edit?error={quote(str(error))}", status_code=303)
    return RedirectResponse(url=f"/characters/{character_id}/edit?success=status-removed", status_code=303)


@router.get("/{character_id}/abilities")
def character_abilities_form(request: Request, character_id: str):
    try:
        character = get_character(request.app.state.storage, character_id)
    except ValueError as error:
        return _render_not_found(request, str(error))
    return _render_abilities_form(request, character)


@router.post("/{character_id}/abilities/add")
async def character_ability_add(request: Request, character_id: str):
    form = await request.form()
    data = _clean_form(form)
    try:
        character = get_character(request.app.state.storage, character_id)
        ability = _parse_ability_edit_form(data, existing_ids={item.id for item in list_abilities(character)})
        update_character(request.app.state.storage, add_ability(character, ability))
    except ValueError as error:
        character = get_character(request.app.state.storage, character_id)
        return _render_abilities_form(request, character, error=str(error), form=data, status_code=400)
    return RedirectResponse(url=f"/characters/{character_id}/abilities?success=ability-added", status_code=303)


@router.post("/{character_id}/abilities/{ability_id}/edit")
async def character_ability_edit(request: Request, character_id: str, ability_id: str):
    form = await request.form()
    data = _clean_form(form)
    try:
        character = get_character(request.app.state.storage, character_id)
        ability = _parse_ability_edit_form(data, ability_id=ability_id)
        update_character(request.app.state.storage, update_ability(character, ability))
    except ValueError as error:
        character = get_character(request.app.state.storage, character_id)
        return _render_abilities_form(request, character, error=str(error), form=data, status_code=400)
    return RedirectResponse(url=f"/characters/{character_id}/abilities?success=ability-updated", status_code=303)


@router.post("/{character_id}/abilities/{ability_id}/remove")
def character_ability_remove(request: Request, character_id: str, ability_id: str):
    try:
        character = get_character(request.app.state.storage, character_id)
        update_character(request.app.state.storage, remove_ability(character, ability_id))
    except ValueError as error:
        return RedirectResponse(url=f"/characters/{character_id}/abilities?error={quote(str(error))}", status_code=303)
    return RedirectResponse(url=f"/characters/{character_id}/abilities?success=ability-removed", status_code=303)


@router.post("/{character_id}/abilities/{ability_id}/restore")
def character_ability_restore(request: Request, character_id: str, ability_id: str):
    try:
        character = get_character(request.app.state.storage, character_id)
        ability = get_ability(character, ability_id)
        if ability.usage_limit is None:
            raise ValueError("Habilidade nao possui limite de uso para restaurar.")
        ability.remaining_uses = ability.usage_limit
        update_character(request.app.state.storage, update_ability(character, ability))
    except ValueError as error:
        return RedirectResponse(url=f"/characters/{character_id}/abilities?error={quote(str(error))}", status_code=303)
    return RedirectResponse(url=f"/characters/{character_id}/abilities?success=ability-restored", status_code=303)


@router.get("/{character_id}")
def character_detail(request: Request, character_id: str):
    try:
        character = get_character(request.app.state.storage, character_id)
    except ValueError as error:
        return _render_not_found(request, str(error))
    return request.app.state.templates.TemplateResponse(
        request,
        "characters/detail.html",
        {
            "request": request,
            "title": character.name,
            "character": character,
            "view": _character_sheet_view(character),
            "error": "",
            "message": _message_from_query(request),
        },
    )


def _render_create_form(
    request: Request,
    error: str = "",
    form: dict[str, str] | None = None,
    status_code: int = 200,
):
    return request.app.state.templates.TemplateResponse(
        request,
        "characters/create.html",
        {
            "request": request,
            "title": "Criar personagem",
            "error": error,
            "form": form or {},
            "ability_slots": ABILITY_SLOTS,
            "ability_types": sorted(ABILITY_TYPES),
            "ability_uses": sorted(ABILITY_USES),
        },
        status_code=status_code,
    )


def _render_not_found(request: Request, error: str):
    return request.app.state.templates.TemplateResponse(
        request,
        "characters/detail.html",
        {
            "request": request,
            "title": "Personagem nao encontrado",
            "character": None,
            "error": error,
            "message": {},
        },
        status_code=404,
    )


def _render_edit_form(
    request: Request,
    character: Character,
    error: str = "",
    form: dict[str, str] | None = None,
    status_code: int = 200,
):
    return request.app.state.templates.TemplateResponse(
        request,
        "characters/edit.html",
        {
            "request": request,
            "title": f"Editar {character.name}",
            "character": character,
            "form": form or _character_edit_form_data(character),
            "error": error or _message_from_query(request).get("error", ""),
            "success": _message_from_query(request).get("success", ""),
        },
        status_code=status_code,
    )


def _render_abilities_form(
    request: Request,
    character: Character,
    error: str = "",
    form: dict[str, str] | None = None,
    status_code: int = 200,
):
    return request.app.state.templates.TemplateResponse(
        request,
        "characters/abilities.html",
        {
            "request": request,
            "title": f"Habilidades de {character.name}",
            "character": character,
            "abilities": list_abilities(character),
            "form": form or {},
            "ability_types": sorted(ABILITY_TYPES),
            "ability_uses": sorted(ABILITY_USES),
            "error": error or _message_from_query(request).get("error", ""),
            "success": _message_from_query(request).get("success", ""),
        },
        status_code=status_code,
    )


ABILITY_SLOTS = (1, 2, 3)
NOTE_LABELS = {
    "Descricao": "description",
    "Historia": "history",
    "Personalidade": "personality",
    "Frases marcantes": "catchphrases",
    "Observacoes": "general",
}
SPECIAL_SYSTEM_LABELS = {
    "ikisaki": "Ikisaki",
    "shadow_staff": "Cajado Sombrio",
}
SPECIAL_ABILITY_LABELS = {
    "shadow_switch": "Switch Sombrio",
}
SUCCESS_MESSAGES = {
    "character-updated": "Personagem atualizado.",
    "equipment-added": "Equipamento adicionado.",
    "equipment-removed": "Equipamento removido.",
    "status-added": "Status adicionado.",
    "status-removed": "Status removido.",
    "ability-added": "Habilidade adicionada.",
    "ability-updated": "Habilidade atualizada.",
    "ability-removed": "Habilidade removida.",
    "ability-restored": "Usos da habilidade restaurados.",
}


def _character_card_view(character: Character) -> dict:
    return {
        "character": character,
        "health_percent": _health_percent(character),
        "armor_percent": _armor_percent(character.armor),
    }


def _character_sheet_view(character: Character) -> dict:
    return {
        "health_percent": _health_percent(character),
        "armor_percent": _armor_percent(character.armor),
        "notes": _split_character_notes(character.notes),
        "special_systems": _special_systems_for_display(character),
    }


def _health_percent(character: Character) -> int:
    if character.max_health <= 0:
        return 0
    percent = round((character.current_health / character.max_health) * 100)
    return max(0, min(100, percent))


def _armor_percent(armor: int) -> int:
    return max(0, min(100, armor * 10))


def _split_character_notes(notes: list[str]) -> dict[str, list[str]]:
    grouped = {
        "description": [],
        "history": [],
        "personality": [],
        "catchphrases": [],
        "general": [],
    }
    for note in notes:
        label, separator, value = note.partition(":")
        key = NOTE_LABELS.get(label.strip()) if separator else None
        if key and value.strip():
            grouped[key].append(value.strip())
        else:
            grouped["general"].append(note)
    return grouped


def _special_systems_for_display(character: Character) -> list[str]:
    systems: list[str] = []
    for system_id in character.special_systems:
        systems.append(SPECIAL_SYSTEM_LABELS.get(system_id, system_id))
    if character.living_weapon:
        systems.append(f"Arma viva: {character.living_weapon}")
    for ability in character.abilities:
        ability_id = str(ability.get("id", ""))
        if ability_id in SPECIAL_ABILITY_LABELS:
            systems.append(SPECIAL_ABILITY_LABELS[ability_id])
    return _unique_values(systems)


def _unique_values(values: list[str]) -> list[str]:
    unique: list[str] = []
    seen: set[str] = set()
    for value in values:
        normalized = value.casefold()
        if normalized not in seen:
            unique.append(value)
            seen.add(normalized)
    return unique


def _message_from_query(request: Request) -> dict[str, str]:
    success_key = request.query_params.get("success", "")
    error = request.query_params.get("error", "")
    return {
        "success": SUCCESS_MESSAGES.get(success_key, ""),
        "error": error,
    }


def _character_edit_form_data(character: Character) -> dict[str, str]:
    return {
        "name": character.name,
        "character_class": character.character_class,
        "max_health": str(character.max_health),
        "current_health": str(character.current_health),
        "armor": str(character.armor),
        "tags": ", ".join(character.tags),
        "equipment": ", ".join(character.equipment),
        "status": ", ".join(character.status),
        "notes": "\n".join(character.notes),
    }


def _update_character_from_edit_form(request: Request, character: Character, data: dict[str, str]) -> Character:
    parsed = _parse_character_edit_form(data)
    character.name = parsed["name"]
    character.character_class = parsed["character_class"]
    character.max_health = parsed["max_health"]
    character.current_health = parsed["current_health"]
    character.armor = parsed["armor"]
    character.tags = parsed["tags"]
    character.equipment = parsed["equipment"]
    character.status = parsed["status"]
    character.notes = parsed["notes"]
    return update_character(request.app.state.storage, character)


def _parse_character_edit_form(data: dict[str, str]) -> dict:
    name = data.get("name", "").strip()
    character_class = data.get("character_class", "").strip()
    if not name:
        raise ValueError("Nome do personagem e obrigatorio.")
    if not character_class:
        raise ValueError("Classe do personagem e obrigatoria.")

    max_health = _parse_int(data.get("max_health", ""), "Vida maxima")
    current_health = _parse_int(data.get("current_health", ""), "Vida atual")
    armor = _parse_int(data.get("armor", "0") or "0", "Armadura")
    if max_health <= 0:
        raise ValueError("Vida maxima deve ser maior que zero.")
    if current_health < 0:
        raise ValueError("Vida atual nao pode ser negativa.")
    if current_health > max_health:
        raise ValueError("Vida atual nao pode ultrapassar a vida maxima.")
    if armor < 0:
        raise ValueError("Armadura nao pode ser negativa.")

    return {
        "name": name,
        "character_class": character_class,
        "max_health": max_health,
        "current_health": current_health,
        "armor": armor,
        "tags": _split_csv(data.get("tags", "")),
        "equipment": _split_csv(data.get("equipment", "")),
        "status": _split_csv(data.get("status", "")),
        "notes": _split_lines(data.get("notes", "")),
    }


def _clean_form(form) -> dict[str, str]:
    return {key: str(value).strip() for key, value in form.items()}


def _build_character_preview(data: dict[str, str]) -> Character:
    parsed = _parse_character_form(data)
    return Character(
        id=generate_character_id(parsed["name"]),
        name=parsed["name"],
        character_class=parsed["character_class"],
        max_health=parsed["max_health"],
        current_health=parsed["current_health"],
        armor=parsed["armor"],
        equipment=parsed["equipment"],
        abilities=[ability.to_dict() for ability in parsed["abilities"]],
        notes=parsed["notes"],
        tags=parsed["tags"],
    )


def _save_character_from_form(request: Request, data: dict[str, str]) -> Character:
    parsed = _parse_character_form(data)
    character = create_character(
        request.app.state.storage,
        name=parsed["name"],
        character_class=parsed["character_class"],
        max_health=parsed["max_health"],
        armor=parsed["armor"],
        equipment=parsed["equipment"],
        notes=parsed["notes"],
        tags=parsed["tags"],
        abilities=[ability.to_dict() for ability in parsed["abilities"]],
    )
    try:
        if parsed["current_health"] != character.max_health:
            character = update_character_health(request.app.state.storage, character.id, parsed["current_health"])
    except ValueError:
        remove_character(request.app.state.storage, character.id, confirm=True)
        raise
    return character


def _parse_character_form(data: dict[str, str]) -> dict:
    name = data.get("name", "").strip()
    character_class = data.get("character_class", "").strip()
    if not name:
        raise ValueError("Nome do personagem e obrigatorio.")
    if not character_class:
        raise ValueError("Classe do personagem e obrigatoria.")

    max_health = _parse_int(data.get("max_health", ""), "Vida maxima")
    current_health_text = data.get("current_health", "")
    current_health = _parse_int(current_health_text, "Vida atual") if current_health_text else max_health
    armor = _parse_int(data.get("armor", "0") or "0", "Armadura")

    if max_health <= 0:
        raise ValueError("Vida maxima deve ser maior que zero.")
    if current_health < 0:
        raise ValueError("Vida atual nao pode ser negativa.")
    if current_health > max_health:
        raise ValueError("Vida atual nao pode ultrapassar a vida maxima.")
    if armor < 0:
        raise ValueError("Armadura nao pode ser negativa.")

    return {
        "name": name,
        "character_class": character_class,
        "max_health": max_health,
        "current_health": current_health,
        "armor": armor,
        "equipment": _split_csv(data.get("equipment", "")),
        "tags": _split_csv(data.get("tags", "")),
        "notes": _build_notes(data),
        "abilities": _parse_abilities(data),
    }


def _parse_abilities(data: dict[str, str]) -> list[Ability]:
    abilities: list[Ability] = []
    used_ids: set[str] = set()
    for slot in ABILITY_SLOTS:
        fields = {
            "name": data.get(f"ability_name_{slot}", ""),
            "description": data.get(f"ability_description_{slot}", ""),
            "type": data.get(f"ability_type_{slot}", "utilidade") or "utilidade",
            "use": data.get(f"ability_use_{slot}", "livre") or "livre",
            "effect": data.get(f"ability_effect_{slot}", ""),
            "cost": data.get(f"ability_cost_{slot}", ""),
            "usage_limit": data.get(f"ability_usage_limit_{slot}", ""),
            "requires_test": data.get(f"ability_requires_test_{slot}", ""),
            "suggested_test": data.get(f"ability_suggested_test_{slot}", ""),
            "notes": data.get(f"ability_notes_{slot}", ""),
        }
        if not _has_ability_content(fields):
            continue
        if not fields["name"].strip():
            raise ValueError(f"Nome da habilidade {slot} e obrigatorio quando a habilidade tem dados.")

        usage_limit = _parse_optional_int(fields["usage_limit"], f"Limite de uso da habilidade {slot}")
        ability_id = _unique_ability_id(fields["name"], used_ids)
        ability = Ability(
            id=ability_id,
            name=fields["name"].strip(),
            description=fields["description"].strip(),
            type=fields["type"].strip(),
            use=fields["use"].strip(),
            effect=fields["effect"].strip(),
            cost=fields["cost"].strip(),
            usage_limit=usage_limit,
            remaining_uses=usage_limit,
            requires_test=_parse_bool(fields["requires_test"]),
            suggested_test=fields["suggested_test"].strip() or None,
            notes=fields["notes"].strip(),
        )
        validate_ability(ability)
        abilities.append(ability)
    return abilities


def _parse_ability_edit_form(
    data: dict[str, str],
    ability_id: str | None = None,
    existing_ids: set[str] | None = None,
) -> Ability:
    name = data.get("name", "").strip()
    if not name:
        raise ValueError("Nome da habilidade e obrigatorio.")

    usage_limit = _parse_optional_int(data.get("usage_limit", ""), "Limite de uso")
    remaining_text = data.get("remaining_uses", "")
    remaining_uses = _parse_optional_int(remaining_text, "Usos restantes") if remaining_text else usage_limit
    if ability_id is None:
        generated_id = _unique_ability_id(name, {item.casefold() for item in existing_ids or set()})
    else:
        generated_id = ability_id

    ability = Ability(
        id=generated_id,
        name=name,
        description=data.get("description", "").strip(),
        type=data.get("type", "utilidade").strip() or "utilidade",
        use=data.get("use", "livre").strip() or "livre",
        effect=data.get("effect", "").strip(),
        cost=data.get("cost", "").strip(),
        usage_limit=usage_limit,
        remaining_uses=remaining_uses,
        requires_test=_parse_bool(data.get("requires_test", "")),
        suggested_test=data.get("suggested_test", "").strip() or None,
        notes=data.get("notes", "").strip(),
    )
    validate_ability(ability)
    return ability


def _has_ability_content(fields: dict[str, str]) -> bool:
    ignored_defaults = {"type": "utilidade", "use": "livre"}
    for key, value in fields.items():
        cleaned = value.strip()
        if key in ignored_defaults and cleaned == ignored_defaults[key]:
            continue
        if cleaned:
            return True
    return False


def _build_notes(data: dict[str, str]) -> list[str]:
    raw_note = data.get("notes", "").strip()
    has_story_fields = any(
        data.get(field, "").strip()
        for field in ("short_description", "history", "personality", "catchphrases")
    )
    if raw_note and not has_story_fields:
        return [raw_note]

    notes: list[str] = []
    for field, label in (
        ("short_description", "Descricao"),
        ("history", "Historia"),
        ("personality", "Personalidade"),
        ("catchphrases", "Frases marcantes"),
        ("notes", "Observacoes"),
    ):
        value = data.get(field, "").strip()
        if value:
            notes.append(f"{label}: {value}")
    return notes


def _unique_ability_id(name: str, used_ids: set[str]) -> str:
    base_id = generate_character_id(name)
    ability_id = base_id
    suffix = 2
    while ability_id.casefold() in used_ids:
        ability_id = f"{base_id}-{suffix}"
        suffix += 1
    used_ids.add(ability_id.casefold())
    return ability_id


def _parse_int(value: str, label: str) -> int:
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"{label} deve ser um numero inteiro.") from exc


def _parse_optional_int(value: str, label: str) -> int | None:
    if not value.strip():
        return None
    parsed = _parse_int(value, label)
    if parsed < 0:
        raise ValueError(f"{label} nao pode ser negativo.")
    return parsed


def _parse_bool(value: str) -> bool:
    return value.strip().casefold() in {"1", "true", "on", "s", "sim", "yes"}


def _split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def _split_lines(value: str) -> list[str]:
    return [line.strip() for line in value.splitlines() if line.strip()]
