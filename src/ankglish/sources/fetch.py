"""Cached source retrieval with credential-free cache metadata."""

from __future__ import annotations

import json
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
    progress: Callable[[int, int, str, str], None] | None = None,
) -> tuple[dict[str, list[dict[str, object]]], dict[str, str]]:
    cache_dir.mkdir(parents=True, exist_ok=True)
    entries: dict[str, list[dict[str, object]]] = {}
    failures: dict[str, str] = {}
    total = len(words)
    for index, word in enumerate(words, start=1):
        path = cache_dir / f"{_safe_name(word)}.json"
        source = "cache"
        try:
            if path.is_file() and not refresh:
                payload = json.loads(path.read_text(encoding="utf-8"))
            elif not allow_network:
                failures[word] = "missing_cache"
                if progress:
                    progress(index, total, word, "missing_cache")
                continue
            else:
                source = "network"
                payload = client.fetch(word)
                path.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")
                if delay_seconds:
                    time.sleep(delay_seconds)
            entries[word] = payload
            if progress:
                progress(index, total, word, source)
        except Exception as error:  # provider failures belong in the report
            failures[word] = type(error).__name__
            if progress:
                progress(index, total, word, f"failed:{type(error).__name__}")
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