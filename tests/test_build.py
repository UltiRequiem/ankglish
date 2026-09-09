import json
from pathlib import Path

from ankglish.build import build_tsv


def test_build_is_deterministic_and_writes_manifest(tmp_path: Path) -> None:
    first_dir = tmp_path / "first"
    second_dir = tmp_path / "second"
    kwargs = {
        "input_path": Path("tests/fixtures/notes.tsv"),
        "config_path": Path("config/default.toml"),
        "variants": ("full", "standard"),
    }

    build_tsv(output_dir=first_dir, **kwargs)
    build_tsv(output_dir=second_dir, **kwargs)

    assert (first_dir / "ankglish-full.tsv").read_bytes() == (
        second_dir / "ankglish-full.tsv"
    ).read_bytes()
    manifest = json.loads((first_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["record_count"] == 1
    assert manifest["variants"] == ["full", "standard"]