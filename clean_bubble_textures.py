#!/usr/bin/env python3
"""
Clean checkerboard pattern from bubble PNGs in assets/images/underwater_assets.
This script will make all pixels that match the checkerboard pattern fully transparent.

Usage: pdm run python clean_bubble_textures.py
"""
import os

from PIL import Image

BUBBLE_FILES = [
    "assets/images/underwater_assets/bubble_small.png",
    "assets/images/underwater_assets/bubble_large.png",
]

# Checkerboard colors (common: light gray and dark gray)
CHECKER_COLORS = [
    (192, 192, 192),  # light gray
    (128, 128, 128),  # dark gray
    (200, 200, 200),  # some PNGs use slightly different grays
    (120, 120, 120),
]

TOLERANCE = 12  # Accept color matches within this tolerance


def is_checker_color(rgb):
    for ref in CHECKER_COLORS:
        if all(abs(c - r) <= TOLERANCE for c, r in zip(rgb, ref)):
            return True
    return False


def clean_bubble(path):
    img = Image.open(path).convert("RGBA")
    pixels = img.load()
    w, h = img.size
    changed = 0
    for y in range(h):
        for x in range(w):
            r, g, b, a = pixels[x, y]
            if a > 0 and is_checker_color((r, g, b)):
                pixels[x, y] = (0, 0, 0, 0)
                changed += 1
    if changed:
        img.save(path)
        print(f"Cleaned {changed} checker pixels in {path}")
    else:
        print(f"No checker pixels found in {path}")


if __name__ == "__main__":
    for path in BUBBLE_FILES:
        if os.path.exists(path):
            clean_bubble(path)
        else:
            print(f"File not found: {path}")
            print(f"File not found: {path}")
            print(f"File not found: {path}")
