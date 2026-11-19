"""User-facing exceptions shared across the tool."""


class SpriteError(Exception):
    """An error that should be shown to the user without a traceback."""


class UsageError(SpriteError):
    """The command was called with invalid arguments."""


class ImageError(SpriteError):
    """The image could not be read or processed."""
