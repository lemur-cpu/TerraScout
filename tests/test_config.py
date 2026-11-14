from terra_scout.config import Settings


def test_settings_do_not_define_a_second_registry_path() -> None:
    assert "database_path" not in Settings.model_fields
