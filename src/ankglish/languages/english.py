"""English: the only language implementation wired up today.

Composes the existing English-specific providers (wordfreq ranking,
Merriam-Webster Learner's Dictionary, MWLD normalization) behind the generic
`LanguageProfile` contract.
"""

from __future__ import annotations

from ..config import BuildConfig
from ..pipeline.normalize import normalize_entries
from ..sources.frequency import frequency_words
from ..sources.mwld import MWLDClient
from .base import LanguageProfile

CODE = "en"


def _frequency(max_rank: int) -> list:
    return frequency_words(CODE, max_rank)


def _build_dictionary_client(config: BuildConfig) -> MWLDClient:
    return MWLDClient(config.learner_api_key)


ENGLISH = LanguageProfile(
    code=CODE,
    name="English",
    frequency=_frequency,
    build_dictionary_client=_build_dictionary_client,
    normalize=normalize_entries,
)
