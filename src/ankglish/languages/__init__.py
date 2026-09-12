"""Language resolution: maps a language code to its `LanguageProfile`.

Only English is implemented. This module is the single place that knows the
full set of supported languages, so the rest of the pipeline never has to.
"""

from __future__ import annotations

from .base import DictionaryClient, LanguageCode, LanguageProfile
from .english import ENGLISH

_LANGUAGES: dict[LanguageCode, LanguageProfile] = {ENGLISH.code: ENGLISH}


def resolve_language(code: LanguageCode) -> LanguageProfile:
    try:
        return _LANGUAGES[code]
    except KeyError:
        supported = ", ".join(sorted(_LANGUAGES))
        raise ValueError(
            f"unsupported language {code!r} (supported: {supported})"
        ) from None


__all__ = [
    "DictionaryClient",
    "ENGLISH",
    "LanguageCode",
    "LanguageProfile",
    "resolve_language",
]
