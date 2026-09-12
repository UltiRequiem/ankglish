import pytest

from ankglish.languages import ENGLISH, resolve_language
from ankglish.sources.frequency import english_words
from ankglish.sources.mwld import MWLDClient


def test_resolve_language_returns_english_profile() -> None:
    assert resolve_language("en") is ENGLISH


def test_resolve_language_rejects_unsupported_code() -> None:
    with pytest.raises(ValueError, match="unsupported language"):
        resolve_language("es")


def test_english_frequency_matches_the_backward_compatible_wrapper() -> None:
    assert ENGLISH.frequency(5) == english_words(max_rank=5)


def test_english_dictionary_client_is_mwld() -> None:
    from ankglish.config import BuildConfig

    config = BuildConfig(
        project_name="ankglish",
        schema="deck-note-v1",
        target_language="en",
        frequency_provider="wordfreq",
        frequency_version="pinned-in-lockfile",
        dictionary_provider="merriam-webster-learner",
        dictionary_fallback="kaikki-wiktionary",
        dictionary_max_concurrency=8,
        translations_enabled=False,
        package_headword_audio=True,
        example_tts_enabled=False,
        frequency_max_rank=60000,
        learner_api_key="test-key",
        elementary_api_key=None,
    )

    client = ENGLISH.build_dictionary_client(config)

    assert isinstance(client, MWLDClient)
    assert client.api_key == "test-key"
