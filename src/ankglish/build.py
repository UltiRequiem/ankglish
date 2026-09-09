"""Deterministic offline build for validated TSV inputs."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .config import load_config
from .exporters.apkg import export_apkg
from .pipeline.normalize import normalize_entries
from .pipeline.quality import quality_filter
from .sources.fetch import fetch_audio, fetch_mwld
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
) -> dict[str, object]:
    config = load_config(config_path)
    rank_limit = max_rank or config.frequency_max_rank
    frequency = english_words(rank_limit)
    words = [item.word for item in frequency]
    client = MWLDClient(config.learner_api_key)
    if offline:
        entries, failures = fetch_mwld(
            words,
            client=client,
            cache_dir=cache_dir,
            refresh=False,
            allow_network=False,
            delay_seconds=0,
        )
    else:
        entries, failures = fetch_mwld(
            words, client=client, cache_dir=cache_dir, refresh=refresh
        )
    ranks = {item.word: item.rank for item in frequency}
    if offline and failures:
        raise ValueError(f"offline cache is missing {len(failures)} required words")
    full_notes, normalization_rejections = normalize_entries(entries, frequency_ranks=ranks)
    full_notes, quality_rejections = quality_filter(full_notes)
    media_dir = cache_dir / "audio"
    media_files: list[Path] = []
    for note in full_notes:
        audio_url = note.fields.get("AudioURL", "")
        try:
            audio_path = fetch_audio(audio_url, cache_dir=media_dir, refresh=refresh)
        except (OSError, ValueError, RuntimeError):
            audio_path = None
        if audio_path is not None:
            note.fields["Audio"] = f"[sound:{audio_path.name}]"
            note.fields["AudioPath"] = str(audio_path)
            media_files.append(audio_path)
    standard_notes: list = []
    seen_words: set[str] = set()
    for note in full_notes:
        if note.headword.casefold() not in seen_words:
            standard_notes.append(note)
            seen_words.add(note.headword.casefold())

    output_dir.mkdir(parents=True, exist_ok=True)
    export_apkg(full_notes, output_dir / "ankglish-full.apkg", variant="full")
    export_apkg(standard_notes, output_dir / "ankglish-standard.apkg", variant="standard")
    manifest = {
        "project": config.project_name,
        "source": {"frequency": "wordfreq", "dictionary": "mwld"},
        "max_rank": rank_limit,
        "candidate_count": len(words),
        "fetched_count": len(entries),
        "failed_words": len(failures),
        "full_count": len(full_notes),
        "standard_count": len(standard_notes),
        "rejections": {**normalization_rejections, **quality_rejections},
        "audio_count": len(media_files),
        "offline": offline,
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return manifest