from pathlib import Path

from ankglish.validation import validate_tsv


def test_validation_reports_missing_directive_and_rows(tmp_path: Path) -> None:
    input_path = tmp_path / "invalid.tsv"
    input_path.write_text("word only\n", encoding="utf-8")

    assert validate_tsv(input_path) == [
        "Missing #separator:Tab directive",
        "Every note row must contain a tab separator",
    ]
