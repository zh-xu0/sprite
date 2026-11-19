#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (C) 2026 Zachary Xu
"""SPRITE - Sprite Pixel Region Isolation, Transform & Editing.

Small tools for pixel-art images.

Examples:

    ./sprite.py -C -O 3 image.png
    ./sprite.py -Cm -O 2 image.png
    ./sprite.py -c -O 1 image.png
    ./sprite.py -O 3 image.png
    ./sprite.py -E 4 image.png
"""

from __future__ import annotations

import sys


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv

    try:
        import PIL  # noqa: F401
    except ModuleNotFoundError:
        print(
            "Pillow is required. Install it with:\n"
            f"  {sys.executable} -m pip install pillow",
            file=sys.stderr,
        )
        return 1

    from sprite.cli import main as cli_main

    return cli_main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
