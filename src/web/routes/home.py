"""Home routes for the MAGIK Engine web interface."""

from __future__ import annotations

from fastapi import APIRouter, Request


router = APIRouter()


@router.get("/")
def home(request: Request):
    return request.app.state.templates.TemplateResponse(
        request,
        "home.html",
        {
            "request": request,
            "title": "MAGIK Engine",
        },
    )
