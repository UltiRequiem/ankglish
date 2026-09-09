"""Merriam-Webster Learner's Dictionary API access."""

from __future__ import annotations

import time
from dataclasses import dataclass

import httpx


class MWLDConfigurationError(RuntimeError):
    """Raised when the MWLD adapter cannot be configured safely."""


class MWLDRequestError(RuntimeError):
    """Raised when MWLD cannot provide an entry after bounded retries."""


@dataclass(frozen=True)
class MWLDClient:
    api_key: str | None
    timeout_seconds: float = 15.0
    retries: int = 3
    base_url: str = "https://www.dictionaryapi.com/api/v3/references/learners/json"

    def fetch(self, headword: str) -> list[dict[str, object]]:
        if not self.api_key:
            raise MWLDConfigurationError(
                "MWLD credentials are missing; set MWLD_LEARNER_API_KEY in the environment."
            )
        if not headword.strip():
            raise ValueError("headword must not be empty")

        url = f"{self.base_url}/{httpx.URL(headword.strip())}"
        last_error: Exception | None = None
        for attempt in range(self.retries):
            try:
                response = httpx.get(
                    url,
                    params={"key": self.api_key},
                    timeout=self.timeout_seconds,
                )
                response.raise_for_status()
                payload = response.json()
                if not isinstance(payload, list):
                    raise MWLDRequestError("MWLD returned an unexpected response shape")
                return [item for item in payload if isinstance(item, dict)]
            except (httpx.HTTPError, ValueError, MWLDRequestError) as error:
                last_error = error
                if attempt + 1 < self.retries:
                    time.sleep(2**attempt)
        raise MWLDRequestError(
            f"MWLD request failed for {headword!r} after {self.retries} attempts"
        ) from last_error
