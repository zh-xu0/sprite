# SPRITE (Sprite Pixel Region Isolation, Transform & Editing)

Small command-line tools for pixel-art images.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt
```

## Use

```bash
./sprite.py --help
./sprite.py center test_image.png                    # -> test_image_centered.png
./sprite.py center mathematical test_image.png
./sprite.py center visual test_image.png
./sprite.py crop test_image.png                      # -> test_image_cropped.png
./sprite.py crop test_image.png -o output.png
```

`center` keeps the original canvas size and moves the artwork to the middle:

- `mathematical` aligns the content bounding box with the canvas center.
- `visual` aligns the alpha-weighted center of mass with the canvas center,
  which looks better when the artwork is heavier on one side.

`crop` saves only the content bounding box, removing blank padding.

Both commands accept:

- `--tolerance N` - per-channel colour tolerance for matching a blank
  background that is not exactly uniform.
- `--alpha N` - treat pixels with alpha <= N as blank.

Default outputs (`*_centered.png`, `*_cropped.png`) are git-ignored.

## Adding a command

Create `sprite/commands/<name>.py` exposing `NAME`, `HELP`,
`add_arguments(parser)` and `run(args)`. It is discovered automatically and
appears in `./sprite.py --help`.
