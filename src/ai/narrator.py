"""Optional AI narrator layer with local fallback."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import os
from types import SimpleNamespace
from typing import Any, Mapping, Protocol
from urllib import request
from urllib.error import HTTPError, URLError

from src.ai.prompts import build_prompt
from src.systems.narrative import (
    generate_narrative_consequence,
    generate_random_event,
    generate_rumor,
    narrate_ikisaki_roulette,
    normalize_tone,
)


@dataclass(frozen=True)
class AIConfig:
    enabled: bool
    api_key: str | None
    model: str = "gpt-4o-mini"

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> "AIConfig":
        values = env or os.environ
        enabled_text = values.get("MAGIK_AI_ENABLED", "true").strip().casefold()
        enabled = enabled_text not in {"0", "false", "nao", "no", "off"}
        return cls(
            enabled=enabled,
            api_key=values.get("OPENAI_API_KEY"),
            model=values.get("OPENAI_MODEL", "gpt-4o-mini"),
        )


@dataclass(frozen=True)
class NarrationResult:
    source: str
    text: str
    should_register: bool = False
    diagnostic: str = "ok"
    message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class AIClient(Protocol):
    def complete(self, prompt: str, config: AIConfig) -> str:
        """Return AI-generated text for a prompt."""


class OpenAIResponsesClient:
    """Tiny stdlib-only client for optional narration."""

    endpoint = "https://api.openai.com/v1/responses"

    def complete(self, prompt: str, config: AIConfig) -> str:
        if not config.api_key:
            raise RuntimeError("OPENAI_API_KEY nao configurada.")
        payload = json.dumps(
            {
                "model": config.model,
                "input": prompt,
                "max_output_tokens": 300,
            }
        ).encode("utf-8")
        http_request = request.Request(
            self.endpoint,
            data=payload,
            headers={
                "Authorization": f"Bearer {config.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with request.urlopen(http_request, timeout=20) as response:
                data = json.loads(response.read().decode("utf-8"))
        except URLError as exc:
            raise RuntimeError("Falha ao chamar IA Narradora Auxiliar.") from exc

        text = data.get("output_text")
        if isinstance(text, str) and text.strip():
            return text.strip()
        for item in data.get("output", []):
            for content in item.get("content", []):
                if content.get("type") in {"output_text", "text"} and content.get("text"):
                    return str(content["text"]).strip()
        raise RuntimeError("Resposta da IA veio vazia ou em formato inesperado.")


def is_ai_available(config: AIConfig | None = None) -> bool:
    resolved = config or AIConfig.from_env()
    return bool(resolved.enabled and resolved.api_key)


def check_ai_status(config: AIConfig | None = None) -> dict[str, str | bool]:
    resolved = config or AIConfig.from_env()
    if not resolved.enabled:
        return {"available": False, "reason": "IA desativada por MAGIK_AI_ENABLED."}
    if not resolved.api_key:
        return {"available": False, "reason": "OPENAI_API_KEY nao configurada; fallback local ativo."}
    return {"available": True, "reason": "IA configurada por variavel de ambiente."}


def run_quick_ai_test(
    client: AIClient | None = None,
    config: AIConfig | None = None,
) -> dict[str, str | bool]:
    resolved_config = config or AIConfig.from_env()
    status = check_ai_status(resolved_config)
    result = generate_short_narration(
        {
            "acao": "teste rapido da IA Narradora",
            "resultado": "sem efeito mecanico",
            "tom": "neutro",
            "observacoes": "Nao registrar automaticamente no historico.",
        },
        client=client,
        config=resolved_config,
    )
    return {
        "available": status["available"],
        "reason": status["reason"],
        "source": result.source,
        "text": result.text,
        "should_register": result.should_register,
        "diagnostic": result.diagnostic,
        "message": result.message,
    }


def generate_short_narration(
    context: dict[str, Any],
    client: AIClient | None = None,
    config: AIConfig | None = None,
) -> NarrationResult:
    return _generate_or_fallback(
        "Gerar narracao curta sem alterar regras.",
        context,
        lambda: _fallback_event_text(context),
        client,
        config,
    )


def generate_npc_line(
    context: dict[str, Any],
    client: AIClient | None = None,
    config: AIConfig | None = None,
) -> NarrationResult:
    return _generate_or_fallback(
        "Gerar fala curta de NPC sem estabelecer verdade absoluta.",
        context,
        lambda: f"{context.get('npc', 'NPC')}: {generate_rumor(context.get('tom')).text}",
        client,
        config,
    )


def describe_consequence(
    context: dict[str, Any],
    client: AIClient | None = None,
    config: AIConfig | None = None,
) -> NarrationResult:
    return _generate_or_fallback(
        "Descrever consequencia narrativa sem criar regra nova.",
        context,
        lambda: generate_narrative_consequence(
            str(context.get("preco", context.get("price_level", "leve"))),
            tone=context.get("tom"),
        ).text,
        client,
        config,
    )


def summarize_session(
    context: dict[str, Any],
    client: AIClient | None = None,
    config: AIConfig | None = None,
) -> NarrationResult:
    return _generate_or_fallback(
        "Resumir sessao de campanha de forma objetiva.",
        context,
        lambda: _fallback_summary(context),
        client,
        config,
    )


def improve_event_text(
    context: dict[str, Any],
    client: AIClient | None = None,
    config: AIConfig | None = None,
) -> NarrationResult:
    return _generate_or_fallback(
        "Melhorar texto de evento mantendo o mesmo significado.",
        context,
        lambda: f"Evento organizado: {context.get('evento', context.get('acao', 'acontecimento sem titulo'))}.",
        client,
        config,
    )


def explain_ikisaki_roulette(
    roulette_result: Any,
    tone: str | None = None,
    client: AIClient | None = None,
    config: AIConfig | None = None,
) -> NarrationResult:
    context = _roulette_context(roulette_result, tone)
    return _generate_or_fallback(
        "Narrar resultado da Roleta Sombria usando apenas dados mecanicos fornecidos.",
        context,
        lambda: narrate_ikisaki_roulette(_roulette_namespace(context), tone=context.get("tom")).text,
        client,
        config,
    )


def _generate_or_fallback(
    task: str,
    context: dict[str, Any],
    fallback: Any,
    client: AIClient | None,
    config: AIConfig | None,
) -> NarrationResult:
    resolved_config = config or AIConfig.from_env()
    if not resolved_config.enabled:
        return _fallback_result(fallback, "disabled")
    if not resolved_config.api_key:
        return _fallback_result(fallback, "missing_api_key")

    try:
        prompt = build_prompt(task, context)
        text = (client or OpenAIResponsesClient()).complete(prompt, resolved_config)
        return NarrationResult(
            source="ai",
            text=text,
            should_register=False,
            diagnostic="ok",
            message="IA respondeu com sucesso.",
        )
    except Exception as exc:
        return _fallback_result(fallback, diagnose_ai_error(exc))


def _fallback_result(fallback: Any, diagnostic: str) -> NarrationResult:
    return NarrationResult(
        source="fallback",
        text=str(fallback()),
        should_register=False,
        diagnostic=diagnostic,
        message=ai_diagnostic_message(diagnostic),
    )


def diagnose_ai_error(error: BaseException) -> str:
    for current in _error_chain(error):
        if _is_openai_import_error(current):
            return "missing_openai_library"
        if _is_missing_api_key_error(current):
            return "missing_api_key"
        if isinstance(current, HTTPError):
            return _diagnose_http_error(current)
        if isinstance(current, (URLError, TimeoutError, ConnectionError)):
            return "connection_error"

    text = _safe_error_text(error)
    if any(part in text for part in ("invalid_api_key", "incorrect api key", "unauthorized", "401")):
        return "invalid_api_key"
    if any(
        part in text
        for part in (
            "billing",
            "credito",
            "credit",
            "quota",
            "insufficient_quota",
            "permission",
            "permissao",
            "forbidden",
            "403",
            "429",
        )
    ):
        return "billing_permission_error"
    if any(part in text for part in ("connection", "conexao", "timeout", "timed out", "network")):
        return "connection_error"
    return "unknown_error"


def ai_diagnostic_message(diagnostic: str) -> str:
    messages = {
        "ok": "IA respondeu com sucesso.",
        "disabled": "IA desativada. Usando narracao local.",
        "missing_api_key": "OPENAI_API_KEY ausente. Usando narracao local.",
        "missing_openai_library": (
            "IA configurada, mas a chamada falhou. Usando fallback local. "
            "Diagnostico: biblioteca openai nao instalada."
        ),
        "invalid_api_key": (
            "IA configurada, mas a chamada falhou. Usando fallback local. "
            "Diagnostico: chave invalida."
        ),
        "connection_error": (
            "IA configurada, mas a chamada falhou. Usando fallback local. "
            "Diagnostico: erro de conexao."
        ),
        "billing_permission_error": (
            "IA configurada, mas a chamada falhou. Usando fallback local. "
            "Diagnostico: billing, credito ou permissao."
        ),
        "unknown_error": (
            "IA configurada, mas a chamada falhou. Usando fallback local. "
            "Diagnostico: erro desconhecido."
        ),
    }
    return messages.get(diagnostic, messages["unknown_error"])


def _error_chain(error: BaseException) -> list[BaseException]:
    chain = [error]
    current = error
    while current.__cause__ is not None:
        current = current.__cause__
        chain.append(current)
    current = error
    while current.__context__ is not None:
        current = current.__context__
        chain.append(current)
    return chain


def _is_openai_import_error(error: BaseException) -> bool:
    if not isinstance(error, (ImportError, ModuleNotFoundError)):
        return False
    module_name = getattr(error, "name", None)
    return module_name == "openai" or "openai" in str(error).casefold()


def _is_missing_api_key_error(error: BaseException) -> bool:
    text = _safe_error_text(error)
    return "openai_api_key" in text and "nao configurada" in text


def _diagnose_http_error(error: HTTPError) -> str:
    body = _read_http_error_body(error)
    text = f"{error.code} {error.reason} {body}".casefold()
    if error.code == 401 or "invalid_api_key" in text or "incorrect api key" in text:
        return "invalid_api_key"
    if error.code in {402, 403, 429} or any(
        part in text
        for part in (
            "billing",
            "credit",
            "credito",
            "quota",
            "insufficient_quota",
            "permission",
            "permissao",
            "forbidden",
        )
    ):
        return "billing_permission_error"
    if error.code >= 500:
        return "connection_error"
    return "unknown_error"


def _read_http_error_body(error: HTTPError) -> str:
    try:
        body = error.read()
    except Exception:
        return ""
    if isinstance(body, bytes):
        return body.decode("utf-8", errors="ignore")
    return str(body)


def _safe_error_text(error: BaseException) -> str:
    texts = [str(item) for item in _error_chain(error)]
    return " ".join(texts).casefold()


def _fallback_event_text(context: dict[str, Any]) -> str:
    tone = context.get("tom")
    location_type = context.get("tipo_local")
    event = generate_random_event(tone=tone, location_type=location_type)
    return event.text


def _fallback_summary(context: dict[str, Any]) -> str:
    title = context.get("titulo") or context.get("sessao") or "sessao"
    events = context.get("eventos") or context.get("events") or []
    if isinstance(events, list) and events:
        return f"Resumo local de {title}: " + " ".join(str(event) for event in events[:5])
    return f"Resumo local de {title}: sem eventos detalhados informados."


def _roulette_context(roulette_result: Any, tone: str | None) -> dict[str, Any]:
    if isinstance(roulette_result, dict):
        result = roulette_result
    else:
        result = {
            "number": getattr(roulette_result, "number"),
            "link_name": getattr(roulette_result, "link_name"),
            "price_level": getattr(roulette_result, "price_level"),
            "repeated_number": getattr(roulette_result, "repeated_number", False),
            "chain_debt_generated": getattr(roulette_result, "chain_debt_generated", False),
            "switch_risk": getattr(roulette_result, "switch_risk", False),
        }
    return {
        "numero": result.get("number", result.get("numero")),
        "elo": result.get("link_name", result.get("elo")),
        "preco": result.get("price_level", result.get("preco")),
        "numero_repetido": result.get("repeated_number", result.get("numero_repetido", False)),
        "divida_gerada": result.get("chain_debt_generated", result.get("divida_gerada", False)),
        "risco_switch": result.get("switch_risk", result.get("risco_switch", False)),
        "tom": normalize_tone(tone),
    }


def _roulette_namespace(context: dict[str, Any]) -> SimpleNamespace:
    return SimpleNamespace(
        number=context["numero"],
        link_name=context["elo"],
        price_level=context["preco"],
        repeated_number=context["numero_repetido"],
        chain_debt_generated=context["divida_gerada"],
        switch_risk=context["risco_switch"],
    )
