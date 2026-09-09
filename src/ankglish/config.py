"""Configuration loading for reproducible builds."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os
import tomllib

from dotenv import load_dotenv


@dataclass(frozen=True)
class BuildConfig:
    project_name: str
    schema: str
    frequency_provider: str
    frequency_version: str
    dictionary_provider: str
    dictionary_fallback: str
    translations_enabled: bool
    package_headword_audio: bool
    example_tts_enabled: bool
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
    return BuildConfig(
        project_name=project["name"],
        schema=project["schema"],
        frequency_provider=frequency["provider"],
        frequency_version=frequency["version"],
        dictionary_provider=dictionary["provider"],
        dictionary_fallback=dictionary["fallback"],
        translations_enabled=translations["enabled"],
        package_headword_audio=audio["package_headword_audio"],
        example_tts_enabled=audio["example_tts_enabled"],
        learner_api_key=os.getenv(learner_env),
        elementary_api_key=os.getenv(elementary_env),
    )