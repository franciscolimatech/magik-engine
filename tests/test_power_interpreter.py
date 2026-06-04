import json

from src.ai.narrator import AIConfig
from src.ai.power_interpreter import interpret_power


class FakeOpenAIClient:
    def complete(self, prompt: str, config: AIConfig) -> str:
        return json.dumps(
            {
                "nome": "Fios de Luz",
                "tipo": "controle",
                "descricao": "Manipula fios de luz.",
                "efeito_narrativo": "Prende ou revela algo narrativamente.",
                "limitacao": "Precisa de alcance curto e aprovacao do mestre.",
                "custo_ou_preco": "Pode chamar atencao.",
                "uso_sugerido": "Conforme decisao do mestre.",
                "teste_sugerido": "Vontade",
                "observacao_do_mestre": "Sugestao nao oficial. O mestre deve aprovar.",
                "deve_ser_aprovado": True,
            }
        )


class FailingOpenAIClient:
    def complete(self, prompt: str, config: AIConfig) -> str:
        raise RuntimeError("boom")


def unavailable_ollama() -> dict:
    return {"available": False, "model": "fake"}


def available_ollama() -> dict:
    return {"available": True, "model": "fake"}


def fake_ollama_generator(prompt: str, model: str | None = None) -> str:
    return json.dumps(
        {
            "nome": "Vozes Antigas",
            "tipo": "utilidade",
            "descricao": "Escuta ecos de espiritos antigos.",
            "efeito_narrativo": "Recebe pistas vagas e simbolicas.",
            "limitacao": "Pode confundir ou atrair presencas; exige aprovacao do mestre.",
            "custo_ou_preco": "Cansa a mente.",
            "uso_sugerido": "1 vez por cena.",
            "teste_sugerido": "Vontade",
            "observacao_do_mestre": "Sugestao nao oficial. O mestre deve aprovar.",
            "deve_ser_aprovado": True,
        }
    )


def test_power_interpreter_fallback_returns_expected_structure() -> None:
    result = interpret_power(
        character_name="Lia",
        character_class="Mago",
        equipment=[],
        raw_power="Manipula fios de luz.",
        story="Busca uma cidade perdida.",
        config=AIConfig(enabled=False, api_key=None),
    )

    assert set(result) == {
        "source",
        "nome",
        "tipo",
        "descricao",
        "efeito_narrativo",
        "limitacao",
        "custo_ou_preco",
        "uso_sugerido",
        "teste_sugerido",
        "observacao_do_mestre",
        "deve_ser_aprovado",
    }
    assert result["source"] == "fallback"
    assert result["deve_ser_aprovado"] is True


def test_power_interpreter_guardrails_include_master_approval() -> None:
    result = interpret_power(
        character_name="Lia",
        character_class="Mago",
        equipment=[],
        raw_power="Cria luz.",
        config=AIConfig(enabled=False, api_key=None),
    )

    assert "mestre" in result["observacao_do_mestre"].casefold()
    assert "apro" in result["observacao_do_mestre"].casefold()


def test_absurd_power_receives_clear_limitation() -> None:
    result = interpret_power(
        character_name="Lia",
        character_class="Mago",
        equipment=[],
        raw_power="Sou invencivel e tenho dano infinito.",
        config=AIConfig(enabled=False, api_key=None),
    )

    assert "limitado" in result["limitacao"].casefold() or "limite" in result["limitacao"].casefold()
    assert "mestre" in result["limitacao"].casefold()


def test_power_interpreter_uses_ollama_when_available() -> None:
    result = interpret_power(
        character_name="Lia",
        character_class="Curandeiro",
        equipment=["Amuleto estranho"],
        raw_power="Escuto vozes antigas.",
        config=AIConfig(enabled=True, api_key=None),
        ollama_status_provider=available_ollama,
        ollama_generator=fake_ollama_generator,
    )

    assert result["source"] == "ollama"
    assert result["nome"] == "Vozes Antigas"
    assert result["deve_ser_aprovado"] is True


def test_power_interpreter_uses_openai_when_configured() -> None:
    result = interpret_power(
        character_name="Lia",
        character_class="Mago",
        equipment=[],
        raw_power="Manipula fios de luz.",
        config=AIConfig(enabled=True, api_key="fake"),
        openai_client=FakeOpenAIClient(),
        ollama_status_provider=unavailable_ollama,
    )

    assert result["source"] == "openai"
    assert result["nome"] == "Fios de Luz"


def test_power_interpreter_falls_back_when_ai_fails() -> None:
    result = interpret_power(
        character_name="Lia",
        character_class="Mago",
        equipment=[],
        raw_power="Manipula fios de luz.",
        config=AIConfig(enabled=True, api_key="fake"),
        openai_client=FailingOpenAIClient(),
        ollama_status_provider=unavailable_ollama,
    )

    assert result["source"] == "fallback"
    assert result["nome"] == "Poder Especial"
