"""Generic language-configuration contract for the deck pipeline.

`build.py` orchestrates deck generation without knowing which language it is
building. A `LanguageProfile` is the seam: it bundles the frequency source,
dictionary client, and normalizer that a concrete language (currently only
English) supplies, so the pipeline can depend on this shape instead of
importing any one language's providers directly.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from ..config import BuildConfig
    from ..models import DeckNote
    from ..sources.frequency import FrequencyWord

LanguageCode = str


class DictionaryClient(Protocol):
    """Capability a dictionary provider must expose to the generic pipeline."""

    def fetch(self, headword: str) -> list[dict[str, object]]: ...


@dataclass(frozen=True)
class LanguageProfile:
    """One concrete language's providers and processing, wired for the pipeline."""

    code: LanguageCode
    name: str
    frequency: Callable[[int], list[FrequencyWord]]
    build_dictionary_client: Callable[[BuildConfig], DictionaryClient]
    normalize: Callable[..., tuple[list[DeckNote], dict[str, int]]]
