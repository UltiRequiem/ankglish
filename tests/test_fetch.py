from pathlib import Path
import time

from ankglish.sources.fetch import fetch_mwld


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