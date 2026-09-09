"""Deterministic offline build for validated TSV inputs."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .config import load_config
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