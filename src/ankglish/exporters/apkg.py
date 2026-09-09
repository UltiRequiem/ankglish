"""Stable, language-neutral Anki package export."""

from __future__ import annotations

from pathlib import Path

import genanki

from ..models import DeckNote

MODEL_ID = 1_701_001
DECK_IDS = {"full": 1_701_101, "standard": 1_701_102}


def _template(name: str) -> str:
    source_path = Path(__file__).parents[3] / "templates" / name
    package_path = Path(__file__).parents[1] / "templates" / name
    template_path = source_path if source_path.is_file() else package_path
    return template_path.read_text(encoding="utf-8")


def export_apkg(
    notes: list[DeckNote], output_path: Path, *, variant: str, description: str = ""
) -> None:
    if variant not in DECK_IDS:
        raise ValueError(f"unsupported variant: {variant}")

    model = genanki.Model(
        MODEL_ID,
        "ankglish pronunciation",
        fields=[
            {"name": "Headword"},
            {"name": "PartOfSpeech"},
            {"name": "Pronunciation"},
            {"name": "Definition"},
            {"name": "Examples"},
            {"name": "Translation"},
            {"name": "Example"},
            {"name": "Audio"},
            {"name": "CardScript"},
        ],
        templates=[
            {
                "name": "Recognition",
                "qfmt": _template("card-front.html"),
                "afmt": _template("card-back.html"),
            }
        ],
        css=_template("styles.css"),
    )
    deck = genanki.Deck(
        DECK_IDS[variant], f"ankglish::{variant}", description=description
    )
    media_files: list[str] = []
    for deck_note in notes:
        note = genanki.Note(
            model=model,
            fields=[
                deck_note.fields.get("Headword", deck_note.headword),
                deck_note.fields.get("PartOfSpeech", deck_note.part_of_speech),
                deck_note.fields.get("Pronunciation", ""),
                deck_note.fields.get("Definition", deck_note.sense.definition),
                deck_note.fields.get("Examples", "<br>".join(deck_note.sense.examples)),
                deck_note.fields.get("Translation", ""),
                deck_note.fields.get(
                    "Example",
                    deck_note.sense.examples[0] if deck_note.sense.examples else "",
                ),
                deck_note.fields.get("Audio", ""),
                _template("card.js"),
            ],
        )
        note.guid = deck_note.note_id
        deck.add_note(note)
        audio_path = deck_note.fields.get("AudioPath")
        if audio_path:
            media_files.append(audio_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    package = genanki.Package(deck)
    package.media_files = media_files
    package.write_to_file(str(output_path))
