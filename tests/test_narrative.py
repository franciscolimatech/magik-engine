import pytest

from src.core.session import list_events
from src.core.character import create_miko_meu
from src.storage.memory import MemoryStorage
from src.systems.ikisaki import use_shadow_roulette
from src.systems.narrative import (
    IKISAKI_LINES,
    NARRATIVE_CONSEQUENCES,
    CURSE_OMENS,
    RANDOM_EVENTS,
    RUMORS,
    generate_curse_omen,
    generate_ikisaki_line,
    generate_narrative_consequence,
    generate_random_event,
    generate_rumor,
    maybe_record_narrative_result,
    narrate_ikisaki_roulette,
    ikisaki_cajado,
    ikisaki_combate,
    ikisaki_debochada,
    ikisaki_fala_seria,
    ikisaki_numero_alto,
    ikisaki_numero_ruim,
    ikisaki_recusa,
    ikisaki_switch_sombrio,
    record_narrative_result,
    reset_narrative_memory,
)


class FirstChoiceRng:
    def choice(self, sequence):
        return sequence[0]


@pytest.mark.parametrize("category", list(IKISAKI_LINES))
def test_generate_ikisaki_line_by_category(category: str) -> None:
    result = generate_ikisaki_line(category, rng=FirstChoiceRng())

    assert result.category == category
    assert result.text == IKISAKI_LINES[category][0]


def test_ikisaki_line_helper_functions_return_expected_categories() -> None:
    rng = FirstChoiceRng()

    assert ikisaki_debochada(rng).category == "debochada"
    assert ikisaki_combate(rng).category == "combate"
    assert ikisaki_numero_ruim(rng).category == "numero ruim na roleta"
    assert ikisaki_numero_alto(rng).category == "numero alto na roleta"
    assert ikisaki_recusa(rng).category == "recusa em ajudar"
    assert ikisaki_switch_sombrio(rng).category == "switch sombrio"
    assert ikisaki_fala_seria(rng).category == "fala seria"
    assert ikisaki_cajado(rng).category == "cajado usado no lugar dela"


def test_generate_ikisaki_line_rejects_invalid_category() -> None:
    with pytest.raises(ValueError):
        generate_ikisaki_line("categoria inexistente")


@pytest.mark.parametrize("price_level", list(NARRATIVE_CONSEQUENCES))
def test_generate_narrative_consequence_by_price(price_level: str) -> None:
    result = generate_narrative_consequence(price_level, rng=FirstChoiceRng())

    assert result.price_level == price_level
    assert result.description == NARRATIVE_CONSEQUENCES[price_level][0]


def test_generate_narrative_consequence_rejects_invalid_price() -> None:
    with pytest.raises(ValueError):
        generate_narrative_consequence("carissimo")


def test_generate_narrative_consequence_with_valid_tone() -> None:
    result = generate_narrative_consequence("leve", tone="misterioso", rng=FirstChoiceRng())

    assert result.tom == "misterioso"
    assert result.tipo == "consequencia narrativa"


def test_generate_narrative_consequence_rejects_invalid_tone() -> None:
    with pytest.raises(ValueError):
        generate_narrative_consequence("leve", tone="dramatico demais")


def test_generate_random_event() -> None:
    event = generate_random_event(rng=FirstChoiceRng())

    assert event == RANDOM_EVENTS[0]
    assert event.category
    assert event.description
    assert event.possible_consequence


def test_generate_random_event_by_location_type() -> None:
    event = generate_random_event(location_type="floresta", rng=FirstChoiceRng())

    assert event.category in {"rastro", "ruido suspeito", "criatura distante", "pressagio magico"}


def test_generate_random_event_with_tone() -> None:
    event = generate_random_event(tone="perigoso", rng=FirstChoiceRng())

    assert event.tom == "perigoso"
    assert event.category in {"perigo imediato", "criatura distante", "rastro", "ruido suspeito"}


def test_generate_rumor() -> None:
    rumor = generate_rumor(rng=FirstChoiceRng())

    assert rumor == RUMORS[0]
    assert rumor.level in {"comum", "estranho", "perigoso", "possivelmente falso"}
    assert rumor.text


def test_generate_rumor_with_tone() -> None:
    rumor = generate_rumor(tone="engraçado", rng=FirstChoiceRng())

    assert rumor.tom == "engracado"
    assert rumor.level in {"possivelmente falso", "comum"}


def test_generate_curse_omen() -> None:
    omen = generate_curse_omen(rng=FirstChoiceRng())

    assert omen == CURSE_OMENS[0]
    assert "Miko" in omen.description


def test_avoid_immediate_repetition_when_more_than_one_option_exists() -> None:
    reset_narrative_memory()

    first = generate_ikisaki_line("debochada", rng=FirstChoiceRng())
    second = generate_ikisaki_line("debochada", rng=FirstChoiceRng())

    assert first.text != second.text


def test_narrative_result_has_structured_fields() -> None:
    result = generate_random_event(tone="misterioso", location_type="estrada", rng=FirstChoiceRng())
    data = result.to_dict()

    assert set(data) == {
        "tipo",
        "categoria",
        "tom",
        "texto",
        "teste_sugerido",
        "consequencia_possivel",
        "registrar_no_historico",
        "metadata",
    }
    assert result.registrar_no_historico is True


def test_narrate_ikisaki_roulette_result() -> None:
    roulette_result = use_shadow_roulette(create_miko_meu(), forced_roll=10)

    narrative = narrate_ikisaki_roulette(roulette_result)

    assert narrative.tipo == "narrativa da roleta"
    assert "numero 10" in narrative.text
    assert "Corrente do Ultimo Elo" in narrative.text
    assert narrative.metadata["chain_debt_generated"] is True
    assert narrative.metadata["switch_risk"] is True


def test_record_narrative_result_in_session_history() -> None:
    storage = MemoryStorage({"sessions.json": []})

    event = record_narrative_result(
        storage,
        character="Ikisaki",
        action="Fala da Ikisaki",
        result="Vai mesmo usar esse graveto?",
        notes="Registro narrativo automatico.",
    )
    events = list_events(storage)

    assert event.character == "Ikisaki"
    assert len(events) == 1
    assert events[0].action == "Fala da Ikisaki"
    assert events[0].result == "Vai mesmo usar esse graveto?"
    assert events[0].notes == "Registro narrativo automatico."


def test_maybe_record_narrative_result_can_register() -> None:
    storage = MemoryStorage({"sessions.json": []})
    result = generate_rumor(rng=FirstChoiceRng())

    event = maybe_record_narrative_result(storage, result, should_register=True)

    assert event is not None
    assert len(list_events(storage)) == 1


def test_maybe_record_narrative_result_can_discard() -> None:
    storage = MemoryStorage({"sessions.json": []})
    result = generate_rumor(rng=FirstChoiceRng())

    event = maybe_record_narrative_result(storage, result, should_register=False)

    assert event is None
    assert list_events(storage) == []
