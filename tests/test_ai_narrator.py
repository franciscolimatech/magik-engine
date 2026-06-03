import io
import json
from urllib.error import HTTPError, URLError

import pytest

from src.ai import ollama_client
from src.ai.context_builder import build_narrative_context
from src.ai.narrator import (
    AIConfig,
    NarrationResult,
    check_ai_status,
    describe_consequence,
    explain_ikisaki_roulette,
    generate_npc_line,
    generate_short_narration,
    improve_event_text,
    is_ai_available,
    run_quick_ai_test,
    summarize_session,
)
import src.ai.narrator as narrator_module
from src.ai.prompts import SYSTEM_GUARDRAILS, build_prompt, sanitize_context
from src.core.campaigns import (
    add_campaign_location,
    add_session_event,
    add_session_participant,
    create_campaign,
    create_campaign_session,
)
from src.core.character import create_miko_meu
from src.storage.memory import MemoryStorage
from src.systems.narrative import reset_narrative_memory
from src.systems.ikisaki import use_shadow_roulette


class FakeClient:
    def __init__(self, text: str = "Texto da IA.") -> None:
        self.text = text
        self.prompt = ""

    def complete(self, prompt: str, config: AIConfig) -> str:
        self.prompt = prompt
        assert config.api_key == "fake-key"
        return self.text


class FailingClient:
    def complete(self, prompt: str, config: AIConfig) -> str:
        raise RuntimeError("falhou")


class RaisingClient:
    def __init__(self, error: BaseException) -> None:
        self.error = error

    def complete(self, prompt: str, config: AIConfig) -> str:
        raise self.error


@pytest.fixture(autouse=True)
def clear_narrative_memory(monkeypatch):
    monkeypatch.setattr(
        narrator_module,
        "get_ollama_status",
        lambda: {
            "available": False,
            "model": "llama3.2:3b",
            "url": "http://localhost:11434",
            "reason": "Ollama não respondeu em localhost:11434. Tentando próxima opção.",
        },
    )
    reset_narrative_memory()
    yield
    reset_narrative_memory()


def test_ai_unavailable_without_openai_api_key() -> None:
    config = AIConfig.from_env({})

    assert is_ai_available(config) is False
    assert check_ai_status(config)["available"] is False
    assert check_ai_status(config)["ollama_available"] is False
    assert check_ai_status(config)["openai_configured"] is False


def test_generate_short_narration_uses_fallback_without_key() -> None:
    result = generate_short_narration({"acao": "abrir porta"}, config=AIConfig.from_env({}))

    assert result.source == "fallback"
    assert result.text
    assert result.should_register is False
    assert result.diagnostic == "missing_api_key"
    assert "OPENAI_API_KEY ausente" in result.message


def test_prompt_sanitizes_sensitive_keys() -> None:
    context = sanitize_context({"personagem": "Miko", "api_key": "segredo", "token": "abc"})
    prompt = build_prompt("Narrar", context)

    assert "Miko" in prompt
    assert "segredo" not in prompt
    assert "token" not in prompt


def test_prompt_guardrails_keep_ai_out_of_game_state() -> None:
    guardrails = SYSTEM_GUARDRAILS.casefold()

    assert "inventar dano" in guardrails
    assert "alterar vida" in guardrails
    assert "alterar armadura" in guardrails
    assert "mudar resultado de dado" in guardrails
    assert "matar personagem" in guardrails
    assert "mudanca permanente" in guardrails
    assert "registrar automaticamente" in guardrails
    assert "mestre aprova" in guardrails


def test_prompt_with_context_keeps_rule_limits_explicit() -> None:
    prompt = build_prompt(
        "Narrar evento",
        {
            "resultado_mecanico": {"rolagem": 18, "resultado": "sucesso"},
            "tom_desejado": "sombrio",
            "campanha": {"nome": "Ecos de Ikisaki"},
        },
    )

    assert "Dados mecanicos ja decididos" in prompt
    assert "Ecos de Ikisaki" in prompt
    assert "nao invente dano, morte, mudanca permanente, regra" in prompt


def test_generate_with_fake_ai_returns_structured_output() -> None:
    client = FakeClient("Cena narrada.")
    config = AIConfig(enabled=True, api_key="fake-key")

    result = generate_short_narration({"acao": "correr"}, client=client, config=config)

    assert isinstance(result, NarrationResult)
    assert result.source == "ai"
    assert result.text == "Cena narrada."
    assert result.should_register is False
    assert "Python decide regras" in client.prompt


