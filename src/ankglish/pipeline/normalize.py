"""Normalize MWLD responses into stable deck notes."""

from __future__ import annotations

from html import escape
import re

from ..models import DeckNote, Provenance, Sense, stable_note_id


def _plain(value: object) -> str:
    return re.sub(r"\s+", " ", str(value)).strip()


def _examples(record: dict[str, object]) -> tuple[str, ...]:
    examples: list[str] = []

    def visit(value: object) -> None:
        if isinstance(value, dict):
            if "t" in value and isinstance(value["t"], str):
                text = re.sub(r"\{/?(?:it|b|ldquo|rdquo)\}", "", value["t"])
                text = _plain(text)
                if text and text not in examples:
                    examples.append(text)
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    visit(record.get("def", []))
    return tuple(examples[:6])


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
        examples = _examples(record)
        sound = pronunciation.get("sound", {})
        audio_id = _plain(sound.get("audio", "")) if isinstance(sound, dict) else ""
        audio_url = (
            f"https://media.merriam-webster.com/soundc11/{audio_id[0]}/{audio_id}.wav"
            if audio_id
            else ""
        )
        for index, definition in enumerate(definitions, start=1):
            sense_id = f"{entry_id}-{index}"
            sense = Sense(
                source_id=sense_id,
                definition=escape(definition),
                part_of_speech=_plain(record.get("fl", "unknown")),
                examples=examples,
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
                    "AudioURL": audio_url,
                    "PartOfSpeech": escape(_plain(record.get("fl", "unknown"))),
                    "Examples": "<br>".join(escape(example) for example in examples),
                    "Example": escape(examples[0]) if examples else "",
                },
            )
            notes.append(note)
    return notes, rejected