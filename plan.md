# Automated Anki Deck Rebuild Plan

## 1. Goal and current state

Turn this repository from a checked-in generated deck snapshot into a
reproducible, inspectable build system for high-quality English pronunciation
Anki decks.

The first supported product remains English pronunciation and vocabulary. A
rebuild must be able to:

- fetch the newest supported frequency, dictionary, IPA, and audio data;
- normalize and validate it into a versioned intermediate dataset;
- generate an Anki-importable CSV and, preferably, an `.apkg` release;
- generate both a complete deck and a smaller study-focused deck;
- leave translations out by default, with an explicitly selected optional
  provider and target language;
- run locally through a CLI and remotely through GitHub Actions;
- publish immutable release assets and a changelog when the generated deck
  changes.

The previous generated snapshot has been removed. The README documents
Merriam-Webster Learner's Dictionary (MWLD) and Kaikki/Wiktionary as candidate
sources, but the authoritative frequency source, provider cache, templates, and
release generator still need to be established. No legacy generated data is a
build input.

## 2. Decisions to make before implementation

Resolve these decisions in the first implementation milestone and record the
result in the README and a source manifest:

1. **Authoritative word list:** identify the exact frequency list and its
   license, URL, version, and ranking semantics. Do not call the existing `60k`
   label a source until the input is identified and pinned.
2. **Dictionary access:** confirm the official MWLD API entitlement, key
   handling, request limits, caching behavior, and service terms. Prefer
   Merriam-Webster definitions, examples, IPA, and audio as the primary source.
   Never commit the API key, and make provider failures visible in build
   reports.
3. **Wiktionary fallback:** use a pinned Kaikki/Wiktionary dump or documented
   endpoint for fields MWLD cannot provide, retain attribution/source metadata,
   and prefer free accessible fallback audio only when MWLD audio is
   unavailable.
4. **Audio redistribution:** package the preferred Merriam-Webster media in the
   `.apkg` when available, with Wiktionary or another stable free source as
   fallback. Keep provider URLs in provenance and make source failures
   actionable without making the deck architecture depend on a single provider
   being perfect forever.
5. **Anki packaging:** use `genanki` or another maintained package builder only
   after confirming its support for the required note type, media, deck
   hierarchy, and stable IDs. CSV remains a supported fallback and inspection
   artifact. For compatibility with the current file, decide explicitly whether
   generated TSV includes Anki directives (`#separator`, `#html`,
   `#notetype column`, `#deck column`, and `#tags column`) or whether those
   settings move to a separate import guide; test the chosen path with a real
   Anki import fixture.
6. **Translation policy:** default to no translation. Define a provider
   interface for user-supplied/local files or an explicitly enabled non-Google
   provider, with language, attribution, and licensing metadata. A build with no
   translation provider must still produce a complete deck.
7. **Runtime audio policy:** default to locally packaged headword audio. Make
   example-sentence TTS disabled by default and opt-in per user/provider; use an
   approved-provider allowlist, verify output-license terms and data handling,
   obtain explicit consent before sending sentence text, and handle failure
   offline. Do not make reviews depend on an undocumented third-party service.

For Kaikki/Wiktionary, record the exact dump URL, revision/date, transformation
notice, and file-level source metadata for every fallback asset. Generate useful
attribution in each release bundle rather than relying only on the repository
README. For the official deck, the project owner has confirmed permission for
the selected media and providers; retain source metadata for operational
traceability without turning licensing review into a routine release blocker.

Maintain source/provider metadata at field and asset level for frequency data,
MWLD definitions/examples/branding/audio, Wiktionary text, each media file,
translations, templates, and original code. The official-deck permission
decision is an explicit project assumption; source metadata remains valuable for
debugging, attribution, provider replacement, and future maintenance. Provider
outages or missing fallback fields should be reported and handled by quality
rules, not hidden.

The former generated snapshot was removed before migration. Do not recreate or
automatically carry generated material into a new release. Identify the exact
frequency source/version before making coverage claims, keep translations
disabled by default, and document opt-in TTS only after that policy is
implemented.

## 3. Target repository layout

Adopt a small Python build project with a clear distinction between source,
generated data, and release output:

