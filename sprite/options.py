# SPDX-License-Identifier: MIT
# Copyright (C) 2026 Zachary Xu
"""Argument value parsers shared by the CLI front end."""

from __future__ import annotations

import argparse
import re

from .core import RGBA

_RGB_PATTERN = re.compile(
    r"rgb\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*\)",
    re.IGNORECASE,
)
_RGBA_PATTERN = re.compile(
    r"rgba\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*\)",
    re.IGNORECASE,
)


def positive_int(value: str) -> int:
    """argparse type for an integer of at least 1."""
    try:
        number = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"invalid integer: {value!r}") from None
    if number < 1:
        raise argparse.ArgumentTypeError("must be at least 1")
    return number


def _channel(value: int, label: str, original: str) -> int:
    if not 0 <= value <= 255:
        raise argparse.ArgumentTypeError(
            f"{label} must be between 0 and 255 in {original!r}"
        )
    return value


def parse_color(value: str) -> RGBA:
    """argparse type for a colour given in rgb()/rgba() or hex notation."""
    text = value.strip()
    if text.startswith("#"):
        digits = text[1:]
        if len(digits) in (3, 4):
            digits = "".join(character * 2 for character in digits)
        if len(digits) not in (6, 8):
            raise argparse.ArgumentTypeError(f"invalid colour: {value!r}")
        try:
            channels = bytes.fromhex(digits)
        except ValueError:
            raise argparse.ArgumentTypeError(f"invalid colour: {value!r}") from None
        if len(channels) == 3:
            return (channels[0], channels[1], channels[2], 255)
        return (channels[0], channels[1], channels[2], channels[3])

    match = _RGBA_PATTERN.fullmatch(text)
    if match is not None:
        red, green, blue, alpha = match.groups()
        return (
            _channel(int(red), "red", value),
            _channel(int(green), "green", value),
            _channel(int(blue), "blue", value),
            _channel(int(alpha), "alpha", value),
        )

    match = _RGB_PATTERN.fullmatch(text)
    if match is not None:
        red, green, blue = match.groups()
        return (
            _channel(int(red), "red", value),
            _channel(int(green), "green", value),
            _channel(int(blue), "blue", value),
            255,
        )

    raise argparse.ArgumentTypeError(
        f"invalid colour: {value!r} "
        "(use rgb(r,g,b), rgba(r,g,b,a), or #hex)"
    )
