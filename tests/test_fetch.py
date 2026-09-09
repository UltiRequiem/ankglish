from pathlib import Path
import time

from ankglish.sources.fetch import fetch_audio_many, fetch_mwld


class FakeClient:
    def fetch(self, word: str) -> list[dict[str, object]]:
        time.sleep(0.01)
        return [{"word": word}]


def test_offline_fetch_does_not_call_network_for_missing_cache(tmp_path: Path) -> None:
    entries, failures = fetch_mwld(
        ["missing"],
        client=None,  # type: ignore[arg-type]
        cache_dir=tmp_path,
        allow_network=False,
        delay_seconds=0,
    )

    assert entries == {}
    assert failures == {"missing": "missing_cache"}


def test_fetch_preserves_input_order_with_parallel_workers(tmp_path: Path) -> None:
    entries, failures = fetch_mwld(
        ["one", "two", "three"],
        client=FakeClient(),
        cache_dir=tmp_path,
        delay_seconds=0,
        max_concurrency=3,
    )

    assert list(entries) == ["one", "two", "three"]
    assert failures == {}

def test_fetch_audio_many_dedupes_and_reports_progress(tmp_path: Path) -> None:
    for name in ("a000001.wav", "b000001.wav"):
        (tmp_path / name).write_bytes(b"RIFF")
    base = "https://media.merriam-webster.com/soundc11"
    urls = [
        f"{base}/a/a000001.wav",
        f"{base}/a/a000001.wav",  # duplicate collapses
        f"{base}/b/b000001.wav",
        "",  # skipped
    ]
    events: list[tuple[int, int, str]] = []

    results = fetch_audio_many(
        urls,
        cache_dir=tmp_path,
        progress=lambda *event: events.append(event),
    )

    assert set(results) == {urls[0], urls[2]}
    assert results[urls[0]].name == "a000001.wav"
    assert len(events) == 2  # two distinct non-empty URLs
    assert events[-1][1] == 2  # total reflects deduped count
