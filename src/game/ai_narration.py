"""Safe optional AI narration adapter for the 2D game layer.

This module prepares small PyGame contexts for the existing narrator. It never
writes saves, applies flags, grants rewards, creates quests, or changes combat.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import asdict, dataclass
from typing import Any

from src.ai.narrator import AIConfig, NarrationResult, generate_short_narration


MAX_TEXT_LENGTH = 600
MAX_FLAGS = 12
SENSITIVE_KEY_PARTS = ("key", "token", "secret", "password", "senha")
ALLOWED_CONTEXT_KEYS = {
    "location_id",
    "location_name",
    "event_id",
    "npc_id",
    "story_flags",
    "world_flags",
    "decided_consequence",
    "tone",
    "tom",
}
GAME_NARRATION_GUARDRAILS = (
    "A IA so pode melhorar ou narrar o texto local.",
    "A IA nao pode decidir dano, vida, recompensa, loot, missao, marca, magia, morte ou consequencia mecanica.",
    "A consequencia real ja foi decidida pelo Python.",
    "A IA nao pode alterar save, flags, inventario, itens, quests ou estado do jogo.",
    "A resposta deve ser curta e em portugues brasileiro.",
    "Se faltar contexto, mantenha o texto local.",
)


GameNarrator = Callable[..., Any]


@dataclass(frozen=True)
class GameNarrationResult:
    text: str
    source: str
    used_ai: bool
    diagnostic: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_safe_game_narration_context(
    context: Mapping[str, Any] | None = None,
    **overrides: Any,
) -> dict[str, Any]:
    """Return a small AI-safe context for PyGame narration."""

    raw_context = dict(context or {})
    raw_context.update(overrides)
    safe: dict[str, Any] = {
        "camada": "pygame",
        "tipo": "narracao_auxiliar",
        "limites_da_ia": list(GAME_NARRATION_GUARDRAILS),
    }
    for key in ALLOWED_CONTEXT_KEYS:
        if key not in raw_context or _is_sensitive_key(key):
            continue
        value = raw_context[key]
        if key in {"story_flags", "world_flags"}:
            flags = _safe_string_list(value, limit=MAX_FLAGS)
            if flags:
                safe[key] = flags
            continue
        cleaned = _safe_text(value)
        if cleaned:
            safe[key] = cleaned
    if "tone" in safe and "tom" not in safe:
        safe["tom"] = safe["tone"]
    fallback_text = _safe_text(raw_context.get("fallback_text"))
    if fallback_text:
        safe["texto_local"] = fallback_text
    return safe


def get_local_fallback_narration(fallback_text: str) -> GameNarrationResult:
    return GameNarrationResult(
        text=_safe_text(fallback_text),
        source="fallback",
        used_ai=False,
        diagnostic="local_fallback",
    )


def narrate_game_text(
    fallback_text: str,
    context: Mapping[str, Any] | None = None,
    *,
    config: AIConfig | None = None,
    narrator: GameNarrator | None = None,
) -> GameNarrationResult:
    """Ask the optional narrator for text, safely falling back to local text.

    The returned text is only a suggestion for display. This function does not
    receive storage and cannot mutate the game save.
    """

    local_text = _safe_text(fallback_text)
    if not local_text:
        raise ValueError("fallback_text e obrigatorio para narracao segura do jogo.")

    resolved_config = config or AIConfig.from_env()
    if not resolved_config.enabled:
        return GameNarrationResult(
            text=local_text,
            source="disabled",
            used_ai=False,
            diagnostic="disabled",
        )

    safe_context = build_safe_game_narration_context(context, fallback_text=local_text)
    try:
        result = (narrator or generate_short_narration)(safe_context, config=resolved_config)
    except Exception:
        return GameNarrationResult(
            text=local_text,
            source="error",
            used_ai=False,
            diagnostic="narrator_error",
        )

    result_source = str(getattr(result, "source", "fallback"))
    result_text = _safe_text(getattr(result, "text", ""))
    diagnostic = str(getattr(result, "diagnostic", ""))
    if result_source in {"ai", "ollama"} and result_text:
        return GameNarrationResult(
            text=result_text,
            source=result_source,
            used_ai=True,
            diagnostic=diagnostic or "ok",
        )
    return GameNarrationResult(
        text=local_text,
        source=_fallback_source_for(result_source, diagnostic),
        used_ai=False,
        diagnostic=diagnostic or result_source,
    )


def _fallback_source_for(source: str, diagnostic: str) -> str:
    if diagnostic == "disabled":
        return "disabled"
    if diagnostic in {"unknown_error", "connection_error", "ollama_error", "invalid_api_key", "billing_permission_error"}:
        return "error"
    if source == "fallback":
        return "fallback"
    return "error"


def _safe_text(value: Any, *, limit: int = MAX_TEXT_LENGTH) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if not text:
        return ""
    return text[:limit]


def _safe_string_list(value: Any, *, limit: int) -> list[str]:
    if isinstance(value, str):
        candidates = [value]
    elif isinstance(value, (list, tuple, set)):
        candidates = list(value)
    else:
        return []
    result: list[str] = []
    for item in candidates:
        cleaned = _safe_text(item, limit=80)
        if cleaned and cleaned not in result:
            result.append(cleaned)
        if len(result) >= limit:
            break
    return result


def _is_sensitive_key(key: str) -> bool:
    return any(part in key.casefold() for part in SENSITIVE_KEY_PARTS)
