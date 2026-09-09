from pathlib import Path

from ankglish.cli import main


def test_validate_accepts_existing_input(tmp_path: Path) -> None:
    input_path = tmp_path / "notes.tsv"
    input_path.write_text("#separator:Tab\nfixture\tdeck\n", encoding="utf-8")

    assert main(["validate", "--input", str(input_path)]) == 0


def test_validate_rejects_missing_input(tmp_path: Path) -> None:
    assert main(["validate", "--input", str(tmp_path / "missing.tsv")]) == 1