def test_ollama_available_with_mock(monkeypatch) -> None:
    monkeypatch.setattr(
        narrator_module,
        "get_ollama_status",
        lambda: {
            "available": True,
            "model": "llama3.2:3b",
            "url": "http://localhost:11434",
            "reason": "Ollama local disponível usando modelo llama3.2:3b.",
        },
    )

    status = check_ai_status(AIConfig.from_env({}))

    assert status["available"] is True
    assert status["ollama_available"] is True
    assert status["ollama_model"] == "llama3.2:3b"
    assert "Ollama local disponível" in str(status["reason"])


def test_ollama_unavailable_with_mock() -> None:
    status = check_ai_status(AIConfig.from_env({}))

    assert status["available"] is False
    assert status["ollama_available"] is False
    assert status["fallback_active"] is True
    assert "fallback local" in str(status["reason"])


def test_source_is_ollama_when_ollama_responds(monkeypatch) -> None:
    monkeypatch.setattr(
        narrator_module,
        "get_ollama_status",
        lambda: {
            "available": True,
            "model": "llama3.2:3b",
            "url": "http://localhost:11434",
            "reason": "Ollama local disponível usando modelo llama3.2:3b.",
        },
    )
    monkeypatch.setattr(narrator_module, "generate_with_ollama", lambda prompt, model=None: "Cena vinda do Ollama.")

    result = generate_short_narration({"acao": "abrir porta"}, config=AIConfig.from_env({}))

    assert result.source == "ollama"
    assert result.text == "Cena vinda do Ollama."
    assert result.should_register is False
    assert result.diagnostic == "ok"


def test_ollama_error_uses_openai_as_second_option(monkeypatch) -> None:
    monkeypatch.setattr(
        narrator_module,
        "get_ollama_status",
        lambda: {
            "available": True,
            "model": "llama3.2:3b",
            "url": "http://localhost:11434",
            "reason": "Ollama local disponível usando modelo llama3.2:3b.",
        },
    )
    monkeypatch.setattr(
        narrator_module,
        "generate_with_ollama",
        lambda prompt, model=None: (_ for _ in ()).throw(RuntimeError("ollama caiu")),
    )

    result = generate_short_narration(
        {"acao": "abrir porta"},
        client=FakeClient("OpenAI assumiu."),
        config=AIConfig(enabled=True, api_key="fake-key"),
    )

    assert result.source == "ai"
    assert result.text == "OpenAI assumiu."


def test_ollama_error_uses_fallback_when_openai_missing(monkeypatch) -> None:
    monkeypatch.setattr(
        narrator_module,
        "get_ollama_status",
        lambda: {
            "available": True,
            "model": "llama3.2:3b",
            "url": "http://localhost:11434",
            "reason": "Ollama local disponível usando modelo llama3.2:3b.",
        },
    )
    monkeypatch.setattr(
        narrator_module,
        "generate_with_ollama",
        lambda prompt, model=None: (_ for _ in ()).throw(RuntimeError("ollama caiu")),
    )

    result = generate_short_narration({"acao": "abrir porta"}, config=AIConfig.from_env({}))

    assert result.source == "fallback"
    assert result.diagnostic == "ollama_error"
    assert "Ollama local falhou" in result.message


def test_ai_error_uses_fallback() -> None:
    result = generate_npc_line(
        {"npc": "Nara", "tom": "misterioso"},
        client=FailingClient(),
        config=AIConfig(enabled=True, api_key="fake-key"),
    )

    assert result.source == "fallback"
    assert result.text
    assert result.diagnostic == "unknown_error"
    assert "IA configurada, mas a chamada falhou" in result.message


def test_all_main_ai_functions_use_fallback_without_key() -> None:
    config = AIConfig.from_env({})
    roulette_context = {
        "number": 10,
        "link_name": "Corrente do Ultimo Elo",
        "price_level": "grave",
        "repeated_number": False,
        "chain_debt_generated": True,
        "switch_risk": True,
    }

    results = [
        generate_short_narration({"acao": "abrir porta"}, config=config),
        describe_consequence({"preco": "medio", "tom": "misterioso"}, config=config),
        explain_ikisaki_roulette(roulette_context, tone="sombrio", config=config),
        generate_npc_line({"npc": "Nara", "tom": "neutro"}, config=config),
        summarize_session({"titulo": "Sessao 1", "eventos": ["A porta abriu."]}, config=config),
        improve_event_text({"evento": "Miko viu uma sombra"}, config=config),
    ]

    for result in results:
        assert result.source == "fallback"
        assert result.source in {"ai", "fallback"}
        assert result.text
        assert result.should_register is False


