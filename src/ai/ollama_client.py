"""Stdlib-only client for local Ollama narration."""

from __future__ import annotations

import json
import os
from typing import Any
from urllib import request
from urllib.error import URLError


DEFAULT_OLLAMA_URL = "http://localhost:11434"
DEFAULT_OLLAMA_MODEL = "llama3.2:3b"
OLLAMA_TIMEOUT_SECONDS = 2


def get_ollama_model(env: dict[str, str] | None = None) -> str:
    values = env or os.environ
    return values.get("OLLAMA_MODEL", DEFAULT_OLLAMA_MODEL).strip() or DEFAULT_OLLAMA_MODEL


def get_ollama_url(env: dict[str, str] | None = None) -> str:
    values = env or os.environ
    return values.get("OLLAMA_URL", DEFAULT_OLLAMA_URL).strip().rstrip("/") or DEFAULT_OLLAMA_URL


def is_ollama_available() -> bool:
    status = get_ollama_status()
    return bool(status["available"])


def get_ollama_status() -> dict[str, Any]:
    model = get_ollama_model()
    url = get_ollama_url()
    try:
        with request.urlopen(f"{url}/api/tags", timeout=OLLAMA_TIMEOUT_SECONDS) as response:
            response.read()
    except (OSError, URLError, TimeoutError):
        return {
            "available": False,
            "model": model,
            "url": url,
            "reason": "Ollama não respondeu em localhost:11434. Tentando próxima opção.",
        }
    return {
        "available": True,
        "model": model,
        "url": url,
        "reason": f"Ollama local disponível usando modelo {model}.",
    }


def generate_with_ollama(prompt: str, model: str | None = None) -> str:
    resolved_model = model or get_ollama_model()
    url = get_ollama_url()
    payload = json.dumps(
        {
            "model": resolved_model,
            "prompt": prompt,
            "stream": False,
        }
    ).encode("utf-8")
    http_request = request.Request(
        f"{url}/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with request.urlopen(http_request, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))
    except (OSError, URLError, TimeoutError) as exc:
        raise RuntimeError("Falha ao chamar Ollama local.") from exc

    text = data.get("response")
    if isinstance(text, str) and text.strip():
        return text.strip()
    raise RuntimeError("Resposta do Ollama veio vazia ou em formato inesperado.")
