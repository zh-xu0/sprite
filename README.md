# SPRITE (Sprite Pixel Region Isolation, Transform & Editing)

Small command-line tools for pixel-art images.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt
```

## Use

Operations are flags, so they can be combined:

```bash
./sprite.py -C -O 3 image.png         # visually center + 3 px outline
./sprite.py -Cm -O 2 image.png        # mathematically center + outline
./sprite.py -c -O 1 image.png         # crop away padding, then outline
./sprite.py -c image.png              # crop only
./sprite.py -O 3 image.png            # outline only
./sprite.py -E 4 image.png            # enlarge 4x (nearest neighbour)
```

`image.png` above is a placeholder; pass the path to your own image.

| Flag | Meaning |
| --- | --- |
| `-C`, `-Cv` | center visually (default center mode) |
| `-Cm` | center mathematically |
| `-c` | crop away blank padding |
| `-O N`, `--outline N` | add an N-pixel outline (N >= 1) |
| `-E N`, `--enlarge N` | enlarge by a factor of N using nearest-neighbour sampling (N >= 1) |
| `--outline-color COLOR` | outline colour (default `#000000`) |
| `-o PATH` | output base path; the operation descriptor is appended (default: input stem) |
| `--tolerance N` | per-channel colour tolerance for background matching |
| `--alpha N` | treat pixels with alpha <= N as blank |

Operations run in the order crop, center, outline, enlarge. When `-c` is used
the canvas is reduced to the artwork, so centering has no effect.

### Output names

The output name is the input stem followed by the operations that ran, in
pipeline order:

```bash
./sprite.py -C image.png          # -> image_centered_visual.png
./sprite.py -Cm -O 2 image.png    # -> image_centered_mathematical_outline_2_000000.png
./sprite.py -c -O 1 image.png     # -> image_cropped_outline_1_000000.png
./sprite.py -O 3 image.png        # -> image_outline_3_000000.png
./sprite.py -E 4 image.png        # -> image_enlarged_4.png
```

A combined example:

```bash
./sprite.py -C -O 3 -E 4 image.png
# -> image_centered_visual_outline_3_000000_enlarged_4.png
```

The outline colour is included as a 6-digit hex code, or 8 digits when it has
alpha. `-o` sets the base name; the same descriptor is appended:

```bash
./sprite.py -C -O 3 image.png -o result.png
# -> result_centered_visual_outline_3_000000.png
```

### Center modes

`center` keeps the original canvas size and moves the artwork to the middle:

- `visual` (default) aligns the alpha-weighted center of mass with the canvas
  center.
- `mathematical` aligns the content bounding box with the canvas center.

Visual usually looks better when the artwork is heavier on one side.

### Outline

`-O N` adds an N-pixel outline that follows the artwork's silhouette and grows
the canvas by N pixels on every side. It is black by default.

`--outline-color` accepts `rgb(r,g,b)`, `rgba(r,g,b,a)`, `#rgb`, `#rgba`,
`#rrggbb`, or `#rrggbbaa`. Colour names are not supported.

```bash
./sprite.py -O 3 --outline-color 'rgb(255, 0, 0)' image.png        # rgb
./sprite.py -O 3 --outline-color 'rgba(255, 0, 0, 128)' image.png  # rgba
./sprite.py -O 3 --outline-color '#f00' image.png                  # #rgb
./sprite.py -O 3 --outline-color '#f008' image.png                 # #rgba
./sprite.py -O 3 --outline-color '#ff0000' image.png               # #rrggbb
./sprite.py -O 3 --outline-color '#ff000080' image.png             # #rrggbbaa
```

### Enlarge

`-E N` scales the final image by a factor of N using nearest-neighbour
sampling, so every source pixel becomes a clean N x N block.

Enlarging happens last. If you combine it with `-O`, the outline is scaled too:
`-O 3 -E 4` produces a 12-pixel-thick outline in the final image.

### Crop

`-c` saves only the content bounding box, removing blank padding.

## Formats

Inputs are converted to RGBA internally, so any format Pillow can read works.
Tested inputs include PNG, JPEG, BMP, GIF, WebP, and TIFF.

An input needs a detectable blank background (the corners are checked);
otherwise the tool reports `no blank padding detected`. JPEG compression noise
can make `--tolerance` useful.

Output defaults to PNG regardless of the input extension. Use `-o` to choose
another extension:

| Extension | Result |
| --- | --- |
| `.png` (default) | RGBA; recommended |
| `.webp` | RGBA |
| `.tiff` | RGBA |
| `.gif` | palette mode; limited transparency |
| `.bmp` | RGB; alpha is dropped |
| `.jpg`, `.jpeg` | not supported; RGBA cannot be written as JPEG |

If `-o` has no extension, `.png` is used. Animated GIF/WebP and multi-page
TIFF inputs use only the first frame/page, and EXIF orientation is not applied.

Generated `.png` outputs are git-ignored; outputs with other extensions are
not.

## Adding an operation

Implement the transform in `sprite/core.py`, expose it as a flag in
`sprite/cli.py`, and add its descriptor to the output name there.

## License

SPRITE is released under the MIT License. You may use, modify, and distribute
it, including commercially, provided the copyright and permission notice are
retained. See [LICENSE](LICENSE) for the full text.

Copyright (c) 2026 zh-xu0.

SPDX-License-Identifier: MIT
