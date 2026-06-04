"""Character routes for the MAGIK Engine web interface."""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

from src.core.abilities import ABILITY_TYPES, ABILITY_USES, Ability, validate_ability
from src.core.character import (
    Character,
    create_character,
    generate_character_id,
    get_character,
    list_characters,
    remove_character,
    update_character_health,
)


router = APIRouter(prefix="/characters", tags=["characters"])


@router.get("")
def character_list(request: Request):
    characters = list_characters(request.app.state.storage)
    return request.app.state.templates.TemplateResponse(
        request,
        "characters/list.html",
        {
            "request": request,
            "title": "Personagens",
            "characters": characters,
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


@router.get("/{character_id}")
def character_detail(request: Request, character_id: str):
    try:
        character = get_character(request.app.state.storage, character_id)
    except ValueError as error:
        return request.app.state.templates.TemplateResponse(
            request,
            "characters/detail.html",
            {
                "request": request,
                "title": "Personagem nao encontrado",
                "character": None,
                "error": str(error),
            },
            status_code=404,
        )
    return request.app.state.templates.TemplateResponse(
        request,
        "characters/detail.html",
        {
            "request": request,
            "title": character.name,
            "character": character,
            "error": "",
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


ABILITY_SLOTS = (1, 2, 3)


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
