from ankglish.exporters.notices import build_attribution, deck_description


def test_attribution_marks_active_and_inactive_sources() -> None:
    text = build_attribution(
        {"fetched_count": 10, "audio_count": 5, "wiktionary_count": 0}
    )
    assert "Merriam-Webster Learner's Dictionary (used in this build)" in text
    assert "https://dictionaryapi.com/info/terms-of-service" in text
    assert "English Wiktionary via Kaikki.org (not used in this build)" in text
    assert "wordfreq (used in this build)" in text
    assert "Audio (used in this build)" in text


def test_attribution_includes_cc_by_sa_when_wiktionary_used() -> None:
    text = build_attribution(
        {"fetched_count": 0, "audio_count": 0, "wiktionary_count": 3}
    )
    assert "English Wiktionary via Kaikki.org (used in this build)" in text
    assert "CC BY-SA 4.0" in text
    assert "Merriam-Webster Learner's Dictionary (not used in this build)" in text


def test_deck_description_reflects_sources() -> None:
    with_mw = deck_description({"fetched_count": 10, "wiktionary_count": 0})
    assert "Merriam-Webster" in with_mw
    assert "not openly licensed" in with_mw
    assert "Pipeline code: MIT." in with_mw

    with_wik = deck_description({"fetched_count": 0, "wiktionary_count": 4})
    assert "CC BY-SA 4.0" in with_wik
