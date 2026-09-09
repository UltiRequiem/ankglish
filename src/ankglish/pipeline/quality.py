"""Quality gates for normalized deck notes."""

from __future__ import annotations

from collections import Counter

from ..models import DeckNote


def quality_filter(notes: list[DeckNote]) -> tuple[list[DeckNote], dict[str, int]]:
    accepted: list[DeckNote] = []
    rejected: Counter[str] = Counter()
    seen: set[str] = set()
    for note in notes:
        if note.note_id in seen:
            rejected["duplicate_note_id"] += 1
        elif not note.headword or not note.sense.definition:
            rejected["empty_required_field"] += 1
        else:
            seen.add(note.note_id)
            accepted.append(note)
    return accepted, dict(rejected)
