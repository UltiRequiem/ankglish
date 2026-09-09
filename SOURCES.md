# Source Inventory

This file records the source decisions for the new `ankglish` build. No
generated deck snapshot is checked in.

| Path                       | Role                 | Current status                                                                        |
| -------------------------- | -------------------- | ------------------------------------------------------------------------------------- |
| `tests/fixtures/notes.tsv` | Offline test fixture | Minimal Anki-shaped fixture used only for CLI smoke tests. It is not release content. |

## Providers to pin before a release

- Frequency list: `wordfreq`, pinned through `uv.lock`; English wordlist
  iteration and Zipf scores provide deterministic ranking, capped at 60,000 by
  default. Monthly dependency refreshes update this source explicitly. The
  package is an input dependency, not a claim that the old snapshot's frequency
  labels were authoritative.
- Merriam-Webster Learner's Dictionary: intended primary dictionary/audio
  provider, subject to API entitlement, terms, and redistribution permission.
- Kaikki/Wiktionary: intended fallback provider, subject to a pinned dump or
  endpoint revision and per-asset attribution/license records.
- Translation: disabled by default. Only an explicitly supplied local file is
  supported; no remote translation service is enabled.

MWLD credentials are supplied through `MWLD_LEARNER_API_KEY` and
`MWLD_ELEMENTARY_API_KEY`. They are local/CI secrets, never source metadata.

Every future normalized record and media asset must carry provider identity,
source version or URL, and a checksum where applicable.
