# ankglish docs

Technical docs for the build pipeline (not the Anki deck itself — see the
[repo README](../README.md) for that).

- [architecture.md](architecture.md) — module map, data flow, design decisions
  (why cache-first, why deterministic IDs).
- [pipeline.md](pipeline.md) — step-by-step trace of `ankglish rebuild`: fetch →
  normalize → quality-filter → export.
- [cli.md](cli.md) — every command and flag, with examples.
- [data-model.md](data-model.md) — core dataclasses (`WordEntry`, `Sense`,
  `DeckNote`, ...) and the note-ID scheme that keeps Anki review history stable
  across rebuilds.