```text
.
├── .github/workflows/build-release.yml
├── src/ankglish/
│   ├── cli.py
│   ├── config.py
│   ├── models.py
│   ├── sources/
│   │   ├── frequency.py
│   │   ├── mwld.py
│   │   ├── kaikki.py
│   │   ├── audio.py
│   │   └── translations.py
│   ├── pipeline/
│   │   ├── fetch.py
│   │   ├── normalize.py
│   │   ├── quality.py
│   │   ├── dedupe.py
│   │   ├── variants.py
│   │   └── manifest.py
│   └── exporters/
│       ├── csv.py
│       └── apkg.py
├── templates/
│   ├── card-front.html
│   ├── card-back.html
│   ├── styles.css
│   └── media/
├── tests/
│   ├── fixtures/
│   ├── test_normalization.py
│   ├── test_quality.py
│   ├── test_variants.py
│   ├── test_csv_export.py
│   └── test_reproducibility.py
├── data/                  # cache/intermediate data; ignored by default
├── dist/                  # generated local outputs; ignored by default
├── pyproject.toml
├── uv.lock                # or the repository's chosen lockfile
├── config/default.toml
├── SOURCES.md
├── CHANGELOG.md
└── README.md
```

Do not add a second generated snapshot during migration. Templates, caches, and
release outputs belong under the new layout and must have explicit provenance.

## 4. Canonical data model and provenance

Create typed records for:

- `WordEntry`: normalized spelling, frequency rank/list, lemma or headword, part
  of speech, inflection metadata, and source provenance;
- `Sense`: stable source ID, definition HTML/text, labels, usage/register, sense
  priority, examples, and source URL;
- `Pronunciation`: IPA, dialect/region, audio source URL, local media filename,
  checksum, and license/attribution;
- `Translation`: target language, translated definition/examples, provider
  ID/version, and attribution;
- `DeckNote`: stable note ID, schema version, variant, all rendered fields, and
  source fingerprints.

Store provenance in the intermediate data and in a machine-readable
`manifest.json`. The manifest should include input URLs/versions, retrieval
timestamps, checksums, generator source digest, generator code revision, release
package version, configuration hash, record/card counts, omitted-card counts by
reason, provider metadata, and license/attribution notes. Compute the generator
source digest from the generator, templates, lockfile, and build configuration
while excluding release-only version/changelog files and workflow metadata.
Define the candidate/release content fingerprint from pinned source checksums,
canonical data, configuration, schema, template content, and that generator
source digest while excluding retrieval timestamps and the release package
version. Keep those volatile/release fields in the human-audit manifest but out
of the reproducible manifest checksum.

For Anki note identity, do not hash the rendered question or full card HTML:
wording, formatting, translations, and template improvements are mutable fields
that should update an existing note. Instead derive a stable semantic key from
the provider namespace, source entry ID, source sense ID, normalized
headword/POS, and schema identity, then hash that key with SHA-256 (or an
equivalent deterministic digest) and encode it as the note GUID. Use a separate
variant/configuration namespace when full and standard decks must coexist
without collisions. Define and test deterministic algorithms for numeric Anki
note/card IDs, notetype IDs, deck/subdeck IDs, and card ordinals. Document a
migration map from legacy note IDs if preserving update continuity is required.
Prove with repeated APKG builds that updates do not create duplicate
notes/cards, and prove that changing a definition, template, translation, or
audio URL updates the existing note rather than creating a new one.

Treat HTML from sources as untrusted input. Sanitize/allowlist the markup
required by the card template, escape CSV fields correctly, validate URLs, and
never interpolate source text into executable JavaScript without safe encoding.

## 5. Fetch and normalization pipeline

Implement the pipeline as explicit, resumable stages so a failed API request
does not require starting over:

1. Load configuration and validate credentials before network work.
2. Fetch and verify the pinned frequency source; cache raw responses/dumps with
   checksums and license metadata.
3. Fetch MWLD entries in bounded, rate-limited batches with retries, exponential
   backoff, timeouts, and a persistent cache. Respect API terms and never log
   secrets.
4. Fetch Kaikki/Wiktionary only for missing permitted fields such as IPA/audio,
   preserving the exact source revision/dump date.
5. Normalize orthography, POS labels, IPA, audio references, labels,
   definitions, examples, and line breaks into the canonical model.
