#!/usr/bin/env python3
"""
Extract individual bubble sprites from underwater_bubbles.png.
Update the BUBBLES dict below with bounding boxes for each bubble.

Usage: pdm run python extract_underwater_bubbles.py
"""
import os

from PIL import Image

SOURCE = "assets/images/underwater_bubbles.png"
OUTPUT_DIR = "assets/images/underwater_bubbles_extracted"

# Manually defined bounding boxes for a few bubbles (left, top, right, bottom)
BUBBLES = {
    "bubble1": (40, 40, 180, 180),
    "bubble2": (220, 60, 360, 200),
    "bubble3": (400, 30, 540, 170),
    "bubble4": (600, 60, 740, 200),
    "bubble5": (800, 40, 940, 180),
}


def extract_bubbles():
    if not BUBBLES:
        print("No bubbles defined! Please update the BUBBLES dict with bounding boxes.")
        print(f"\nSprite sheet size: {Image.open(SOURCE).size}")
        print("\nAdd entries like:")
        print('    "bubble1": (left, top, right, bottom),')
        return
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    img = Image.open(SOURCE)
    print(f"Loaded sprite sheet: {img.size}")
    for name, bbox in BUBBLES.items():
        bubble = img.crop(bbox)
        output_path = os.path.join(OUTPUT_DIR, f"{name}.png")
        bubble.save(output_path)
        print(f"  Extracted: {name}.png ({bubble.size})")
    print(f"\nDone! Extracted {len(BUBBLES)} bubbles to {OUTPUT_DIR}/")


if __name__ == "__main__":
    extract_bubbles()
    extract_bubbles()
    extract_bubbles()
