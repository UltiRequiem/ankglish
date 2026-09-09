"""Deterministic offline build for validated TSV inputs."""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

from .config import load_config
from .exporters.apkg import export_apkg
from .exporters.notices import build_attribution, deck_description
from .pipeline.normalize import normalize_entries
from .pipeline.quality import quality_filter
from .sources.fetch import fetch_audio_many, fetch_mwld
from .sources.frequency import english_words
from .sources.mwld import MWLDClient
from .validation import validate_tsv


def build_tsv(
    *, input_path: Path, output_dir: Path, config_path: Path, variants: tuple[str, ...]
) -> list[Path]:
    errors = validate_tsv(input_path)
    if errors:
        raise ValueError("; ".join(errors))

    config = load_config(config_path)
    lines = input_path.read_text(encoding="utf-8").splitlines()
    directives = sorted(line for line in lines if line.startswith("#"))
    rows = sorted(line for line in lines if line and not line.startswith("#"))
    content = "\n".join((*directives, *rows)) + "\n"
    output_dir.mkdir(parents=True, exist_ok=True)

    outputs: list[Path] = []
    for variant in variants:
        output_path = output_dir / f"ankglish-{variant}.tsv"
        output_path.write_text(content, encoding="utf-8", newline="\n")
        outputs.append(output_path)

    manifest = {
        "project": config.project_name,
        "schema": config.schema,
        "variants": list(variants),
        "input": str(input_path),
        "record_count": len(rows),
        "outputs": {
            path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in outputs
        },
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return outputs


def rebuild_live(
    *,
    output_dir: Path,
    config_path: Path,
    cache_dir: Path,
    max_rank: int | None = None,
    refresh: bool = False,
    offline: bool = False,
    max_concurrency: int | None = None,
    media: str = "embed",
    refresh_audio: bool = False,
    audio_concurrency: int | None = None,
) -> dict[str, object]:
    if media not in {"embed", "link", "both"}:
        raise ValueError("media must be one of: embed, link, both")
    config = load_config(config_path)
    rank_limit = max_rank or config.frequency_max_rank
    frequency = english_words(rank_limit)
    words = [item.word for item in frequency]
    client = MWLDClient(config.learner_api_key)

    started_at = time.monotonic()

    def report(index: int, total: int, word: str, source: str) -> None:
        if (
            index == 1
            or index % 100 == 0
            or index == total
            or source.startswith("failed")
        ):
            elapsed = time.monotonic() - started_at
            rate = index / elapsed if elapsed else 0
            remaining = (total - index) / rate if rate else 0
            print(
                f"Progress: {index}/{total} ({index / total:.1%}) "
                f"word={word!r} source={source} "
                f"rate={rate:.1f}/s eta={remaining / 60:.1f}m",
                flush=True,
            )

    if offline:
        entries, failures = fetch_mwld(
            words,
            client=client,
            cache_dir=cache_dir,
            refresh=False,
            allow_network=False,
            delay_seconds=0,
            max_concurrency=max_concurrency or config.dictionary_max_concurrency,
            progress=report,
        )
    else:
        entries, failures = fetch_mwld(
            words,
            client=client,
            cache_dir=cache_dir,
            refresh=refresh,
            max_concurrency=max_concurrency or config.dictionary_max_concurrency,
            progress=report,
        )
    ranks = {item.word: item.rank for item in frequency}
    if offline and failures:
        raise ValueError(f"offline cache is missing {len(failures)} required words")

    stage_started = time.monotonic()
    full_notes, normalization_rejections = normalize_entries(
        entries, frequency_ranks=ranks
    )
    full_notes, quality_rejections = quality_filter(full_notes)
    print(
        f"Normalized {len(full_notes)} notes in {time.monotonic() - stage_started:.1f}s",
        flush=True,
    )

    media_dir = cache_dir / "audio"
    media_files: list[Path] = []
    if media in {"embed", "both"}:
        audio_started = time.monotonic()

        def audio_report(done: int, total: int, _url: str) -> None:
            if done == 1 or done % 100 == 0 or done == total:
                elapsed = time.monotonic() - audio_started
                rate = done / elapsed if elapsed else 0
                remaining = (total - done) / rate if rate else 0
                print(
                    f"Audio: {done}/{total} ({done / total:.1%}) "
                    f"rate={rate:.1f}/s eta={remaining / 60:.1f}m",
                    flush=True,
                )

        audio_paths = fetch_audio_many(
            [note.fields.get("AudioURL", "") for note in full_notes],
            cache_dir=media_dir,
            refresh=refresh_audio,
            max_concurrency=(
                audio_concurrency
                or max_concurrency
                or config.dictionary_max_concurrency
            ),
            progress=audio_report,
        )
        for note in full_notes:
            audio_path = audio_paths.get(note.fields.get("AudioURL", ""))
            if audio_path is not None:
                note.fields["Audio"] = f"[sound:{audio_path.name}]"
                note.fields["AudioPath"] = str(audio_path)
                media_files.append(audio_path)
        print(
            f"Audio: {len(media_files)} files in "
            f"{time.monotonic() - audio_started:.1f}s",
            flush=True,
        )

    standard_notes: list = []
    seen_words: set[str] = set()
    for note in full_notes:
        if note.headword.casefold() not in seen_words:
            standard_notes.append(note)
            seen_words.add(note.headword.casefold())

    output_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "project": config.project_name,
        "source": {"frequency": "wordfreq", "dictionary": "mwld"},
        "max_rank": rank_limit,
        "candidate_count": len(words),
        "fetched_count": len(entries),
        "wiktionary_count": 0,
        "failed_words": len(failures),
        "full_count": len(full_notes),
        "standard_count": len(standard_notes),
        "rejections": {**normalization_rejections, **quality_rejections},
        "audio_count": len(media_files),
        "audio_url_count": sum(
            1 for note in full_notes if note.fields.get("AudioURL", "")
        ),
        "media": media,
        "offline": offline,
    }
    description = deck_description(manifest)

    if media in {"embed", "both"}:
        _export_pair(full_notes, standard_notes, output_dir, description, suffix="")
    if media in {"link", "both"}:
        for note in full_notes:
            audio_url = note.fields.get("AudioURL", "")
            note.fields["Audio"] = (
                f'<audio controls preload="none" src="{audio_url}"></audio>'
                if audio_url
                else ""
            )
            note.fields.pop("AudioPath", None)
        _export_pair(
            full_notes, standard_notes, output_dir, description, suffix="-online"
        )

    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (output_dir / "ATTRIBUTION.md").write_text(
        build_attribution(manifest), encoding="utf-8"
    )
    print(
        f"Completed source fetch: candidates={len(words)} fetched={len(entries)} "
        f"failed={len(failures)}",
        flush=True,
    )
    return manifest


def _export_pair(
    full_notes: list,
    standard_notes: list,
    output_dir: Path,
    description: str,
    *,
    suffix: str,
) -> None:
    for variant, notes in (("full", full_notes), ("standard", standard_notes)):
        started = time.monotonic()
        output_path = output_dir / f"ankglish-{variant}{suffix}.apkg"
        export_apkg(notes, output_path, variant=variant, description=description)
        print(
            f"Wrote {output_path.name} ({len(notes)} notes) in "
            f"{time.monotonic() - started:.1f}s",
            flush=True,
        )
