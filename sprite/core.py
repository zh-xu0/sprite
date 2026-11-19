"""Core image analysis and rendering shared by the CLI."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from PIL import Image, ImageChops, ImageFilter

from .errors import ImageError

RGBA = tuple[int, int, int, int]
Box = tuple[int, int, int, int]  # left, top, right, bottom; right/bottom exclusive


@dataclass
class Analysis:
    """An image plus what we learned about its artwork."""

    path: Path
    image: Image.Image
    background: RGBA
    bbox: Box
    centroid: tuple[float, float]
    pixel_count: int

    @property
    def width(self) -> int:
        return self.image.width

    @property
    def height(self) -> int:
        return self.image.height

    @property
    def content_width(self) -> int:
        return self.bbox[2] - self.bbox[0]

    @property
    def content_height(self) -> int:
        return self.bbox[3] - self.bbox[1]

    @property
    def margins(self) -> tuple[int, int, int, int]:
        """Current margins around the artwork: left, top, right, bottom."""
        left, top, right, bottom = self.bbox
        return left, top, self.width - right, self.height - bottom

    @property
    def transparent_background(self) -> bool:
        return self.background[3] == 0


def describe_background(background: RGBA) -> str:
    if background[3] == 0:
        return "transparent"
    return "#" + "".join(f"{channel:02x}" for channel in background[:3])


def _color_close(color: Sequence[int], target: Sequence[int], tolerance: int) -> bool:
    return all(abs(a - b) <= tolerance for a, b in zip(color[:3], target[:3]))


def find_background(
    image: Image.Image, tolerance: int = 0, alpha_min: int = 0
) -> RGBA | None:
    """Guess what blank space looks like from the image corners.

    Returns the fill colour for blank space ((0, 0, 0, 0) for transparency),
    or None when the corners do not agree, meaning there is no detectable
    padding.
    """
    width, height = image.size
    pixels = image.load()
    corners = [
        pixels[0, 0],
        pixels[width - 1, 0],
        pixels[0, height - 1],
        pixels[width - 1, height - 1],
    ]

    # Mostly transparent corners -> transparent background.
    if sum(corner[3] <= alpha_min for corner in corners) >= 3:
        return (0, 0, 0, 0)

    # At least three corners share an opaque colour -> that is the background.
    for corner in corners:
        if corner[3] <= alpha_min:
            continue
        matching = sum(
            other[3] > alpha_min and _color_close(corner, other, tolerance)
            for other in corners
        )
        if matching >= 3:
            return corner[:3] + (255,)

    if any(corner[3] <= alpha_min for corner in corners):
        return (0, 0, 0, 0)
    return None


def analyze(path: Path, tolerance: int = 0, alpha_min: int = 0) -> Analysis:
    """Load an image and locate its artwork.

    Raises ImageError if the file cannot be read, has no detectable padding,
    or is completely blank.
    """
    path = Path(path)
    if not path.is_file():
        raise ImageError(f"no such file: {path}")
    try:
        with Image.open(path) as opened:
            image = opened.convert("RGBA")
    except (OSError, ValueError) as exc:
        raise ImageError(f"could not read {path}: {exc}") from exc

    background = find_background(image, tolerance, alpha_min)
    if background is None:
        raise ImageError(f"{path.name}: no blank padding detected")

    stats = _scan_content(image, background, tolerance, alpha_min)
    if stats is None:
        raise ImageError(f"{path.name}: the image is entirely blank")

    bbox, centroid, pixel_count = stats
    return Analysis(path, image, background, bbox, centroid, pixel_count)


def _scan_content(
    image: Image.Image, background: RGBA, tolerance: int, alpha_min: int
) -> tuple[Box, tuple[float, float], int] | None:
    """Find the content box and alpha-weighted centre of mass in one pass."""
    width, height = image.size
    data = image.tobytes()
    stride = width * 4
    transparent_bg = background[3] == 0

    left, top = width, height
    right, bottom = -1, -1
    weight_total = 0.0
    x_total = 0.0
    y_total = 0.0
    count = 0

    for y in range(height):
        row = data[y * stride : (y + 1) * stride]
        for x in range(width):
            offset = x * 4
            alpha = row[offset + 3]
            if alpha <= alpha_min:
                continue
            if not transparent_bg and _color_close(
                row[offset : offset + 3], background, tolerance
            ):
                continue

            if x < left:
                left = x
            if x > right:
                right = x
            if y < top:
                top = y
            if y > bottom:
                bottom = y

            weight = alpha
            weight_total += weight
            x_total += x * weight
            y_total += y * weight
            count += 1

    if right < 0:
        return None
    return (
        (left, top, right + 1, bottom + 1),
        (x_total / weight_total, y_total / weight_total),
        count,
    )


CenterMode = Callable[[Analysis], tuple[int, int]]


def _mathematical_offset(analysis: Analysis) -> tuple[int, int]:
    """Align the content bounding box with the canvas center."""
    return (
        (analysis.width - analysis.content_width) // 2,
        (analysis.height - analysis.content_height) // 2,
    )


def _visual_offset(analysis: Analysis) -> tuple[int, int]:
    """Align the alpha-weighted centre of mass with the canvas center."""
    centroid_x, centroid_y = analysis.centroid
    x = round(analysis.bbox[0] + (analysis.width - 1) / 2 - centroid_x)
    y = round(analysis.bbox[1] + (analysis.height - 1) / 2 - centroid_y)
    # Never push the artwork off the canvas.
    x = min(max(x, 0), analysis.width - analysis.content_width)
    y = min(max(y, 0), analysis.height - analysis.content_height)
    return x, y


CENTER_MODES: dict[str, tuple[str, CenterMode]] = {
    "mathematical": (
        "align the content bounding box with the canvas center",
        _mathematical_offset,
    ),
    "visual": (
        "align the alpha-weighted center of mass with the canvas center",
        _visual_offset,
    ),
}


def center_offset(analysis: Analysis, mode: str = "mathematical") -> tuple[int, int]:
    """Return where the artwork's top-left corner should be placed."""
    try:
        _, offset = CENTER_MODES[mode]
    except KeyError:
        raise ValueError(f"unknown center mode {mode!r}") from None
    return offset(analysis)


