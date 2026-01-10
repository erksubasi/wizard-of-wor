#!/usr/bin/env python3
"""
Generate clean circular gradient bubble PNGs for use in the game.
Creates small and large bubble textures with smooth transparency.

Usage: pdm run python generate_bubble_png.py
"""
import math
import os

from PIL import Image, ImageDraw

OUTPUT_DIR = "assets/images/underwater_assets"


def generate_bubble(size, filename):
    """Generate a clean circular bubble with gradient transparency."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    center = size // 2
    radius = size // 2 - 2

    pixels = img.load()

    for y in range(size):
        for x in range(size):
            # Distance from center
            dx = x - center
            dy = y - center
            dist = math.sqrt(dx * dx + dy * dy)

            if dist > radius:
                continue

            # Normalized distance (0 at center, 1 at edge)
            norm_dist = dist / radius

            # Bubble color: light cyan/white in center, more transparent at edges
            # Create a glass-like effect with highlight

            # Base transparency: more opaque in middle ring, transparent at center and edge
            if norm_dist < 0.3:
                # Center: fairly transparent (glass center)
                alpha = int(40 + norm_dist * 100)
            elif norm_dist < 0.7:
                # Middle ring: more visible
                alpha = int(70 + (0.7 - norm_dist) * 80)
            else:
                # Edge: fade out
                edge_factor = (1.0 - norm_dist) / 0.3
                alpha = int(90 * edge_factor)

            # Color: light cyan to white
            # Highlight in upper-left quadrant
            highlight = 0
            if dx < 0 and dy < 0 and norm_dist > 0.2 and norm_dist < 0.6:
                highlight_dist = math.sqrt(
                    (dx + radius * 0.3) ** 2 + (dy + radius * 0.3) ** 2
                )
                if highlight_dist < radius * 0.35:
                    highlight = int(80 * (1 - highlight_dist / (radius * 0.35)))

            r = min(255, 180 + highlight)
            g = min(255, 230 + highlight // 2)
            b = min(255, 250 + highlight // 3)

            pixels[x, y] = (r, g, b, alpha)

    # Add a subtle rim/edge highlight
    draw = ImageDraw.Draw(img)

    output_path = os.path.join(OUTPUT_DIR, filename)
    img.save(output_path)
    print(f"Generated: {output_path} ({size}x{size})")
    return output_path


if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    generate_bubble(64, "bubble_small.png")
    generate_bubble(128, "bubble_large.png")
    print("\nDone! Clean bubble textures generated.")
    print("\nDone! Clean bubble textures generated.")
    print("\nDone! Clean bubble textures generated.")
