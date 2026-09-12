# Architecture

ankglish is a build pipeline, not a runtime app. It runs once (locally, or in CI
on a monthly schedule) and produces `.apkg` files. Nothing it does happens
inside Anki at review time except the card templates and their small toggle
script.

## Module map

```
src/ankglish/
├── cli.py              argparse entry point (validate / build / rebuild)
├── build.py             orchestrates the pipeline: build_tsv, rebuild_live
├── config.py             loads config/default.toml + .env into BuildConfig
├── models.py             shared dataclasses + stable_note_id()
├── validation.py         sanity checks for the offline TSV fixture path
├── languages/
│   ├── base.py            LanguageProfile contract (frequency, dictionary
│   │                      client, normalize) the generic pipeline depends on
│   ├── english.py         ENGLISH profile: wires wordfreq + MWLD + normalize
│   └── __init__.py        resolve_language(code) — the only place that knows
│                          which language codes exist
├── sources/
│   ├── frequency.py       wordfreq -> ranked English word list
│   ├── mwld.py            Merriam-Webster Learner's Dictionary HTTP client
│   └── fetch.py           disk cache + thread-pool concurrency around mwld/audio
├── pipeline/
│   ├── normalize.py       raw MWLD JSON -> DeckNote (one per sense)
│   └── quality.py         drop duplicates / empty-field notes
└── exporters/
    ├── apkg.py            DeckNote list -> genanki .apkg file
    └── notices.py         ATTRIBUTION.md + in-deck description text
```

`templates/` (mirrored under `src/ankglish/templates/` for the installed wheel —
see [Two copies of templates](#two-copies-of-templates)) holds the Anki card
HTML/CSS/JS, not Python.

## Two build commands, two purposes

`ankglish` has two independent code paths, picked by CLI subcommand:

- **`build`** (`build_tsv`) — deterministic, offline, no network. Takes a
  pre-made TSV (default: the test fixture), sorts it, hashes it. Used for CLI
  smoke tests and reproducibility checks, not for producing a real deck.
- **`rebuild`** (`rebuild_live`) — the real pipeline. Hits the network (or an
  on-disk cache), talks to MWLD, downloads audio, normalizes, quality-filters,
  exports `.apkg`. This is what `build-release.yml` runs monthly.

See [pipeline.md](pipeline.md) for the `rebuild` walkthrough and
[cli.md](cli.md) for flags on both.

## Language is explicit, English is the only one implemented

`build.py` never imports `wordfreq`, MWLD, or `normalize_entries` directly. It
calls `resolve_language(config.target_language)` (`languages/__init__.py`) to
get a `LanguageProfile` — a small bundle of `frequency`,
`build_dictionary_client`, and `normalize` callables — and drives the pipeline
through that. `config/default.toml`'s `[project].language` (default `"en"`)
selects it; `languages/english.py` is where the English-specific providers
(wordfreq's `"en"` list, `MWLDClient`, MWLD normalization) actually get composed
together.

This exists so a second language would be a new `languages/<code>.py` module
plus an entry in `resolve_language`'s table, not changes to `build.py`. No
second language is implemented today — only `"en"` resolves.

## Design decisions worth knowing

**Cache-first fetching.** `sources/fetch.py` writes every MWLD response to
`data/cache/mwld/<word>.json` and every audio file to `data/cache/mwld/audio/`.
A rebuild without `--refresh` reuses the cache, so local iteration and
`--offline` CI runs cost no API calls. `--refresh` forces new JSON;
`--refresh-audio` separately forces new audio (kept separate because audio URLs
are stable and re-downloading is rarely needed).

**Deterministic note IDs.** Anki tracks review history (intervals, ease) per
note GUID. `models.stable_note_id()` hashes
`(schema, variant, provider, entry_id, sense_id, headword, part_of_speech)` into
a sha256 GUID. As long as MWLD's entry/sense IDs don't change, the same word
keeps the same GUID release over release — re-importing a new monthly `.apkg` in
Anki updates content in place instead of duplicating cards. This is also why
`pipeline/quality.py` treats a repeated `note_id` as a rejection
(`duplicate_note_id`), not silent overwrite.

**One note per sense, not per word.** `pipeline/normalize.py` emits one
`DeckNote` per dictionary sense (definition), all sharing one headword and IPA.
The **full** deck keeps every sense; the **standard** deck (`rebuild_live` in
`build.py`) keeps only the first sense per headword (case-folded), giving a
smaller "one card per word" deck from the same fetched data — no separate fetch
or normalize pass.

**Embed vs. link media.** `--media embed` (default) downloads audio and packages
it inside the `.apkg` (works offline in Anki, larger file). `--media link` skips
download and points `<audio>` at the remote MW URL (small file, needs network to
play). `--media both` builds both variants per deck size (`ankglish-full.apkg` +
`ankglish-full-online.apkg`, etc.) in one run, reusing the already-fetched notes
— see `_export_pair` in `build.py`.

**Attribution is generated, not hand-maintained.** `exporters/notices.py` reads
the build manifest (counts of fetched/audio records) to decide which sources
were _actually used_ in a given build, so `ATTRIBUTION.md` can never claim a
source that isn't in the deck. This matters because MWLD content is
`© Merriam-Webster`, not open-licensed — see [SOURCES.md](../SOURCES.md).

### Two copies of templates

`exporters/apkg.py::_template()` looks in `templates/` (repo root) first and
falls back to `src/ankglish/templates/` (packaged with the wheel per
`pyproject.toml`'s `artifacts = ["templates"]`). Both must stay identical —
running from a checkout uses the root copy; running from an installed package
uses the packaged copy. There's no automated sync step, so if you edit a
template, edit both, or diff them before committing:

```sh
diff templates/card-back.html src/ankglish/templates/card-back.html
```

## Non-Python runtime: the card itself

`card-back.html` embeds `card.js` (as the `CardScript` note field) to add a
"Show translation" toggle button — the `Translation` field starts hidden and is
revealed on click, so translation-less decks show nothing extra. The templates
use Anki's mustache-style `{{Field}}` / `{{#Field}}...{{/Field}}` syntax;
`{{#Field}}` sections render only when the field is non-empty, which is how
`PartOfSpeech`, `Example`, and `Translation` stay invisible on notes that don't
have them.