def test_describe_consequence_uses_fallback() -> None:
    result = describe_consequence({"preco": "grave", "tom": "sombrio"}, config=AIConfig.from_env({}))

    assert result.source == "fallback"
    assert result.text


def test_summarize_session_uses_fallback() -> None:
    result = summarize_session({"titulo": "Sessao 1", "eventos": ["A porta abriu."]}, config=AIConfig.from_env({}))

    assert result.source == "fallback"
    assert "Sessao 1" in result.text


def test_improve_event_text_uses_fallback() -> None:
    result = improve_event_text({"evento": "Miko viu uma sombra"}, config=AIConfig.from_env({}))

    assert result.source == "fallback"
    assert "Miko viu uma sombra" in result.text


def test_explain_ikisaki_roulette_uses_mechanical_result() -> None:
    roulette = use_shadow_roulette(create_miko_meu(), forced_roll=10)

    result = explain_ikisaki_roulette(roulette, tone="sombrio", config=AIConfig.from_env({}))

    assert result.source == "fallback"
    assert "numero 10" in result.text
    assert "Corrente do Ultimo Elo" in result.text


def test_explain_ikisaki_roulette_prompt_includes_campaign_context() -> None:
    storage = MemoryStorage()
    campaign = create_campaign(storage, "Ikisaki Final", "A corrente volta a cobrar.")
    add_campaign_location(storage, campaign.id, "Santuario do Elo")
    session = create_campaign_session(storage, campaign.id, "Divida de Corrente", number=7)
    add_session_participant(storage, session.id, "Miko Meu")
    add_session_event(storage, session.id, "Miko ouviu o elo responder.")
    context = build_narrative_context(
        storage,
        session_id=session.id,
        mechanical_result={"resultado": "roleta ja resolvida"},
        tone="sombrio",
    )
    client = FakeClient("A corrente descreve o preco.")
    roulette_context = {
        "number": 10,
        "link_name": "Corrente do Ultimo Elo",
        "price_level": "grave",
        "repeated_number": False,
        "chain_debt_generated": True,
        "switch_risk": True,
    }

    result = explain_ikisaki_roulette(
        roulette_context,
        tone="sombrio",
        context=context,
        client=client,
        config=AIConfig(enabled=True, api_key="fake-key"),
    )

    assert result.source == "ai"
    assert "Miko Meu" in client.prompt
    assert "numero" in client.prompt
    assert "10" in client.prompt
    assert "Corrente do Ultimo Elo" in client.prompt
    assert "grave" in client.prompt
    assert "divida_de_corrente" in client.prompt
    assert "risco_switch_sombrio" in client.prompt
    assert "Ikisaki Final" in client.prompt
    assert "Divida de Corrente" in client.prompt
    assert "Santuario do Elo" in client.prompt


def test_quick_ai_test_uses_fallback_without_key_and_does_not_register() -> None:
    result = run_quick_ai_test(config=AIConfig.from_env({}))

    assert result["available"] is False
    assert result["source"] == "fallback"
    assert result["source"] in {"ai", "fallback"}
    assert result["text"]
    assert result["should_register"] is False
    assert result["ollama_model"] == "llama3.2:3b"


def test_quick_ai_test_uses_ai_when_available_and_does_not_register() -> None:
    result = run_quick_ai_test(
        client=FakeClient("Teste narrado pela IA."),
        config=AIConfig(enabled=True, api_key="fake-key"),
    )

    assert result["available"] is True
    assert result["source"] == "ai"
    assert result["source"] in {"ai", "fallback"}
    assert result["text"] == "Teste narrado pela IA."
    assert result["should_register"] is False


def test_quick_ai_test_uses_ollama(monkeypatch) -> None:
    monkeypatch.setattr(
        narrator_module,
        "get_ollama_status",
        lambda: {
            "available": True,
            "model": "llama3.2:3b",
            "url": "http://localhost:11434",
            "reason": "Ollama local disponível usando modelo llama3.2:3b.",
        },
    )
    monkeypatch.setattr(narrator_module, "generate_with_ollama", lambda prompt, model=None: "Teste via Ollama.")

    result = run_quick_ai_test(config=AIConfig.from_env({}))

    assert result["available"] is True
    assert result["source"] == "ollama"
    assert result["text"] == "Teste via Ollama."
    assert result["should_register"] is False


