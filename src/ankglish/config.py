"""Configuration loading for reproducible builds."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import tomllib


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


def load_config(path: Path) -> BuildConfig:
    with path.open("rb") as config_file:
        data = tomllib.load(config_file)

    project = data["project"]
    frequency = data["sources"]["frequency"]
    dictionary = data["sources"]["dictionary"]
    translations = data["translations"]
    audio = data["audio"]
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
    )