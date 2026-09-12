# Pipeline walkthrough: `ankglish rebuild`

Entry point: `rebuild_live()` in
[`src/ankglish/build.py`](../src/ankglish/build.py). This is the path that
produces real decks; `ankglish build` (see [cli.md](cli.md)) is a separate,
offline-only smoke-test path.

```
config/default.toml + .env
        │
        ▼
 1. frequency ranking ──────────── sources/frequency.py (wordfreq)
        │  word list, capped at max_rank
        ▼
 2. dictionary fetch ───────────── sources/fetch.py + sources/mwld.py
        │  per-word JSON, cache-first, thread-pooled
        ▼
 3. normalize ──────────────────── pipeline/normalize.py
        │  raw MWLD JSON → one DeckNote per sense
        ▼
 4. quality filter ─────────────── pipeline/quality.py
        │  drop dup note_id / empty required fields
        ▼
 5. audio fetch (if embedding) ─── sources/fetch.py (fetch_audio_many)
        │  attach [sound:...] + local path to each note
        ▼
 6. standard-deck reduction ────── build.py (first sense per headword)
        ▼
 7. export ─────────────────────── exporters/apkg.py + exporters/notices.py
        │  full.apkg, standard.apkg (+ -online variants), manifest.json,
        │  ATTRIBUTION.md
        ▼
     dist/
```

## Step by step

### 1. Frequency ranking

`sources/frequency.py::english_words(max_rank)` iterates `wordfreq`'s English
wordlist, keeping only lowercase alphabetic entries, and assigns rank by
position (1 = most frequent). This is deterministic given a pinned `wordfreq`
version (pinned via `uv.lock`), so re-running produces the same candidate list.

### 2. Dictionary fetch

`sources/fetch.py::fetch_mwld()` runs one `ThreadPoolExecutor` job per word:

- Cache hit (`data/cache/mwld/<safe_word>.json` exists, no `--refresh`) → read
  from disk, no network.
- Cache miss / `--refresh` → call `MWLDClient.fetch(word)`
  ([`sources/mwld.py`](../src/ankglish/sources/mwld.py)), write the raw JSON to
  cache.
- `--offline` → cache miss is a hard failure for that word (`missing_cache`),
  never falls through to network. `rebuild_live` then raises if _any_ word the
  offline build needs is missing — offline builds are meant to be reproducible
  from a cache someone already populated.

`MWLDClient.fetch` retries up to 3 times with exponential backoff on HTTP or
shape errors, then raises `MWLDRequestError`. Per-word failures don't abort the
run — they're collected into a `failures` dict and reported in `manifest.json`'s
`failed_words` count.

Concurrency is `--concurrency` (CLI) → `max_concurrency` param → falls back to
`config.dictionary_max_concurrency` (`[sources.dictionary].max_concurrency` in
`config/default.toml`, default 8).

### 3. Normalize

`pipeline/normalize.py::normalize_entries()` takes the first MWLD entry per word
(`records[0]`) and requires:

- at least one pronunciation with an `ipa` field (else `no_pronunciation`)
- at least one non-empty `shortdef` (else `no_definition`)

For each `shortdef`, it emits one `DeckNote` (see
[data-model.md](data-model.md)) with a stable `note_id`, HTML-escaped fields,
and up to 6 example sentences scraped out of the nested `def` structure (MWLD
markup tokens like `{it}`, `{b}`, `{ldquo}` are stripped). The headword audio
URL is derived from the pronunciation's `sound.audio` id using MW's static asset
convention (`.../soundc11/<first-char>/<id>.wav`).

### 4. Quality filter

`pipeline/quality.py::quality_filter()` is a second, cheap gate after
normalization: drops any note whose `note_id` collides with one already seen
(`duplicate_note_id`) or whose `headword`/`definition` ended up empty
(`empty_required_field`). Both counts flow into the manifest's `rejections`.

### 5. Audio fetch (embed / both media modes)

Only runs when `--media` is `embed` or `both`. `fetch_audio_many()` deduplicates
URLs across notes, downloads each once (`fetch_audio()` checks `content-type`
starts with `audio/` before accepting a response), caches to
`data/cache/mwld/audio/`, and writes the resulting `AudioPath` back onto every
note that shares that URL. `--refresh-audio` forces re-download; plain
`--refresh` does not touch audio (URLs rarely change).

### 6. Standard-deck reduction

No re-fetch: `rebuild_live` walks `full_notes` in order and keeps the first note
per case-folded headword. Because `full_notes` preserves MWLD's sense order,
"first sense" is MWLD's own primary sense.

### 7. Export

`exporters/apkg.py::export_apkg()` builds one `genanki.Model` (shared field
list, one template pair) and one `genanki.Deck` per variant, then writes the
`.apkg`. `_export_pair()` in `build.py` does this twice when `--media both`:
once with embedded `Audio`/`AudioPath` fields, once after swapping `Audio` to a
remote `<audio src=...>` tag for the `-online` suffix files.

Finally, `manifest.json` (build stats: counts, rejections, media mode) and
`ATTRIBUTION.md` (see
[architecture.md](architecture.md#attribution-is-generated-not-hand-maintained))
are written to `--output-dir`.

## Progress reporting

Both the dictionary fetch and audio fetch stages print throughput lines
(`Progress: 1234/60000 (2.1%) ... rate=... eta=...`) every 100 items, on the
first item, the last item, or any failure — see the `report`/`audio_report`
closures in `build.py`. This is stdout-only; there's no structured log output to
parse.
