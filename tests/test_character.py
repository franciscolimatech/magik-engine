from src.core.character import create_miko_meu, load_or_create_miko, save_characters
from src.storage.json_storage import JSONStorage


def test_create_miko_meu_has_initial_sheet() -> None:
    miko = create_miko_meu()

    assert miko.name == "Miko Meu"
    assert miko.character_class == "Sombrio"
    assert miko.max_health == 25
    assert miko.current_health == 25
    assert miko.armor == 5
    assert miko.equipment == ["Cajado", "Corrente de Ferro"]
    assert miko.living_weapon == "Ikisaki"
    assert miko.can_disappear_in_shadows is True
    assert miko.chain_debts == 0
    assert miko.last_ikisaki_result is None
    assert miko.ikisaki_available is True


def test_save_and_load_miko_from_json_storage(tmp_path) -> None:
    storage = JSONStorage(tmp_path)
    original = create_miko_meu()
    original.chain_debts = 2
    save_characters(storage, [original])

    loaded = load_or_create_miko(storage)

    assert loaded.name == "Miko Meu"
    assert loaded.chain_debts == 2
