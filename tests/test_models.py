from ankglish.models import stable_note_id


def test_stable_note_id_ignores_mutable_rendered_content() -> None:
    first = stable_note_id(
        provider="mwld",
        entry_id="the",
        sense_id="the-1",
        headword="The",
        part_of_speech="article",
    )
    second = stable_note_id(
        provider="mwld",
        entry_id="the",
        sense_id="the-1",
        headword="the",
        part_of_speech="article",
    )

    assert first == second


def test_stable_note_id_separates_variants() -> None:
    full = stable_note_id(
        provider="mwld",
        entry_id="the",
        sense_id="the-1",
        headword="the",
        part_of_speech="article",
        variant="full",
    )
    standard = stable_note_id(
        provider="mwld",
        entry_id="the",
        sense_id="the-1",
        headword="the",
        part_of_speech="article",
        variant="standard",
    )

    assert full != standard
