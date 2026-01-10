#!/usr/bin/env python3
"""
Extract individual sprites from underwater_sea_creatures.png sprite sheet.
Image size: 2816 x 1536 pixels

Run this script and update the SPRITES dict with the correct bounding boxes
for each creature you want to extract.

Usage: pdm run python extract_sea_creatures.py
"""

import os

from PIL import Image

# Source sprite sheet
SOURCE = "assets/images/underwater_sea_creatures.png"
OUTPUT_DIR = "assets/images/sea_creatures"

# Define sprites to extract: name -> (left, top, right, bottom)
# These are example coordinates - update based on actual sprite positions
SPRITES = {
    # Example entries - UPDATE THESE with actual coordinates:
    # "fish_blue": (0, 0, 400, 400),
    # "jellyfish": (400, 0, 800, 400),
    # "crab": (0, 400, 400, 800),
    # "seahorse": (400, 400, 800, 800),
}


def extract_sprites():
    """Extract all defined sprites from the sprite sheet."""
    if not SPRITES:
        print("No sprites defined! Please update the SPRITES dict with bounding boxes.")
        print(f"\nSprite sheet size: {Image.open(SOURCE).size}")
        print("\nAdd entries like:")
        print('    "fish_blue": (left, top, right, bottom),')
        return

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    img = Image.open(SOURCE)
    print(f"Loaded sprite sheet: {img.size}")

    for name, bbox in SPRITES.items():
        sprite = img.crop(bbox)
        output_path = os.path.join(OUTPUT_DIR, f"{name}.png")
        sprite.save(output_path)
        print(f"  Extracted: {name}.png ({sprite.size})")

    print(f"\nDone! Extracted {len(SPRITES)} sprites to {OUTPUT_DIR}/")


if __name__ == "__main__":
    extract_sprites()
    extract_sprites()
    extract_sprites()
