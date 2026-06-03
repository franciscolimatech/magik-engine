"""Character routes for the MAGIK Engine web interface."""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

from src.core.character import (
    create_character,
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
    data = {key: str(value).strip() for key, value in form.items()}
    try:
        max_health = int(data.get("max_health", "0"))
        current_health_text = data.get("current_health", "")
        current_health = int(current_health_text) if current_health_text else max_health
        armor = int(data.get("armor", "0") or "0")
        character = create_character(
            request.app.state.storage,
            name=data.get("name", ""),
            character_class=data.get("character_class", ""),
            max_health=max_health,
            armor=armor,
            equipment=_split_csv(data.get("equipment", "")),
            notes=_notes_from_text(data.get("notes", "")),
            tags=_split_csv(data.get("tags", "")),
        )
        try:
            if current_health != character.max_health:
                character = update_character_health(request.app.state.storage, character.id, current_health)
        except ValueError:
            remove_character(request.app.state.storage, character.id, confirm=True)
            raise
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
        },
        status_code=status_code,
    )


def _split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def _notes_from_text(value: str) -> list[str]:
    cleaned = value.strip()
    return [cleaned] if cleaned else []
