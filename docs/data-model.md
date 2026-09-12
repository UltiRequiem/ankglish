# Data model

All shared record types live in
[`src/ankglish/models.py`](../src/ankglish/models.py). Everything is a frozen
dataclass — pipeline stages transform data by building new instances, never
mutating in place (except `DeckNote.fields`, a plain mutable `dict` — audio
attachment in `build.py` writes into it after normalization).

## `Provenance`

```python
Provenance(provider: str, source_id: str, source_url: str | None, source_version: str | None)
```

Where a piece of content came from. Attached to a `Sense` (and available on
`WordEntry`), currently always `provider="mwld"`.

## `Pronunciation`

```python
Pronunciation(ipa: str, dialect: str | None, audio_url: str | None,
              media_filename: str | None, media_sha256: str | None)
```

Defined but not yet used at full strength — `pipeline/normalize.py` reads IPA
and derives an audio URL directly from the raw MWLD dict rather than
constructing a `Pronunciation` instance. Present for future multi-dialect /
checksum tracking.

## `Sense`

```python
Sense(source_id: str, definition: str, part_of_speech: str,
      examples: tuple[str, ...], labels: tuple[str, ...],
      priority: int, provenance: Provenance | None)
```

One dictionary definition. A `WordEntry` can have many; each becomes its own
`DeckNote` — see [pipeline.md](pipeline.md#3-normalize).

## `WordEntry`

```python
WordEntry(headword: str, frequency_rank: int, frequency_list: str,
          senses: tuple[Sense, ...], pronunciations: tuple[Pronunciation, ...],
          lemma: str | None, inflection: str | None, provenance: Provenance | None)
```

The intended canonical "one word, fully resolved" record. Like `Pronunciation`,
it's defined for a richer future pipeline (e.g. multi-source merging) but the
current `normalize_entries()` builds `DeckNote`s directly from raw MWLD JSON
rather than assembling a `WordEntry` first.

## `Translation`

```python
Translation(language: str, definition: str, examples: tuple[str, ...],
            provider: str | None, provider_version: str | None, attribution: str | None)
```

Attaches to `DeckNote.translations`. Translations are disabled by default
(`[translations].enabled = false` in `config/default.toml`) and nothing in the
current pipeline populates this tuple — the `Translation` card field exists so
the template's hide/show toggle (`card.js`) has something to target once a
translation source is wired up.

## `DeckNote`

```python
DeckNote(note_id: str, headword: str, part_of_speech: str, sense: Sense,
         variant: str, fields: dict[str, str], translations: tuple[Translation, ...])
```

The unit exporters consume. `fields` holds the exact strings that land in Anki
fields (`Headword`, `Pronunciation`, `Definition`, `Examples`, `Example`,
`AudioURL`, `PartOfSpeech`, and later `Audio`/`AudioPath` once audio is fetched)
— `exporters/apkg.py` reads from `fields` first and falls back to the typed
attributes (`headword`, `sense.definition`, ...) only if a key is missing, which
is why `normalize_entries()` must keep `fields` and the typed attributes in sync
for every field it sets.

## Note identity: `stable_note_id()`

```python
stable_note_id(*, provider, entry_id, sense_id, headword, part_of_speech,
                schema="deck-note-v1", variant="full") -> str
```

Returns
`sha256("\x1f".join([schema, variant, provider, entry_id, sense_id,
headword.casefold(), part_of_speech])).hexdigest()`,
used as the Anki note GUID (`note.guid = deck_note.note_id` in
`exporters/apkg.py`).

Why this matters: Anki matches notes across imports by GUID, not content. As
long as none of the seven inputs change for a given word/sense, re-running
`rebuild` next month and re-importing the new `.apkg` updates existing cards in
place — study history (intervals, ease factors) survives. Bumping `schema` (in
`models.py`, currently `"deck-note-v1"`, also set in `config/default.toml`'s
`[project].schema`) is the deliberate way to force every note to be treated as
new, e.g. after a breaking field-layout change.

`entry_id` and `sense_id` come from MWLD's own `meta.id` and a
`{entry_id}-{index}` suffix per definition (`pipeline/normalize.py`), so they
track MWLD's identity for that headword+sense, not ankglish's.

## Rejection counters

Two dicts get merged into `manifest.json`'s `rejections`:

- `pipeline/normalize.py` → `{"no_entry", "no_definition", "no_pronunciation"}`
  (always present, zero-initialized)
- `pipeline/quality.py` → `{"duplicate_note_id", "empty_required_field"}` (only
  present if non-zero, via `Counter`)

The keys never collide, so the `{**a, **b}` merge in `build.py` is safe by
construction — if you add a new rejection reason, keep it out of both sets'
existing key names.
