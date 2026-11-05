"""Regenerates the synthetic sample images in this folder.

These are placeholder images (colors/shapes, no people) for exercising the
EthiViz image-upload pipeline without needing real photos. Run from the repo
root: `python3 sample_data/images/generate_samples.py`
"""
import random
from pathlib import Path

from PIL import Image, ImageDraw

OUT_DIR = Path(__file__).parent


def gradient(path: Path, c1: tuple[int, int, int], c2: tuple[int, int, int], size=(640, 480)) -> None:
    img = Image.new("RGB", size)
    px = img.load()
    w, h = size
    for x in range(w):
        t = x / (w - 1)
        r = int(c1[0] + (c2[0] - c1[0]) * t)
        g = int(c1[1] + (c2[1] - c1[1]) * t)
        b = int(c1[2] + (c2[2] - c1[2]) * t)
        for y in range(h):
            px[x, y] = (r, g, b)
    img.save(path)


def geometric(path: Path, size=(640, 480), seed=1) -> None:
    random.seed(seed)
    img = Image.new("RGB", size, (245, 245, 245))
    draw = ImageDraw.Draw(img)
    colors = [(230, 126, 34), (41, 128, 185), (39, 174, 96), (155, 89, 182), (241, 196, 15)]
    for _ in range(24):
        x0, y0 = random.randint(0, size[0]), random.randint(0, size[1])
        x1, y1 = x0 + random.randint(20, 120), y0 + random.randint(20, 120)
        color = random.choice(colors)
        if random.random() < 0.5:
            draw.ellipse([x0, y0, x1, y1], fill=color)
        else:
            draw.rectangle([x0, y0, x1, y1], fill=color)
    img.save(path)


def swatches(path: Path, size=(640, 480)) -> None:
    """Fitzpatrick-scale-style color bands. Purely synthetic — not faces or skin."""
    tones = [
        (244, 217, 192), (232, 190, 159), (198, 142, 101),
        (161, 102, 64), (115, 71, 44), (69, 42, 28),
    ]
    img = Image.new("RGB", size)
    draw = ImageDraw.Draw(img)
    band = size[0] // len(tones)
    for i, tone in enumerate(tones):
        draw.rectangle([i * band, 0, (i + 1) * band, size[1]], fill=tone)
    img.save(path)


if __name__ == "__main__":
    gradient(OUT_DIR / "gradient_sample.png", (52, 152, 219), (231, 76, 60))
    geometric(OUT_DIR / "geometric_pattern_sample.png")
    swatches(OUT_DIR / "color_swatch_sample.png")
    print(f"Wrote 3 sample images to {OUT_DIR}")
