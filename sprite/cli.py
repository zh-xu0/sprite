# SPDX-License-Identifier: MIT
# Copyright (C) 2026 Zachary Xu
"""Command-line front end for SPRITE."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .core import (
    RGBA,
    add_outline,
    analyze,
    describe_background,
    render_centered,
    render_crop,
    render_enlarged,
    save,
)
from .errors import SpriteError
from .options import parse_color, positive_int


def _program_name() -> str:
    return Path(sys.argv[0]).name or "sprite.py"


def _color_code(color: RGBA) -> str:
    red, green, blue, alpha = color
    code = f"{red:02x}{green:02x}{blue:02x}"
    return code if alpha == 255 else f"{code}{alpha:02x}"


def _described_output(
    image_path: Path, custom: Path | None, description: str
) -> Path:
    if custom is None:
        return image_path.with_name(f"{image_path.stem}_{description}.png")
    suffix = custom.suffix or ".png"
    return custom.with_name(f"{custom.stem}_{description}{suffix}")


def _flag_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "SPRITE (Sprite Pixel Region Isolation, Transform & Editing) - "
            "small tools for pixel-art images."
        ),
        epilog=(
            "Operations run in the order crop, center, outline, enlarge. "
            "Example: ./sprite.py -C -O 3 -E 4 IMAGE"
        ),
        allow_abbrev=False,
    )

    center = parser.add_mutually_exclusive_group()
    center.add_argument(
        "-C",
        dest="center_mode",
        action="store_const",
        const="visual",
        help="center visually (default center mode)",
    )
    center.add_argument(
        "-Cv",
        dest="center_mode",
        action="store_const",
        const="visual",
        help="center visually (same as -C)",
    )
    center.add_argument(
        "-Cm",
        dest="center_mode",
        action="store_const",
        const="mathematical",
        help="center mathematically",
    )

    parser.add_argument(
        "-c", "--crop", action="store_true", help="crop away blank padding"
    )
    parser.add_argument(
        "-O",
        "--outline",
        dest="outline",
        type=positive_int,
        metavar="N",
        help="add an N-pixel outline around the artwork (N >= 1)",
    )
    parser.add_argument(
        "-E",
        "--enlarge",
        dest="enlarge",
        type=positive_int,
        metavar="N",
        help="enlarge by a factor of N using nearest-neighbour sampling (N >= 1)",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        metavar="PATH",
        help="output base path; the operation descriptor is appended (default: input stem)",
    )
    parser.add_argument(
        "--tolerance",
        type=int,
        default=0,
        metavar="N",
        help="per-channel colour tolerance when matching a blank background (default: 0)",
    )
    parser.add_argument(
        "--alpha",
        type=int,
        default=0,
        metavar="N",
        help="treat pixels with alpha <= N as blank (default: 0)",
    )
    parser.add_argument(
        "--outline-color",
        type=parse_color,
        default=(0, 0, 0, 255),
        metavar="COLOR",
        help=(
            "outline colour: rgb(r,g,b), rgba(r,g,b,a), #rgb, #rgba, "
            "#rrggbb, or #rrggbbaa (default: #000000)"
        ),
    )
    parser.add_argument(
        "image", nargs="?", type=Path, metavar="IMAGE", help="input image"
    )
    return parser


def _run_flags(argv: list[str]) -> int:
    parser = _flag_parser()
    args = parser.parse_args(argv)

    if args.image is None:
        if (
            args.center_mode is None
            and not args.crop
            and args.outline is None
            and args.enlarge is None
        ):
            parser.print_help()
            return 0
        parser.error("IMAGE is required")

    if (
        args.center_mode is None
        and not args.crop
        and args.outline is None
        and args.enlarge is None
    ):
        parser.error("no operation given (use -C, -Cm, -c, -O N, or -E N)")

    analysis = analyze(args.image, tolerance=args.tolerance, alpha_min=args.alpha)
    image = analysis.image
    applied: list[str] = []
    descriptors: list[str] = []

    if args.crop:
        image = render_crop(analysis)
        applied.append("crop")
        descriptors.append("cropped")
        if args.center_mode:
            print(
                f"{_program_name()}: note: centering has no effect with -c "
                "(cropping removes the canvas margins)",
                file=sys.stderr,
            )
    elif args.center_mode:
        image, _ = render_centered(analysis, args.center_mode)
        applied.append(f"center ({args.center_mode})")
        descriptors.append(f"centered_{args.center_mode}")

    if args.outline is not None:
        image = add_outline(
            image,
            analysis.background,
            args.outline,
            args.outline_color,
            args.tolerance,
            args.alpha,
        )
        applied.append(f"outline ({args.outline} px)")
        descriptors.append(
            f"outline_{args.outline}_{_color_code(args.outline_color)}"
        )

    if args.enlarge is not None:
        image = render_enlarged(image, args.enlarge)
        applied.append(f"enlarge ({args.enlarge}x)")
        descriptors.append(f"enlarged_{args.enlarge}")

    destination = _described_output(
        args.image, args.output, "_".join(descriptors)
    )
    save(image, destination)

    print(
        f"{args.image.name}: {analysis.width}x{analysis.height}, "
        f"background {describe_background(analysis.background)}"
    )
    print(f"operations: {', '.join(applied)}")
    print(f"saved {destination} ({image.width}x{image.height})")
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else list(argv)
    try:
        return _run_flags(argv)
    except SpriteError as exc:
        print(f"{_program_name()}: error: {exc}", file=sys.stderr)
        return 1
