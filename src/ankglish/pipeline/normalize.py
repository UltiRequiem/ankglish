"""Normalize MWLD responses into stable deck notes."""

from __future__ import annotations

from html import escape
import re

from ..models import DeckNote, Pronunciation, Provenance, Sense, stable_note_id


def _plain(value: object) -> str:
    return re.sub(r"\s+", " ", str(value)).strip()


def normalize_entries(
    entries: dict[str, list[dict[str, object]]],
    *,
    frequency_ranks: dict[str, int],
    variant: str = "full",
) -> tuple[list[DeckNote], dict[str, int]]:
    notes: list[DeckNote] = []
    rejected = {"no_entry": 0, "no_definition": 0, "no_pronunciation": 0}
    for word, records in entries.items():
        if not records:
            rejected["no_entry"] += 1
            continue
        record = records[0]
        headword = _plain(record.get("hwi", {}).get("hw", word)).replace("*", "")
        pronunciations = record.get("hwi", {}).get("prs", [])
        pronunciation = next(
            (item for item in pronunciations if isinstance(item, dict) and item.get("ipa")),
            None,
        )
        if pronunciation is None:
            rejected["no_pronunciation"] += 1
            continue
        definitions = [
            _plain(definition)
            for definition in record.get("shortdef", [])
            if _plain(definition)
        ]
        if not definitions:
            rejected["no_definition"] += 1
            continue
        entry_id = _plain(record.get("meta", {}).get("id", word))
        for index, definition in enumerate(definitions, start=1):
            sense_id = f"{entry_id}-{index}"
            sense = Sense(
                source_id=sense_id,
                definition=escape(definition),
                part_of_speech=_plain(record.get("fl", "unknown")),
                provenance=Provenance(provider="mwld", source_id=entry_id),
            )
            note = DeckNote(
                note_id=stable_note_id(
                    provider="mwld",
                    entry_id=entry_id,
                    sense_id=sense_id,
                    headword=headword,
                    part_of_speech=sense.part_of_speech,
                    variant=variant,
                ),
                headword=headword,
                part_of_speech=sense.part_of_speech,
                sense=sense,
                variant=variant,
                fields={
                    "Headword": escape(headword),
                    "Pronunciation": escape(_plain(pronunciation["ipa"])),
                    "Definition": escape(definition),
                },
            )
            notes.append(note)
    return notes, rejected