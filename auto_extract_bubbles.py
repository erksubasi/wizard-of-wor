#!/usr/bin/env python3
"""
Automatically extract all distinct bubbles from underwater_bubbles.png using connected component analysis.
This will find all non-transparent regions and save each as a separate PNG.

Usage: pdm run python auto_extract_bubbles.py
"""
import os

import numpy as np
from PIL import Image
from scipy.ndimage import find_objects, label

SOURCE = "assets/images/underwater_bubbles.png"
OUTPUT_DIR = "assets/images/underwater_bubbles_extracted"

os.makedirs(OUTPUT_DIR, exist_ok=True)
img = Image.open(SOURCE).convert("RGBA")
arr = np.array(img)

# Create a mask of non-transparent pixels
mask = arr[..., 3] > 32  # alpha threshold

# Label connected regions
labeled, num = label(mask)
print(f"Found {num} bubbles.")

slices = find_objects(labeled)
count = 0
for i, slc in enumerate(slices):
    if slc is None:
        continue
    # Extract bounding box
    y0, y1 = slc[0].start, slc[0].stop
    x0, x1 = slc[1].start, slc[1].stop
    # Ignore tiny specks
    if (x1 - x0) < 16 or (y1 - y0) < 16:
        continue
    bubble = img.crop((x0, y0, x1, y1))
    out_path = os.path.join(OUTPUT_DIR, f"bubble_{count+1:02d}.png")
    bubble.save(out_path)
    print(f"Saved {out_path} ({x1-x0}x{y1-y0})")
    count += 1
print(f"\nExtracted {count} bubbles to {OUTPUT_DIR}/")
print(f"\nExtracted {count} bubbles to {OUTPUT_DIR}/")
print(f"\nExtracted {count} bubbles to {OUTPUT_DIR}/")
