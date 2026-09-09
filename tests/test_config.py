from pathlib import Path

from ankglish.config import load_config


def test_load_default_config(monkeypatch) -> None:
    monkeypatch.delenv("MWLD_LEARNER_API_KEY", raising=False)
    monkeypatch.delenv("MWLD_ELEMENTARY_API_KEY", raising=False)
    config = load_config(Path("config/default.toml"), dotenv_path=Path("/tmp/ankglish-no.env"))

    assert config.project_name == "ankglish"
    assert config.translations_enabled is False
    assert config.example_tts_enabled is False
    assert config.learner_api_key is None
    assert config.elementary_api_key is None