def render_centered(
    analysis: Analysis, mode: str = "mathematical"
) -> tuple[Image.Image, tuple[int, int]]:
    """Return the recentered image and the artwork's new top-left position."""
    x, y = center_offset(analysis, mode)
    canvas = Image.new("RGBA", (analysis.width, analysis.height), analysis.background)
    canvas.paste(analysis.image.crop(analysis.bbox), (x, y))
    return canvas, (x, y)


def render_crop(analysis: Analysis) -> Image.Image:
    """Return just the artwork, with the blank padding removed."""
    return analysis.image.crop(analysis.bbox)


def render_enlarged(image: Image.Image, factor: int) -> Image.Image:
    """Return the image scaled by factor using nearest-neighbour sampling."""
    if factor < 1:
        raise ValueError("enlargement factor must be at least 1")
    return image.resize(
        (image.width * factor, image.height * factor),
        Image.Resampling.NEAREST,
    )


def content_mask(
    image: Image.Image, background: RGBA, tolerance: int = 0, alpha_min: int = 0
) -> Image.Image:
    """Return an 8-bit mask: 255 where the artwork is, 0 where it is blank."""
    alpha_mask = image.getchannel("A").point(
        [0 if value <= alpha_min else 255 for value in range(256)]
    )
    if background[3] == 0:
        return alpha_mask

    difference = ImageChops.difference(
        image.convert("RGB"), Image.new("RGB", image.size, background[:3])
    )
    red, green, blue = difference.split()
    largest = ImageChops.lighter(ImageChops.lighter(red, green), blue)
    color_mask = largest.point(
        [0 if value <= tolerance else 255 for value in range(256)]
    )
    return ImageChops.darker(alpha_mask, color_mask)


def add_outline(
    image: Image.Image,
    background: RGBA,
    width: int,
    color: RGBA,
    tolerance: int = 0,
    alpha_min: int = 0,
) -> Image.Image:
    """Return the image with a width-pixel silhouette outline around it.

    The canvas grows by width pixels on every side, and the outline follows
    the artwork's shape using 8-connected (Chebyshev) distance.
    """
    if width < 1:
        raise ValueError("outline width must be at least 1")

    mask = content_mask(image, background, tolerance, alpha_min)
    canvas_size = (image.width + 2 * width, image.height + 2 * width)

    padded = Image.new("L", canvas_size, 0)
    padded.paste(mask, (width, width))
    # Dilate one pixel at a time: a single (2N+1)-wide kernel is much slower
    # for large outlines than N passes of a 3x3 filter.
    dilated = padded
    for _ in range(width):
        dilated = dilated.filter(ImageFilter.MaxFilter(3))
    outline_mask = ImageChops.subtract(dilated, padded)

    canvas = Image.new("RGBA", canvas_size, background)
    canvas.paste(image, (width, width))
    outline_layer = Image.new("RGBA", canvas_size, (0, 0, 0, 0))
    outline_layer.paste(Image.new("RGBA", canvas_size, color), mask=outline_mask)
    return Image.alpha_composite(canvas, outline_layer)


def save(image: Image.Image, path: Path) -> None:
    try:
        image.save(path)
    except (OSError, ValueError) as exc:
        raise ImageError(f"could not save {path}: {exc}") from exc
