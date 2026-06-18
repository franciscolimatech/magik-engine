from src.ai.narrator import AIConfig, NarrationResult
from src.game.ai_narration import (
    GAME_AI_NARRATION_ENV,
    GAME_NARRATION_GUARDRAILS,
    build_safe_game_narration_context,
    get_local_fallback_narration,
    is_game_ai_narration_enabled,
    narrate_game_text,
)
from src.game.save import create_default_game_save


def test_game_ai_narration_is_disabled_by_default() -> None:
    assert is_game_ai_narration_enabled({}) is False


def test_game_ai_narration_env_accepts_disabled_values() -> None:
    for value in ("0", "false", "no", "off"):
        assert is_game_ai_narration_enabled({GAME_AI_NARRATION_ENV: value}) is False


def test_game_ai_narration_env_accepts_enabled_values() -> None:
    for value in ("1", "true", "yes", "on"):
        assert is_game_ai_narration_enabled({GAME_AI_NARRATION_ENV: value}) is True


def test_without_ai_available_returns_local_fallback() -> None:
    def fallback_narrator(context, config=None):
        return NarrationResult(source="fallback", text="texto local alternativo", diagnostic="missing_api_key")

    result = narrate_game_text(
        "Texto local seguro.",
        {"location_id": "floresta-do-avesso"},
        config=AIConfig(enabled=True, api_key=None),
        narrator=fallback_narrator,
    )

    assert result.text == "Texto local seguro."
    assert result.source == "fallback"
    assert result.used_ai is False
    assert result.diagnostic == "missing_api_key"


def test_disabled_ai_returns_local_fallback_without_calling_narrator() -> None:
    called = False

    def narrator(context, config=None):
        nonlocal called
        called = True
        return NarrationResult(source="ai", text="Nao deve ser usado.")

    result = narrate_game_text(
        "Texto local seguro.",
        config=AIConfig(enabled=False, api_key=None),
        narrator=narrator,
    )

    assert result.text == "Texto local seguro."
    assert result.source == "disabled"
    assert result.used_ai is False
    assert called is False


def test_narrator_error_returns_local_fallback() -> None:
    def failing_narrator(context, config=None):
        raise RuntimeError("falha simulada")

    result = narrate_game_text(
        "Texto local seguro.",
        config=AIConfig(enabled=True, api_key="fake"),
        narrator=failing_narrator,
    )

    assert result.text == "Texto local seguro."
    assert result.source == "error"
    assert result.used_ai is False
    assert result.diagnostic == "narrator_error"


def test_ai_result_returns_generated_text_without_state_effects() -> None:
    def ai_narrator(context, config=None):
        return NarrationResult(source="ai", text="A sombra se curva entre as arvores.", diagnostic="ok")

    result = narrate_game_text(
        "Texto local seguro.",
        {"event_id": "evento-sombra-observa", "tone": "sombrio"},
        config=AIConfig(enabled=True, api_key="fake"),
        narrator=ai_narrator,
    )

    assert result.text == "A sombra se curva entre as arvores."
    assert result.source == "ai"
    assert result.used_ai is True
    assert result.diagnostic == "ok"


def test_context_excludes_sensitive_and_full_save_data() -> None:
    save = create_default_game_save()
    context = build_safe_game_narration_context(
        {
            "location_id": "floresta-do-avesso",
            "location_name": "Floresta do Avesso",
            "event_id": "evento-sombra-observa",
            "api_key": "segredo",
            "token": "abc",
            "save": save.to_dict(),
            "choice_history": [{"id": "escolha"}],
            "story_flags": ["viu_sombra", "viu_sombra", "x" * 120],
            "world_flags": ["floresta_inquieta"],
        },
        fallback_text="Texto local seguro.",
    )

    assert context["location_id"] == "floresta-do-avesso"
    assert context["location_name"] == "Floresta do Avesso"
    assert context["event_id"] == "evento-sombra-observa"
    assert context["story_flags"] == ["viu_sombra", "x" * 80]
    assert context["world_flags"] == ["floresta_inquieta"]
    assert context["texto_local"] == "Texto local seguro."
    assert "api_key" not in context
    assert "token" not in context
    assert "save" not in context
    assert "choice_history" not in context


def test_result_always_has_required_fields() -> None:
    result = get_local_fallback_narration("Texto local.")
    data = result.to_dict()

    assert set(data) == {"text", "source", "used_ai", "diagnostic"}
    assert data["text"] == "Texto local."
    assert data["source"] == "fallback"
    assert data["used_ai"] is False


def test_narration_does_not_mutate_save() -> None:
    save = create_default_game_save()
    before = save.to_dict()

    narrate_game_text(
        "Texto local seguro.",
        {
            "location_id": save.location_id,
            "story_flags": save.story_flags,
            "world_flags": save.world_flags,
            "decided_consequence": "A consequencia ja foi decidida pelo Python.",
        },
        config=AIConfig(enabled=False, api_key=None),
    )

    assert save.to_dict() == before


def test_guardrails_are_sent_in_safe_context() -> None:
    captured = {}

    def ai_narrator(context, config=None):
        captured.update(context)
        return NarrationResult(source="ai", text="Narracao curta.")

    narrate_game_text(
        "Texto local seguro.",
        {"decided_consequence": "Nada mecanico muda.", "tone": "misterioso"},
        config=AIConfig(enabled=True, api_key="fake"),
        narrator=ai_narrator,
    )

    guardrails = " ".join(captured["limites_da_ia"])
    assert list(GAME_NARRATION_GUARDRAILS) == captured["limites_da_ia"]
    assert "nao pode decidir dano" in guardrails
    assert "consequencia real ja foi decidida" in guardrails
    assert captured["texto_local"] == "Texto local seguro."
    assert captured["tom"] == "misterioso"
