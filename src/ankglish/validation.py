"""Validation for the small Anki TSV interchange used by fixtures and exports."""

from __future__ import annotations

from pathlib import Path


def validate_tsv(path: Path) -> list[str]:
    if not path.is_file():
        return [f"Input does not exist: {path}"]

    lines = path.read_text(encoding="utf-8").splitlines()
    directives = [line for line in lines if line.startswith("#")]
    data_lines = [line for line in lines if line and not line.startswith("#")]
    errors: list[str] = []
    if "#separator:Tab" not in directives:
        errors.append("Missing #separator:Tab directive")
    if not data_lines:
        errors.append("Input contains no note rows")
    elif any("\t" not in line for line in data_lines):
        errors.append("Every note row must contain a tab separator")
    return errors