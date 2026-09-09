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
- Merriam-Webster Learner's Dictionary: primary dictionary provider, accessed
  with the local/Actions `MWLD_LEARNER_API_KEY`; live access has been smoke
  tested, while production volume and monthly limits remain provider-policy
  constraints.
- Kaikki/Wiktionary: intended fallback provider, subject to a pinned dump or
  endpoint revision and per-asset attribution/license records.
- Translation: disabled by default. Only an explicitly supplied local file is
  supported; no remote translation service is enabled.

MWLD credentials are supplied through `MWLD_LEARNER_API_KEY` and
`MWLD_ELEMENTARY_API_KEY`. They are local/CI secrets, never source metadata.

Every future normalized record and media asset must carry provider identity,
source version or URL, and a checksum where applicable.

## Licensing scope

The code in this repository is MIT licensed (see LICENSE). This repository
contains only the build pipeline — no dictionary text, structured data, or audio
is stored here; the pipeline fetches those at build time.

Generated decks (`.apkg`, distributed via GitHub Releases) contain third-party
content under its own terms, recorded in each release's build report:

- Wiktionary text via Kaikki.org — CC BY-SA 4.0 (attribution + ShareAlike).
- Merriam-Webster Learner's Dictionary definitions and audio — ©
  Merriam-Webster; use governed by the Merriam-Webster Dictionary API Terms of
  Service.
- Wiktionary/Wikimedia Commons audio — per-file license recorded per asset.

Building or redistributing a deck is your responsibility to do in compliance
with those terms.