6. Match fallback data conservatively. Never attach an audio file or sense to a
   different homograph solely because the spelling matches.
7. Download allowed audio into a content-addressed media cache, verify content
   type and checksum, and reject corrupt/oversized/unlicensed files. Store
   remote URLs only as provenance; for APKG output, convert packaged audio to
   deterministic safe filenames and `[sound:filename]` field references.
8. Produce a normalized snapshot before filtering so the quality report can
   explain every omission.

The pipeline must support offline rebuilds from cached/pinned inputs for tests
and emergency releases. Network freshness should be explicit, not an accidental
property of every CLI invocation. In GitHub Actions, runners are ephemeral:
persist only permitted raw/source snapshots through digest-keyed Actions
artifacts or another documented private store, and let scheduled builds refresh
sources explicitly. Document local cache location, restrictive filesystem
permissions, retention/deletion, access control, cache-key isolation, and
artifact expiry. Reject or redact credential-bearing URLs, authorization
headers, signed URLs, and failed-request payloads before they enter cache
metadata. Never put licensed raw responses, credentials, request headers, or
secrets in release artifacts.

## 6. Quality gates and deduplication

The quality filter is a first-class feature because a smaller, reliable deck is
preferable to a large noisy one. Generate a report in every build with accepted,
rejected, and downgraded records.

Minimum gates:

- non-empty normalized headword, definition, and usable pronunciation data;
- valid source identity and provenance for every accepted sense;
- no duplicate stable note IDs or duplicate `(headword, POS, sense identity)`
  records;
- reject malformed HTML, placeholder definitions, broken URLs, unsupported
  scripts, and examples that are empty after cleanup;
- reject entries with no usable audio from the default pronunciation variants.
  If a no-audio variant is ever offered, put it in a separately named,
  non-default output with its own count and threshold rather than mixing it into
  the pronunciation deck;
- normalize whitespace/case/HTML before comparing content;
- detect duplicate examples and near-duplicate definitions;
- cap pathological example counts and strip dictionary editorial artifacts only
  with tested rules;
- enforce source-specific limits and fail loudly on suspiciously low fetch
  counts.

Use conservative matching and deterministic thresholds. Add fixture tests for
homographs, inflections, abbreviations, duplicate senses, missing audio,
malformed markup, and source outages. Do not silently turn an upstream outage
into a release with thousands of missing cards.

### Variants

Generate two named variants from the same accepted canonical dataset:

- **full:** all accepted useful senses/cards, retaining atomic sense cards and
  existing `core`, `extend`, and `rare`-style priority tags where the source
  supports them;
- **standard:** a lower-volume study set selected by deterministic rules: retain
  the highest-priority sense(s) per lemma/POS, collapse only genuinely redundant
  family members, preserve high-frequency irregular meanings, and cap closely
  related derivations per word family.

Do not reduce the standard variant with a naive stemmer alone. Start with
explicit source lemma/related-form data, then add a reviewed heuristic fallback.
Record why each card was excluded from standard so users can audit or change the
policy. Use frequency rank and sense priority as tie-breakers. Keep the full
variant available for users who want maximum coverage.

## 7. CLI contract

Provide a documented executable, for example `uv run ankglish`, with
subcommands:

```text
ankglish fetch [--refresh] [--check-cache]
ankglish validate [--input PATH]
ankglish build [--variant full|standard|both]
ankglish rebuild --refresh --variant full|standard|both
ankglish build --with-translations --translation-file PATH --target-language CODE
ankglish report [--input PATH]
ankglish clean-cache
```

Recommended build options:

- `--config PATH` and `--output-dir PATH`;
- `--variant full|standard|both`;
- `--max-rank N` or a named frequency range;
- mutually exclusive `--refresh`, `--offline`, and `--check-cache` modes.
  `build --offline` must fail if a required pinned input is missing; `--refresh`
  must be rejected with `--offline`;
- `--with-translations` only when a translation provider/file is explicitly
  selected;
- `--translation-provider ID --target-language CODE` for a configured provider,
  or `--translation-file PATH --target-language CODE` for user-owned
  translations. `--target-language` alone never enables translations; reject it
  without `--with-translations` plus a provider/file, reject provider and file
  together unless explicitly supported, and record provider/version/source
  metadata in the manifest. Project-owned translation inputs are assumed
  approved for this official deck; test the complete option truth table;
