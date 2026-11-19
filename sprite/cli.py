"""Argparse front end: one subcommand per module in sprite.commands."""

from __future__ import annotations

import argparse
import sys

from .commands import iter_command_modules
from .errors import SpriteError, UsageError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "SPRITE (Sprite Pixel Region Isolation, Transform & Editing) - "
            "small tools for pixel-art images."
        ),
    )
    subparsers = parser.add_subparsers(dest="command", metavar="COMMAND")
    for module in iter_command_modules():
        command = subparsers.add_parser(
            module.NAME,
            help=module.HELP,
            description=module.HELP,
        )
        module.add_arguments(command)
        command.set_defaults(_run=module.run)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    run = getattr(args, "_run", None)
    if run is None:
        parser.print_help()
        return 0

    try:
        return run(args) or 0
    except UsageError as exc:
        print(f"{parser.prog}: error: {exc}", file=sys.stderr)
        return 2
    except SpriteError as exc:
        print(f"{parser.prog}: error: {exc}", file=sys.stderr)
        return 1
