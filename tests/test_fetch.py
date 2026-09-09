from pathlib import Path

from ankglish.sources.fetch import fetch_mwld


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