- `--format csv|apkg|both`;
- `--reproducible` to normalize timestamps/order and produce byte-stable outputs
  where possible;
- `--fail-on-warnings` for CI.

`rebuild` must perform refresh, normalization, validation, quality filtering,
and export in one command. The CLI must print a summary, output paths, source
versions, and quality counts. Exit nonzero for credential errors, schema errors,
integrity failures, or quality thresholds that indicate a broken upstream.

## 8. Templates and card UX

Migrate the current templates carefully and remove the hardcoded Chinese
assumption:

- make translation fields conditional and language-neutral
  (`TranslationDefinition`, `TranslationExampleN`, plus a language label/data
  attribute). Store sanitized card HTML separately from plain text, escape every
  text/attribute context, and test quotes, `<`, `>`, and missing translations in
  both exporters;
- hide the translation control entirely when no translation fields exist;
- make the default card fully usable offline with packaged headword audio;
- replace inline `onclick` handlers with small, idempotent scripts and
  accessible buttons (`button`, `aria-label`, keyboard focus, visible focus
  state);
- preserve Anki night-mode compatibility, responsive layout, and safe handling
  of empty fields;
- ensure the front random example selection is deterministic per card/review
  when practical, or at least does not use `Date.now()` in a way that makes
  debugging impossible;
- remove reliance on remote logos/assets by packaging permitted assets or using
  text/CSS that does not infringe source branding requirements;
- make example TTS disabled by default and visibly nonessential, with
  timeout/error handling, an approved configurable provider endpoint, explicit
  consent, a privacy/retention disclosure, and a local/offline alternative where
  feasible. Never ship hard-coded personal service endpoints. Do not cache or
  package TTS-generated audio by default; if an opt-in provider permits
  redistribution, isolate that cache from licensed source caches and record its
  terms, retention, and deletion policy;
- add a translation toggle that works for any configured language, not a
  `zh-Hans`-specific implementation;
- sanitize or encode data before placing it into `data-*` attributes or HTML.

Use a small representative fixture deck to manually inspect desktop/mobile and
Anki light/dark rendering. Add template regression checks that render notes with
missing optional fields and translation enabled/disabled.

## 9. CSV and APKG outputs

Keep CSV as a stable interchange artifact because it is easy to inspect and
import, but define it as a fresh-import/inspection format only. CSV cannot
reliably carry Anki note GUIDs, notetype IDs, deck hierarchy, templates, media,
or update semantics; APKG is the only update-capable artifact unless a separate
importer is built around a documented stable-key column. Correct the misleading
extension/configuration mismatch by either:

- emitting a true comma-separated CSV with documented quoting; or
- emitting a clearly named `.tsv` and documenting the Anki import settings.

Include a header/schema manifest and deterministic column order. Preserve Anki
notetype/deck/tag metadata in a separate import guide; CSV alone cannot carry
all template/media configuration safely.

Build `.apkg` as the primary end-user artifact once the package exporter is
tested. It should include:

- a versioned notetype and templates;
- the selected deck variant and frequency subdecks;
- packaged audio/media with deterministic names and `[sound:filename]`
  references that are checked against the APKG media map;
- stable note/card IDs so updates do not create unnecessary duplicates;
- deck configuration suitable for a fresh import;
- a manifest and license/attribution note where the package format permits it.

Do not commit large generated CSV/APKG files by default. Commit only source
code, templates, lockfiles, small fixtures, and manifests. Publish generated
outputs to GitHub Releases together with `manifest.json`, a generated
`NOTICE`/attribution file, source/provider records, and checksums. The
official-deck permission assumption applies to release packaging; provider
metadata should still make every artifact auditable and replaceable. Optionally
retain a tiny sample output for smoke tests.

## 10. GitHub Actions and releases

Add `.github/workflows/build-release.yml` with:

- `workflow_dispatch` inputs for variant, max rank, translation mode, refresh
  mode, and whether to publish;
- a scheduled run, initially weekly or monthly rather than every few months,
  with the schedule documented and adjustable. Scheduled runs explicitly invoke
  `rebuild --refresh --variant both`; manual runs expose the same refresh and
  variant choices;
