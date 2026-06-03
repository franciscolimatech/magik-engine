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
    summarize_session,
)
from src.ai.prompts import build_prompt, sanitize_context
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
