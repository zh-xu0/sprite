"""The `center` command."""

from __future__ import annotations

import argparse
from pathlib import Path

from ..core import (
    CENTER_MODES,
    analyze,
    default_output,
    describe_background,
    render_centered,
    save,
)
from ..errors import UsageError

NAME = "center"
HELP = "Center the artwork inside its canvas, keeping the canvas size."


def add_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "mode",
        nargs="?",
        metavar="MODE",
        help="mathematical (default) or visual",
    )
    parser.add_argument("image", nargs="?", metavar="IMAGE", help="input image")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        metavar="PATH",
        help="output path (default: <name>_centered.png)",
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


def _mode_and_image(args: argparse.Namespace) -> tuple[str, Path]:
    """Resolve `center [MODE] IMAGE`, where MODE may be omitted."""
    first, second = args.mode, args.image
    if second is None:
        if first is None:
            raise UsageError("center: IMAGE is required")
        if first.lower() in CENTER_MODES:
            raise UsageError("center: IMAGE is required")
        # Only one positional: it was the image, not the mode.
        return "mathematical", Path(first)

    mode = first.lower()
    if mode not in CENTER_MODES:
        choices = ", ".join(CENTER_MODES)
        raise UsageError(f"center: unknown mode {first!r} (choose from {choices})")
    return mode, Path(second)


def run(args: argparse.Namespace) -> int:
    mode, image_path = _mode_and_image(args)
    analysis = analyze(image_path, tolerance=args.tolerance, alpha_min=args.alpha)
    result, (x, y) = render_centered(analysis, mode)

    destination = args.output or default_output(image_path, "centered")
    save(result, destination)

    left, top, right, bottom = analysis.margins
    print(
        f"{image_path.name}: {analysis.width}x{analysis.height}, "
        f"background {describe_background(analysis.background)}"
    )
    print(
        f"content: {analysis.content_width}x{analysis.content_height} "
        f"at ({analysis.bbox[0]}, {analysis.bbox[1]}), "
        f"margins left {left} top {top} right {right} bottom {bottom}"
    )
    if mode == "visual":
        centroid_x, centroid_y = analysis.centroid
        print(
            f"mode: visual (center of mass at "
            f"{centroid_x:.2f}, {centroid_y:.2f})"
        )
    else:
        print("mode: mathematical")
    print(
        f"placed at ({x}, {y}), new margins left {x} top {y} "
        f"right {analysis.width - x - analysis.content_width} "
        f"bottom {analysis.height - y - analysis.content_height}"
    )
    print(f"saved {destination}")
    return 0
