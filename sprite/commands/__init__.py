"""Auto-discovered command modules.

A command module defines:

    NAME              the subcommand name
    HELP              one-line description
    add_arguments(p)  add its arguments to its argparse subparser
    run(args)         perform the command, returning an exit code

Drop a new module in this folder and it appears in the CLI automatically.
"""

from __future__ import annotations

from importlib import import_module
from pkgutil import iter_modules
from types import ModuleType
from typing import Iterator

REQUIRED_ATTRIBUTES = ("NAME", "HELP", "add_arguments", "run")


def iter_command_modules() -> Iterator[ModuleType]:
    for info in sorted(iter_modules(__path__), key=lambda item: item.name):
        if info.name.startswith("_"):
            continue
        module = import_module(f"{__name__}.{info.name}")
        if all(hasattr(module, attribute) for attribute in REQUIRED_ATTRIBUTES):
            yield module
