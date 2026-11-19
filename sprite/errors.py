# SPDX-License-Identifier: MIT
# Copyright (C) 2026 Zachary Xu
"""User-facing exceptions shared across the tool."""


class SpriteError(Exception):
    """An error that should be shown to the user without a traceback."""


class ImageError(SpriteError):
    """The image could not be read or processed."""
