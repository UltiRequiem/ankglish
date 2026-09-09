"""Command-line entry point for the deck build pipeline."""

from __future__ import annotations

import argparse
from pathlib import Path

from . import __version__
from .build import build_tsv
from .validation import validate_tsv


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ankglish",
        description="Build reproducible English pronunciation Anki decks.",
    )
    parser.add_argument("--version", action="version", version=__version__)
    subparsers = parser.add_subparsers(dest="command")

    validate = subparsers.add_parser(
        "validate", help="Check that an input file exists and has TSV data."
    )
    validate.add_argument(
        "--input",
        type=Path,
        default=Path("tests/fixtures/notes.tsv"),
        help="Input note file to inspect (default: tests/fixtures/notes.tsv).",
    )

    build = subparsers.add_parser("build", help="Build deterministic offline TSV output.")
    build.add_argument("--input", type=Path, default=Path("tests/fixtures/notes.tsv"))
    build.add_argument("--config", type=Path, default=Path("config/default.toml"))
    build.add_argument("--output-dir", type=Path, default=Path("dist"))
    build.add_argument("--variant", choices=("full", "standard", "both"), default="both")

    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    if args.command == "validate":
        errors = validate_tsv(args.input)
        if errors:
            for error in errors:
                print(error)
            return 1
        print(f"Found input: {args.input}")
        return 0
    if args.command == "build":
        variants = ("full", "standard") if args.variant == "both" else (args.variant,)
        try:
            outputs = build_tsv(
                input_path=args.input,
                output_dir=args.output_dir,
                config_path=args.config,
                variants=variants,
            )
        except (OSError, ValueError, KeyError) as error:
            print(f"Build failed: {error}")
            return 1
        for output in outputs:
            print(f"Wrote {output}")
        print(f"Wrote {args.output_dir / 'manifest.json'}")
        return 0

    _build_parser().print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())