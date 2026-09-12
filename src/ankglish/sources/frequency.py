"""Deterministic frequency ranking backed by the pinned wordfreq package."""

from __future__ import annotations

from dataclasses import dataclass

from wordfreq import iter_wordlist, zipf_frequency


@dataclass(frozen=True)
class FrequencyWord:
    word: str
    rank: int
    score: float
    source: str = "wordfreq"


def frequency_words(language_code: str, max_rank: int = 60000) -> list[FrequencyWord]:
    words: list[FrequencyWord] = []
    for word in iter_wordlist(language_code):
        if not word.isalpha() or word.lower() != word:
            continue
        words.append(
            FrequencyWord(
                word=word,
                rank=len(words) + 1,
                score=zipf_frequency(word, language_code),
            )
        )
        if len(words) >= max_rank:
            break
    return words


def english_words(max_rank: int = 60000) -> list[FrequencyWord]:
    """Backward-compatible English convenience wrapper around `frequency_words`."""

    return frequency_words("en", max_rank)
