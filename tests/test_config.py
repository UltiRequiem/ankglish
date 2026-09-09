from pathlib import Path

from ankglish.config import load_config


def test_load_default_config() -> None:
    config = load_config(Path("config/default.toml"))

    assert config.project_name == "ankglish"
    assert config.translations_enabled is False
    assert config.example_tts_enabled is False