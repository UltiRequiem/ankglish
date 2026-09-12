"""Configuration loading for reproducible builds."""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class BuildConfig:
    project_name: str
    schema: str
    target_language: str
    frequency_provider: str
    frequency_version: str
    dictionary_provider: str
    dictionary_fallback: str
    dictionary_max_concurrency: int
    translations_enabled: bool
    package_headword_audio: bool
    example_tts_enabled: bool
    frequency_max_rank: int
    learner_api_key: str | None
    elementary_api_key: str | None


def load_config(path: Path, *, dotenv_path: Path | None = None) -> BuildConfig:
    load_dotenv(
        dotenv_path=dotenv_path or path.parent.parent / ".env",
        override=False,
    )
    with path.open("rb") as config_file:
        data = tomllib.load(config_file)

    project = data["project"]
    frequency = data["sources"]["frequency"]
    dictionary = data["sources"]["dictionary"]
    translations = data["translations"]
    audio = data["audio"]
    credentials = data.get("credentials", {})
    learner_env = credentials.get("learner_env", "MWLD_LEARNER_API_KEY")
    elementary_env = credentials.get("elementary_env", "MWLD_ELEMENTARY_API_KEY")

    def secret(name: str) -> str | None:
        value = os.getenv(name)
        return value if value else None

    return BuildConfig(
        project_name=project["name"],
        schema=project["schema"],
        target_language=project.get("language", "en"),
        frequency_provider=frequency["provider"],
        frequency_version=frequency["version"],
        dictionary_provider=dictionary["provider"],
        dictionary_fallback=dictionary["fallback"],
        dictionary_max_concurrency=dictionary.get("max_concurrency", 8),
        translations_enabled=translations["enabled"],
        package_headword_audio=audio["package_headword_audio"],
        example_tts_enabled=audio["example_tts_enabled"],
        frequency_max_rank=frequency["max_rank"],
        learner_api_key=secret(learner_env),
        elementary_api_key=secret(elementary_env),
    )
