import pytest

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
from src.ai.prompts import SYSTEM_GUARDRAILS, build_prompt, sanitize_context
from src.core.character import create_miko_meu
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


@pytest.fixture(autouse=True)
def clear_narrative_memory():
    reset_narrative_memory()
    yield
    reset_narrative_memory()


def test_ai_unavailable_without_openai_api_key() -> None:
    config = AIConfig.from_env({})

    assert is_ai_available(config) is False
    assert check_ai_status(config)["available"] is False


def test_generate_short_narration_uses_fallback_without_key() -> None:
    result = generate_short_narration({"acao": "abrir porta"}, config=AIConfig.from_env({}))

    assert result.source == "fallback"
    assert result.text
    assert result.should_register is False


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
    assert "registrar automaticamente" in guardrails
    assert "mestre aprova" in guardrails


def test_generate_with_fake_ai_returns_structured_output() -> None:
    client = FakeClient("Cena narrada.")
    config = AIConfig(enabled=True, api_key="fake-key")

    result = generate_short_narration({"acao": "correr"}, client=client, config=config)

    assert isinstance(result, NarrationResult)
    assert result.source == "ai"
    assert result.text == "Cena narrada."
    assert result.should_register is False
    assert "Python decide regras" in client.prompt


def test_ai_error_uses_fallback() -> None:
    result = generate_npc_line(
        {"npc": "Nara", "tom": "misterioso"},
        client=FailingClient(),
        config=AIConfig(enabled=True, api_key="fake-key"),
    )

    assert result.source == "fallback"
    assert result.text


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


def test_quick_ai_test_uses_fallback_without_key_and_does_not_register() -> None:
    result = run_quick_ai_test(config=AIConfig.from_env({}))

    assert result["available"] is False
    assert result["source"] == "fallback"
    assert result["source"] in {"ai", "fallback"}
    assert result["text"]
    assert result["should_register"] is False


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
