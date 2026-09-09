"""Stable, language-neutral Anki package export."""

from __future__ import annotations

from pathlib import Path

import genanki

from ..models import DeckNote


MODEL_ID = 1_701_001
DECK_IDS = {"full": 1_701_101, "standard": 1_701_102}


def export_apkg(notes: list[DeckNote], output_path: Path, *, variant: str) -> None:
    if variant not in DECK_IDS:
        raise ValueError(f"unsupported variant: {variant}")

    model = genanki.Model(
        MODEL_ID,
        "ankglish pronunciation",
        fields=[
            {"name": "Headword"},
            {"name": "Pronunciation"},
            {"name": "Definition"},
            {"name": "Examples"},
            {"name": "Translation"},
        ],
        templates=[
            {
                "name": "Recognition",
                "qfmt": "<div class='headword'>{{Headword}}</div><div>{{Pronunciation}}</div>",
                "afmt": "{{FrontSide}}<hr><div>{{Definition}}</div><div>{{Examples}}</div><div>{{Translation}}</div>",
            }
        ],
        css=".card { font-family: sans-serif; text-align: center; } .headword { font-size: 2em; }",
    )
    deck = genanki.Deck(DECK_IDS[variant], f"ankglish::{variant}")
    for deck_note in notes:
        note = genanki.Note(
            model=model,
            fields=[
                deck_note.fields.get("Headword", deck_note.headword),
                deck_note.fields.get("Pronunciation", ""),
                deck_note.fields.get("Definition", deck_note.sense.definition),
                deck_note.fields.get("Examples", "<br>".join(deck_note.sense.examples)),
                deck_note.fields.get("Translation", ""),
            ],
        )
        note.guid = deck_note.note_id
        deck.add_note(note)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    genanki.Package(deck).write_to_file(str(output_path))