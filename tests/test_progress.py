from pathlib import Path

from ankglish.sources.fetch import fetch_mwld


def test_fetch_reports_progress_for_cached_words(tmp_path: Path) -> None:
    (tmp_path / "one.json").write_text("[]\n", encoding="utf-8")
    events: list[tuple[int, int, str, str]] = []

    fetch_mwld(
        ["one"],
        client=None,  # type: ignore[arg-type]
        cache_dir=tmp_path,
        allow_network=False,
        progress=lambda *event: events.append(event),
    )

    assert events == [(1, 1, "one", "cache")]