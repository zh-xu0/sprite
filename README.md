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
./sprite.py -C -O 3 test_image.png         # visually center + 3 px outline
./sprite.py -Cm -O 2 test_image.png        # mathematically center + outline
./sprite.py -c -O 1 test_image.png         # crop away padding, then outline
./sprite.py -c test_image.png              # crop only
./sprite.py -O 3 test_image.png            # outline only
```

| Flag | Meaning |
| --- | --- |
| `-C`, `-Cv` | center visually (default center mode) |
| `-Cm` | center mathematically |
| `-c` | crop away blank padding |
| `-O N`, `--outline N` | add an N-pixel outline (N >= 1) |
| `--outline-color COLOR` | outline colour (default `#000000`) |
| `-o PATH` | output base path; the operation descriptor is appended (default: input stem) |
| `--tolerance N` | per-channel colour tolerance for background matching |
| `--alpha N` | treat pixels with alpha <= N as blank |

Operations run in the order crop, center, outline. When `-c` is used the
canvas is reduced to the artwork, so centering has no effect.

### Output names

The output name is the input stem followed by the operations that ran, in
pipeline order:

```bash
./sprite.py -C test_image.png          # -> test_image_centered_visual.png
./sprite.py -Cm -O 2 test_image.png    # -> test_image_centered_mathematical_outline_2_000000.png
./sprite.py -c -O 1 test_image.png     # -> test_image_cropped_outline_1_000000.png
./sprite.py -O 3 test_image.png        # -> test_image_outline_3_000000.png
```

The outline colour is included as a 6-digit hex code, or 8 digits when it has
alpha. `-o` sets the base name; the same descriptor is appended:

```bash
./sprite.py -C -O 3 test_image.png -o result.png
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
./sprite.py -O 3 --outline-color 'rgb(255, 0, 0)' test_image.png        # rgb
./sprite.py -O 3 --outline-color 'rgba(255, 0, 0, 128)' test_image.png  # rgba
./sprite.py -O 3 --outline-color '#f00' test_image.png                  # #rgb
./sprite.py -O 3 --outline-color '#f008' test_image.png                 # #rgba
./sprite.py -O 3 --outline-color '#ff0000' test_image.png               # #rrggbb
./sprite.py -O 3 --outline-color '#ff000080' test_image.png             # #rrggbbaa
```

### Crop

`-c` saves only the content bounding box, removing blank padding.

Generated outputs are git-ignored.

## Adding an operation

Implement the transform in `sprite/core.py`, expose it as a flag in
`sprite/cli.py`, and add its descriptor to the output name there.
