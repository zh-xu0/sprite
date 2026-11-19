"""The `crop` command."""

from __future__ import annotations

import argparse
from pathlib import Path

from ..core import (
    analyze,
    default_output,
    describe_background,
    render_crop,
    save,
)

NAME = "crop"
HELP = "Crop away blank padding around the artwork."


def add_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("image", type=Path, metavar="IMAGE", help="input image")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        metavar="PATH",
        help="output path (default: <name>_cropped.png)",
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


def run(args: argparse.Namespace) -> int:
    analysis = analyze(args.image, tolerance=args.tolerance, alpha_min=args.alpha)
    result = render_crop(analysis)

    destination = args.output or default_output(args.image, "cropped")
    save(result, destination)

    left, top, right, bottom = analysis.margins
    print(
        f"{args.image.name}: {analysis.width}x{analysis.height}, "
        f"background {describe_background(analysis.background)}"
    )
    print(
        f"content: {analysis.content_width}x{analysis.content_height} "
        f"at ({analysis.bbox[0]}, {analysis.bbox[1]}), "
        f"margins left {left} top {top} right {right} bottom {bottom}"
    )
    print(f"saved {destination} ({analysis.content_width}x{analysis.content_height})")
    return 0
