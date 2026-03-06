#!/usr/bin/env python3
"""
Generate all required icon sizes for the Chrome extension from the source PNG.
Run this once from the chrome-extension/ directory:
    python generate_icons.py
"""
import os
from PIL import Image

SRC  = os.path.join(os.path.dirname(__file__), "../..",
                    "Users", "akashvishwakarma", ".gemini", "antigravity",
                    "brain", "71cdc07a-43ae-4140-9e7b-e74288cee4a5",
                    "drishti_icon_1772791090337.png")

# Fallback: look for any PNG in current dir named drishti_icon*
if not os.path.exists(SRC):
    import glob
    candidates = glob.glob(os.path.expanduser("~/.gemini/antigravity/brain/*/drishti_icon*.png"))
    SRC = candidates[0] if candidates else None

SIZES = [16, 32, 48, 128]
OUT_DIR = os.path.join(os.path.dirname(__file__), "icons")
os.makedirs(OUT_DIR, exist_ok=True)

if SRC and os.path.exists(SRC):
    img = Image.open(SRC).convert("RGBA")
    for size in SIZES:
        out = img.resize((size, size), Image.Resampling.LANCZOS)
        out_path = os.path.join(OUT_DIR, f"icon{size}.png")
        out.save(out_path, "PNG")
        print(f"  ✅ {out_path}")
    print("\nAll icons generated successfully.")
else:
    # Generate minimal placeholder icons using pure Pillow (no source image needed)
    print(f"Source icon not found. Generating placeholder icons...")
    for size in SIZES:
        img = Image.new("RGBA", (size, size), (8, 13, 24, 255))
        # Draw simple eye shape
        from PIL import ImageDraw, ImageFilter
        draw = ImageDraw.Draw(img)
        m = size // 2
        r_outer = int(size * 0.45)
        r_inner = int(size * 0.22)
        r_dot   = int(size * 0.08)
        # Outer circle
        draw.ellipse([m-r_outer, m-r_outer, m+r_outer, m+r_outer],
                     outline=(0, 245, 255, 200), width=max(1, size//32))
        # Inner circle
        draw.ellipse([m-r_inner, m-r_inner, m+r_inner, m+r_inner],
                     fill=(0, 245, 255, 180))
        # Center dot
        draw.ellipse([m-r_dot, m-r_dot, m+r_dot, m+r_dot],
                     fill=(8, 13, 24, 255))
        out_path = os.path.join(OUT_DIR, f"icon{size}.png")
        img.save(out_path, "PNG")
        print(f"  ✅ Placeholder {out_path}")
    print("\nPlaceholder icons generated. Replace with the actual DRISHTI icon.")

if __name__ == "__main__":
    pass