def test_quick_ai_test_falls_back_on_ai_error() -> None:
    result = run_quick_ai_test(
        client=FailingClient(),
        config=AIConfig(enabled=True, api_key="fake-key"),
    )

    assert result["available"] is True
    assert result["source"] == "fallback"
    assert result["source"] in {"ai", "fallback"}
    assert result["text"]
    assert result["should_register"] is False
    assert result["diagnostic"] == "unknown_error"
    assert "IA configurada, mas a chamada falhou" in str(result["message"])


def test_missing_openai_library_is_diagnosed() -> None:
    error = ModuleNotFoundError("No module named 'openai'")
    error.name = "openai"

    result = generate_short_narration(
        {"acao": "teste"},
        client=RaisingClient(error),
        config=AIConfig(enabled=True, api_key="fake-key"),
    )

    assert result.source == "fallback"
    assert result.diagnostic == "missing_openai_library"
    assert "biblioteca openai nao instalada" in result.message
    assert "fake-key" not in result.message


def test_invalid_key_error_is_diagnosed() -> None:
    result = generate_short_narration(
        {"acao": "teste"},
        client=RaisingClient(_http_error(401, b'{"error":{"code":"invalid_api_key"}}')),
        config=AIConfig(enabled=True, api_key="fake-key"),
    )

    assert result.source == "fallback"
    assert result.diagnostic == "invalid_api_key"
    assert "chave invalida" in result.message
    assert "fake-key" not in result.message


def test_connection_error_is_diagnosed() -> None:
    result = generate_short_narration(
        {"acao": "teste"},
        client=RaisingClient(URLError("timed out")),
        config=AIConfig(enabled=True, api_key="fake-key"),
    )

    assert result.source == "fallback"
    assert result.diagnostic == "connection_error"
    assert "erro de conexao" in result.message
    assert "fake-key" not in result.message


def test_billing_credit_permission_error_is_diagnosed() -> None:
    result = generate_short_narration(
        {"acao": "teste"},
        client=RaisingClient(_http_error(429, b'{"error":{"code":"insufficient_quota"}}')),
        config=AIConfig(enabled=True, api_key="fake-key"),
    )

    assert result.source == "fallback"
    assert result.diagnostic == "billing_permission_error"
    assert "billing, credito ou permissao" in result.message
    assert "fake-key" not in result.message


def test_unknown_ai_error_is_diagnosed_without_leaking_key() -> None:
    result = generate_short_narration(
        {"acao": "teste"},
        client=RaisingClient(RuntimeError("falha tecnica com fake-key")),
        config=AIConfig(enabled=True, api_key="fake-key"),
    )

    assert result.source == "fallback"
    assert result.diagnostic == "unknown_error"
    assert "erro desconhecido" in result.message
    assert "fake-key" not in result.message


def _http_error(status: int, body: bytes) -> HTTPError:
    return HTTPError(
        url="https://api.openai.com/v1/responses",
        code=status,
        msg="erro",
        hdrs=None,
        fp=io.BytesIO(body),
    )


class FakeHTTPResponse:
    def __init__(self, payload: dict) -> None:
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")


def test_ollama_client_default_model(monkeypatch) -> None:
    monkeypatch.delenv("OLLAMA_MODEL", raising=False)

    assert ollama_client.get_ollama_model() == "llama3.2:3b"


def test_ollama_client_model_from_env(monkeypatch) -> None:
    monkeypatch.setenv("OLLAMA_MODEL", "mistral")

    assert ollama_client.get_ollama_model() == "mistral"


def test_ollama_client_status_available(monkeypatch) -> None:
    monkeypatch.setattr(ollama_client.request, "urlopen", lambda *args, **kwargs: FakeHTTPResponse({"models": []}))

    status = ollama_client.get_ollama_status()

    assert status["available"] is True
    assert status["model"] == ollama_client.get_ollama_model()


def test_ollama_client_status_unavailable(monkeypatch) -> None:
    def fail(*args, **kwargs):
        raise URLError("connection refused")

    monkeypatch.setattr(ollama_client.request, "urlopen", fail)

    status = ollama_client.get_ollama_status()

    assert status["available"] is False
    assert "Ollama não respondeu" in status["reason"]


def test_ollama_client_generate(monkeypatch) -> None:
    seen = {}

    def fake_urlopen(http_request, timeout):
        seen["payload"] = json.loads(http_request.data.decode("utf-8"))
        return FakeHTTPResponse({"response": "Narracao local."})

    monkeypatch.setattr(ollama_client.request, "urlopen", fake_urlopen)

    text = ollama_client.generate_with_ollama("Prompt seguro.", model="llama3.2:3b")

    assert text == "Narracao local."
    assert seen["payload"]["model"] == "llama3.2:3b"
    assert seen["payload"]["stream"] is False