- a `workflow_dispatch` input set covering refresh mode, variant, max rank,
  translation enabled/disabled, target language, translation provider, and
  publish/dry-run; translations default to disabled and inputs are validated
  before network work. Do not accept arbitrary local paths or secret-bearing
  file content on the runner: support only a checked-in file at a pinned commit
  or a documented secure artifact/reference with a checksum;
- a normal push/PR validation job that uses fixtures and offline mode only;
- separate read-only build/quality jobs and a protected publish job. GitHub
  permissions are job-scoped, so only the publish job declares
  `permissions: contents: write`; the build jobs have no write permission;
- pinned or dependabot-managed action versions, explicit Python/dependency
  versions, caching, concurrency cancellation, and artifact retention;
- explicit checkout with the required full history/tags, Git identity setup,
  release lookup/API or CLI setup, and checks that the target tag/release does
  not already exist;
- secrets supplied through GitHub Actions secrets/environment, never repository
  files or logs;
- a quality gate comparing the new manifest/report with the previous successful
  release and rejecting suspicious cardinality or coverage changes;
- upload of CSV/TSV, APKG, mandatory `NOTICE`, manifest, quality report, and
  checksums as workflow artifacts and release assets. The candidate
  build/quality jobs must produce a manifest fingerprint before any version
  bump; the final publish build must run after the version commit and publish
  only its own validated outputs.

For scheduled/manual successful builds, use this atomic release model: a
protected publish job uses one shared concurrency key for scheduled/manual runs
with `cancel-in-progress: false`, re-fetches and verifies the branch, tag, and
release state immediately before changes, and compares the candidate manifest
fingerprint with the latest release before changing version files. The candidate
manifest, pinned source snapshot, cache digests, configuration, and translation
inputs must be immutable workflow outputs reused by the final build; the final
fingerprint must match the approved candidate fingerprint before publishing. If
there is no meaningful change, stop without a commit or release. If there is a
change, compute the next version from `pyproject.toml`, commit the
version/changelog update, push that commit, run a final build and validation
from that exact commit using the candidate snapshot, create the tag from that
exact commit, and publish only those final validated outputs. Exclude the bot's
version/changelog commit from the normal publish trigger by path or an
unambiguous commit marker, while still running read-only validation. If
repository policy disallows automated commits, the publish job fails with a
documented manual-release instruction rather than silently creating an untracked
version. In either model:

1. Avoid releases when no meaningful deck/source change occurred, unless forced.
2. Bump the minor version for a data refresh according to the selected policy.
3. Upload both `full` and `standard` assets for scheduled/default releases; an
   explicitly selected manual variant may publish only that variant and must say
   so in the release notes.
4. Record source versions and build configuration in release notes.

Because the current directory is not a Git checkout, repository initialization,
remote setup, protected tags/environments, and GitHub token/repository
permissions must be completed before this workflow can operate. Use the built-in
`GITHUB_TOKEN` only with the minimum documented permissions where repository
policy permits it; otherwise document the fine-grained token and fail closed
when release metadata or permissions are unavailable. Use unique versioned asset
names, reject existing tags/releases, protect tags/environments, and publish
corrections as new releases; GitHub assets are not intrinsically immutable.

Use semantic-version rules: data/source refreshes are minor bumps,
backward-compatible build/template fixes are patch bumps, and schema/Anki
identity migrations are major bumps. For a partial failure after a commit, tag,
or upload, reconcile by checking the existing state, never reuse a version, and
resume or mark the run failed before retrying. Add a documented procedure for
license changes, source takedowns, and release withdrawal: mark the affected
release withdrawn, remove/disable assets where possible, publish a withdrawal
notice and replacement mapping, block the affected source/version, and retain an
audit record. Treat GitHub immutability as policy, not a platform guarantee;
corrections use new releases.

## 11. Testing and verification

Add tests before enabling scheduled publishing:

- unit tests for parsing, normalization, escaping, deduplication, variant
  selection, stable IDs, and quality thresholds;
- fixture-based source adapter tests with mocked HTTP responses, retries, rate
  limits, and malformed upstream data;
- golden tests for CSV/TSV schema and representative rendered templates;
- APKG smoke test that opens/imports the package and verifies note count, media
  references, notetype fields, and deck names;
