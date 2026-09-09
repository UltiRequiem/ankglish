from pathlib import Path
from zipfile import ZipFile

from ankglish.exporters.apkg import export_apkg
from ankglish.models import DeckNote, Sense, stable_note_id


def test_apkg_export_contains_stable_note_and_media_tables(tmp_path: Path) -> None:
    sense = Sense(source_id="hello-1", definition="a greeting", part_of_speech="noun")
    note = DeckNote(
        note_id=stable_note_id(
            provider="fixture",
            entry_id="hello",
            sense_id=sense.source_id,
            headword="hello",
            part_of_speech=sense.part_of_speech,
        ),
        headword="hello",
        part_of_speech="noun",
        sense=sense,
        variant="full",
    )
    output = tmp_path / "ankglish.apkg"

    export_apkg([note], output, variant="full")

    with ZipFile(output) as package:
        assert {"collection.anki2", "media"}.issubset(package.namelist())
        assert package.read("media") == b"{}"