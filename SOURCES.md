# Source Inventory

This file records the source decisions for the new `ankglish` build. No
generated deck snapshot is checked in.

| Path | Role | Current status |
| --- | --- | --- |
| `tests/fixtures/notes.tsv` | Offline test fixture | Minimal Anki-shaped fixture used only for CLI smoke tests. It is not release content. |

## Providers to pin before a release

- Frequency list: unresolved. The `60k` label is not an authoritative source
  identifier or version.
- Merriam-Webster Learner's Dictionary: intended primary dictionary/audio
  provider, subject to API entitlement, terms, and redistribution permission.
- Kaikki/Wiktionary: intended fallback provider, subject to a pinned dump or
  endpoint revision and per-asset attribution/license records.
- Translation: disabled by default. No project-owned translation source is
  currently approved as a build input.

Every future normalized record and media asset must carry provider identity,
source version or URL, and a checksum where applicable.