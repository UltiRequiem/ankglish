from ankglish.pipeline.normalize import normalize_entries


def test_normalize_mwld_short_definitions() -> None:
    notes, rejected = normalize_entries(
        {
            "hello": [
                {
                    "meta": {"id": "hello:1"},
                    "hwi": {"hw": "hello", "prs": [{"ipa": "həˈloʊ"}]},
                    "fl": "interjection",
                    "shortdef": ["used as a greeting"],
                }
            ]
        },
        frequency_ranks={"hello": 1},
    )

    assert len(notes) == 1
    assert notes[0].sense.definition == "used as a greeting"
    assert rejected == {"no_entry": 0, "no_definition": 0, "no_pronunciation": 0}