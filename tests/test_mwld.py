import pytest

from ankglish.sources.mwld import MWLDClient, MWLDConfigurationError


def test_mwld_requires_environment_credential() -> None:
    with pytest.raises(MWLDConfigurationError, match="MWLD_LEARNER_API_KEY"):
        MWLDClient(api_key=None).fetch("hello")


def test_mwld_rejects_empty_headword() -> None:
    with pytest.raises(ValueError, match="headword"):
        MWLDClient(api_key="test-key").fetch(" ")
