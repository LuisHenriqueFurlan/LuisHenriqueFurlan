"""Prepare a photo for ASCII conversion.

1. Remove the background (rembg) so only the subject remains.
2. Boost local contrast (CLAHE) so a flatly-lit face gets real highlights/shadows.
3. Composite on pure white so the background maps to blank space in the ASCII ramp.

Usage: python scripts/prep_photo.py source-photo.jpg [output.png]
"""
import sys

import cv2
import numpy as np
from PIL import Image
from rembg import new_session, remove

# Lightweight model: the default one needs >1 GB of RAM and gets OOM-killed on small machines.
MODEL = "u2netp"


def main(src: str, dst: str = "source-prepped.png") -> None:
    img = Image.open(src).convert("RGB")
    # keep memory low: the character grid is only ~100 columns wide anyway
    img.thumbnail((900, 900))

    # 1. cut out the subject
    cut = remove(img, session=new_session(MODEL))  # RGBA
    alpha = np.array(cut.split()[-1]).astype(np.float32) / 255.0
    # the subject mask is also saved: make_ascii_svg.py uses it to keep the background blank
    Image.fromarray((alpha * 255).astype(np.uint8), mode="L").save("source-mask.png")

    # 2. local contrast on the luminance of the subject
    gray = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2GRAY)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    gray = clahe.apply(gray).astype(np.float32)

    # 3. composite onto white
    out = gray * alpha + 255.0 * (1.0 - alpha)
    Image.fromarray(out.clip(0, 255).astype(np.uint8), mode="L").save(dst)
    print(f"wrote {dst}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    main(*sys.argv[1:3])
