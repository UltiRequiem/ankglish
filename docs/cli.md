# CLI reference

Entry point: `ankglish` (installed via `pip install .`, maps to
`ankglish.cli:main` per `pyproject.toml`). Source:
[`src/ankglish/cli.py`](../src/ankglish/cli.py).

```sh
ankglish --version
ankglish <command> [flags]
```

With no command, prints `--help` and exits 0.

## `ankglish validate`

Checks that an input file looks like the offline TSV fixture format (has a
`#separator:Tab` directive, at least one data row, every data row contains a
tab). This is a smoke check for `tests/fixtures/notes.tsv`, not a schema
validator for real deck data.

| Flag      | Default                    | Meaning       |
| --------- | -------------------------- | ------------- |
| `--input` | `tests/fixtures/notes.tsv` | File to check |

Exit 1 and prints each error if invalid; exit 0 and prints `Found input: <path>`
if valid.

## `ankglish build`

Deterministic, offline, no network — see
[architecture.md](architecture.md#two-build-commands-two-purposes). Sorts and
rewrites the input TSV per variant, writes `manifest.json` with a sha256 per
output file. This does **not** produce `.apkg` files or talk to MWLD; it's for
CLI/reproducibility tests only.

| Flag           | Default                    | Meaning                       |
| -------------- | -------------------------- | ----------------------------- |
| `--input`      | `tests/fixtures/notes.tsv` | Source TSV                    |
| `--config`     | `config/default.toml`      | Config file                   |
| `--output-dir` | `dist`                     | Where outputs land            |
| `--variant`    | `both`                     | `full`, `standard`, or `both` |

```sh
ankglish build --variant standard --output-dir /tmp/out
```

## `ankglish rebuild`

The real pipeline: fetch → normalize → quality-filter → export. See
[pipeline.md](pipeline.md) for what each stage does.

| Flag                  | Default                                   | Meaning                                                    |
| --------------------- | ----------------------------------------- | ---------------------------------------------------------- |
| `--config`            | `config/default.toml`                     | Config file                                                |
| `--output-dir`        | `dist`                                    | Where `.apkg`/`manifest.json`/`ATTRIBUTION.md` land        |
| `--cache-dir`         | `data/cache/mwld`                         | Dictionary + audio cache root                              |
| `--max-rank`          | config's `frequency_max_rank` (60000)     | Cap on how many frequency-ranked words to fetch            |
| `--refresh`           | off                                       | Force fresh MWLD JSON, bypass cache                        |
| `--refresh-audio`     | off                                       | Force fresh audio download, bypass cache                   |
| `--offline`           | off                                       | Never hit network; fail if any needed word isn't cached    |
| `--concurrency`       | config's `dictionary_max_concurrency` (8) | Parallel dictionary requests                               |
| `--audio-concurrency` | same as `--concurrency`                   | Parallel audio downloads                                   |
| `--media`             | `embed`                                   | `embed` (package audio), `link` (remote `<audio>`), `both` |

`--refresh` and `--offline` are mutually exclusive (checked in `cli.py` before
calling `rebuild_live`; fails fast with exit 1).

```sh
# Local iteration against whatever is already cached, no network:
ankglish rebuild --offline --max-rank 2000

# Full monthly refresh (what build-release.yml runs):
ankglish rebuild --refresh --media both --max-rank 60000 \
  --concurrency 8 --audio-concurrency 16
```

Requires `MWLD_LEARNER_API_KEY` in the environment (or `.env`) for any network
path — see [config/default.toml](../config/default.toml)'s `[credentials]`
section and [SOURCES.md](../SOURCES.md).

On success, prints a one-line summary:

```
Built full=<N> standard=<N> from fetched=<N> failed=<N>
```

## CI usage

- `ci.yml` runs `ruff check`, `ruff format --check`, and `pytest` on every PR
  and push to `main` — no `rebuild` involved, so it never needs API credentials.
- `build-release.yml` runs monthly (`workflow_dispatch` also available), calls
  `ankglish rebuild --refresh --media both`, then on schedule (or when
  `publish: true` is passed) creates a GitHub release tagged `vYYYY.MM` with the
  `dist/` artifacts attached. It refuses to overwrite an existing tag for the
  same month.