- reproducibility test: same pinned inputs/config produce identical normalized
  records, IDs, ordering, and checksums (excluding explicitly documented
  timestamps);
- byte-identical CSV/APKG output tests where the format permits, cross-variant
  ID-collision tests in one Anki collection, and no-release/recovery tests for
  unchanged input and partial publication states;
- offline build test for CI;
- CLI exit-code tests for missing credentials, empty source data, partial source
  failures, and optional translation absence;
- workflow linting and a dry-run/manual execution against fixtures;
- a final manual Anki check for audio playback, missing-audio behavior,
  translation toggle, night mode, accessibility, and update/import behavior.
- secret scanning and redaction checks proving that credentials, authorization
  headers, signed URLs, and private cache metadata are absent from logs,
  manifests, caches, and release assets;

Set practical CI thresholds: no duplicate IDs, no broken media references, no
schema drift without an explicit migration, and no release when accepted-card
count changes beyond a configured percentage without an override.

## 12. Migration sequence

1. Add project metadata, lockfile, configuration, source/license manifest, and
   fixture tests without deleting the current snapshot.
2. Implement canonical models and deterministic normalization against a small
   checked-in fixture.
3. Implement source adapters and cache/provenance handling; verify credentials,
   provider configuration, and expected service behavior.
4. Implement quality filtering, reports, stable IDs, and full/standard variant
   selection.
5. Implement CSV/TSV exporter and compare a fixture output with the current
   column semantics.
6. Implement APKG exporter and migrate/refactor templates to optional,
   language-neutral translations and offline-safe audio.
7. Add CLI commands and end-to-end offline rebuild.
8. Update README with setup, credentials, source licenses, translation options,
   build commands, import instructions, and release policy; add `SOURCES.md` and
   `CHANGELOG.md`. Correct the current `LICENSE`/README language that broadly
   treats legacy AI-generated translations as CC0 unless their provenance and
   terms are verified; otherwise exclude those translations from distributable
   outputs.
9. Add the workflow in non-publishing validation mode, then perform one manual
   release to validate permissions and assets.
10. Enable the schedule only after a successful manual release and review the
    first scheduled report for source drift.
11. Once the new output is accepted, archive or remove the legacy generated
    snapshot according to the retention decision; do not delete it before a
    release can be reproduced from the new pipeline.

## 13. Acceptance criteria

The work is complete when:

- a new contributor can install pinned dependencies and run an offline fixture
  build;
- a configured contributor can run one CLI command to fetch current data and
  produce both variants;
- no default output contains hardcoded Chinese or any other translation
  language;
- translation is optional, provider-driven, language-labeled, and absent without
  explicit configuration;
- accepted cards pass deterministic quality gates and every card/media item has
  provenance;
- CSV/TSV imports correctly and APKG opens in Anki with templates, media, and
  deck hierarchy intact;
- the templates work without undocumented remote TTS and handle missing optional
  fields;
- CI validates pull requests without network secrets, while scheduled/manual
  jobs can refresh sources and publish releases;
- a meaningful update creates a minor-version GitHub Release with full/standard
  assets, checksums, manifest, and quality report;
- unchanged input does not create release noise;
- README, source/licensing notices, mandatory `NOTICE`/attribution files shipped
  alongside every CSV/TSV and APKG, and changelog describe exactly how to
  reproduce and audit a release. Embed attribution in the APKG where technically
  possible and keep the sidecar notice mandatory regardless.

## 14. Risks and explicit non-goals

- Do not assume provider uptime or silently hide MWLD/API failures; require
  configured credentials, bounded retries, and actionable reports while keeping
  the preferred-provider path simple.
- Do not use Google Cloud Translation or another paid translation API as a
  hidden default. User-supplied/local translations are the primary extension
  point.
- Do not infer that an upstream HTML page or remote audio URL is stable or
  suitable for long-term Anki review; package the preferred audio locally
  whenever possible and retain the URL as fallback/provenance.
- Do not preserve random UUID generation if it causes every rebuild to look like
  a full delete/re-add in Anki.
- Do not make the standard variant delete information from the full variant; it
  is a selection policy, not a destructive transformation.
- Do not commit caches, credentials, or large release artifacts unless a later
  repository policy explicitly requires it.
