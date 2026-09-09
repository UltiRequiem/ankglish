"""Cached source retrieval with credential-free cache metadata."""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import re
import time
from collections.abc import Callable

import httpx

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
    max_concurrency: int = 8,
    progress: Callable[[int, int, str, str], None] | None = None,
) -> tuple[dict[str, list[dict[str, object]]], dict[str, str]]:
    if max_concurrency < 1:
        raise ValueError("max_concurrency must be at least 1")
    cache_dir.mkdir(parents=True, exist_ok=True)
    total = len(words)

    def fetch_one(word: str) -> tuple[str, list[dict[str, object]] | None, str, str | None]:
        path = cache_dir / f"{_safe_name(word)}.json"
        source = "cache"
        try:
            if path.is_file() and not refresh:
                payload = json.loads(path.read_text(encoding="utf-8"))
            elif not allow_network:
                return word, None, "missing_cache", "missing_cache"
            else:
                source = "network"
                payload = client.fetch(word)
                path.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")
                if delay_seconds:
                    time.sleep(delay_seconds)
            return word, payload, source, None
        except Exception as error:  # provider failures belong in the report
            return word, None, f"failed:{type(error).__name__}", type(error).__name__

    entries_by_word: dict[str, list[dict[str, object]]] = {}
    failures: dict[str, str] = {}
    completed = 0
    with ThreadPoolExecutor(max_workers=max_concurrency) as executor:
        futures = [executor.submit(fetch_one, word) for word in words]
        for future in as_completed(futures):
            word, payload, source, failure = future.result()
            completed += 1
            if payload is not None:
                entries_by_word[word] = payload
            if failure is not None:
                failures[word] = failure
            if progress:
                progress(completed, total, word, source)

    entries = {word: entries_by_word[word] for word in words if word in entries_by_word}
    return entries, failures


def fetch_audio(url: str, *, cache_dir: Path, refresh: bool = False) -> Path | None:
    if not url:
        return None
    filename = url.rsplit("/", 1)[-1]
    path = cache_dir / filename
    if path.is_file() and not refresh:
        return path
    response = httpx.get(url, timeout=15.0)
    response.raise_for_status()
    if not response.headers.get("content-type", "").startswith("audio/"):
        return None
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(response.content)
    return path