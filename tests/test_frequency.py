from ankglish.sources.frequency import english_words


def test_frequency_source_is_deterministic_and_ranked() -> None:
    words = english_words(max_rank=5)

    assert len(words) == 5
    assert [word.rank for word in words] == [1, 2, 3, 4, 5]
    assert all(word.source == "wordfreq" for word in words)
    assert all(word.word.islower() for word in words)
