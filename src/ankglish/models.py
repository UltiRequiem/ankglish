"""Canonical records shared by source adapters and exporters."""

from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256


@dataclass(frozen=True)
class Provenance:
    provider: str
    source_id: str
    source_url: str | None = None
    source_version: str | None = None


@dataclass(frozen=True)
class Pronunciation:
    ipa: str
    dialect: str | None = None
    audio_url: str | None = None
    media_filename: str | None = None
    media_sha256: str | None = None


@dataclass(frozen=True)
class Sense:
    source_id: str
    definition: str
    part_of_speech: str
    examples: tuple[str, ...] = ()
    labels: tuple[str, ...] = ()
    priority: int = 0
    provenance: Provenance | None = None


@dataclass(frozen=True)
class Translation:
    language: str
    definition: str
    examples: tuple[str, ...] = ()
    provider: str | None = None
    provider_version: str | None = None
    attribution: str | None = None


@dataclass(frozen=True)
class WordEntry:
    headword: str
    frequency_rank: int
    frequency_list: str
    senses: tuple[Sense, ...]
    pronunciations: tuple[Pronunciation, ...]
    lemma: str | None = None
    inflection: str | None = None
    provenance: Provenance | None = None


@dataclass(frozen=True)
class DeckNote:
    """A rendered note with identity independent of mutable card wording."""

    note_id: str
    headword: str
    part_of_speech: str
    sense: Sense
    variant: str
    fields: dict[str, str] = field(default_factory=dict)
    translations: tuple[Translation, ...] = ()


def stable_note_id(
    *,
    provider: str,
    entry_id: str,
    sense_id: str,
    headword: str,
    part_of_speech: str,
    schema: str = "deck-note-v1",
    variant: str = "full",
) -> str:
    """Return the deterministic ID for one semantic sense card."""

    semantic_key = "\x1f".join(
        (
            schema,
            variant,
            provider,
            entry_id,
            sense_id,
            headword.casefold(),
            part_of_speech,
        )
    )
    return sha256(semantic_key.encode("utf-8")).hexdigest()
