"""Cached source retrieval with credential-free cache metadata."""

from __future__ import annotations

import json
from pathlib import Path
import re
import time

from .mwld import MWLDClient


def _safe_name(word: str) -> str:
    return re.sub(r"[^a-z0-9_-]", "_", word.casefold())


def fetch_mwld(
    words: list[str],
    *,
    client: MWLDClient,
    cache_dir: Path,
    refresh: bool = False,
    allow_network: bool = True,
    delay_seconds: float = 0.1,
) -> tuple[dict[str, list[dict[str, object]]], dict[str, str]]:
    cache_dir.mkdir(parents=True, exist_ok=True)
    entries: dict[str, list[dict[str, object]]] = {}
    failures: dict[str, str] = {}
    for word in words:
        path = cache_dir / f"{_safe_name(word)}.json"
        try:
            if path.is_file() and not refresh:
                payload = json.loads(path.read_text(encoding="utf-8"))
            elif not allow_network:
                failures[word] = "missing_cache"
                continue
            else:
                payload = client.fetch(word)
                path.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")
                if delay_seconds:
                    time.sleep(delay_seconds)
            entries[word] = payload
        except Exception as error:  # provider failures belong in the report
            failures[word] = type(error).__name__
    return entries, failures