from ankglish.pipeline.normalize import normalize_entries


def test_normalize_mwld_short_definitions() -> None:
    notes, rejected = normalize_entries(
        {
            "hello": [
                {
                    "meta": {"id": "hello:1"},
                    "hwi": {
                        "hw": "hello",
                        "prs": [{"ipa": "həˈloʊ", "sound": {"audio": "hello001"}}],
                    },
                    "fl": "interjection",
                    "shortdef": ["used as a greeting"],
                    "def": [[[
                        "sense",
                        {"dt": [["vis", [{"t": "Hello there."}]]]},
                    ]]],
                }
            ]
        },
        frequency_ranks={"hello": 1},
    )

    assert len(notes) == 1
    assert notes[0].sense.definition == "used as a greeting"
    assert notes[0].sense.examples == ("Hello there.",)
    assert "ankglish-example-item" in notes[0].fields["Examples"]
    assert notes[0].fields["AudioURL"].endswith("/h/hello001.wav")
    assert rejected == {"no_entry": 0, "no_definition": 0, "no_pronunciation": 0}