"""Turn the prepped photo into a self-typing, monochrome ASCII portrait (SVG).

Needs source-prepped.png and source-mask.png from prep_photo.py.
Each row is revealed by a left-to-right clip wipe (a block cursor rides the edge),
staggered top to bottom. It plays once and freezes (SMIL, which GitHub renders).

Usage: python scripts/make_ascii_svg.py   # writes ascii-portrait.svg
"""
import os

import numpy as np
from PIL import Image, ImageFilter

# bright (sparse) -> dark (dense) ramp from the tutorial. The panel is dark with light
# glyphs, so we index it the other way round: bright skin -> dense glyph.
RAMP = " .`:-=+*cs#%@"

COLS = 100                      # characters per row
CROP = (40, 40, 520, 880)       # x0, y0, x1, y1 on the prepped image (head, shoulders, tie)
BLANK_BOXES = [(0, 0, 208, 168)]  # leftover wallpaper bit in the cut-out (x0, y0, x1, y1)
FADE_FROM = 0.62                # rows below this fraction fade toward blank
GAMMA = 0.9                     # <1 lifts midtones a little
LIFT = 0.22                     # shadow floor: dark hair/suit stay visible on the dark panel

FONT_SIZE = 7.0
CHAR_W = 4.2                    # monospace advance ~0.6em
LINE_H = 7.6
PAD_X, PAD_Y = 14, 12
BAR_H = 28

BG = "#0d1117"
BAR = "#161b22"
FG = "#c9d1d9"
CURSOR = "#7ee787"
OUT = os.environ.get("OUT", "ascii-portrait.svg")
STATIC = os.environ.get("STATIC") == "1"  # frozen final frame, for local previews


def build_grid():
    gray = Image.open("source-prepped.png").convert("L")
    mask = Image.open("source-mask.png").convert("L")
    if gray.size != mask.size:
        raise SystemExit("prepped image and mask differ in size; rerun prep_photo.py")

    m = np.array(mask).astype(np.float32)
    for x0, y0, x1, y1 in BLANK_BOXES:
        m[y0:y1, x0:x1] = 0
    mask = Image.fromarray(m.astype(np.uint8))

    gray, mask = gray.crop(CROP), mask.crop(CROP)
    # unsharp mask: makes eyes, brows, nose and mouth survive the downsample
    gray = gray.filter(ImageFilter.UnsharpMask(radius=7, percent=220, threshold=2))
    cw, ch = gray.size
    rows = round(COLS * (ch / cw) * (CHAR_W / LINE_H))
    g = np.array(gray.resize((COLS, rows), Image.LANCZOS)).astype(np.float32) / 255.0
    a = np.array(mask.resize((COLS, rows), Image.BOX)).astype(np.float32) / 255.0

    g = np.power(g.clip(0, 1), GAMMA)
    g = LIFT + (1.0 - LIFT) * g
    # fade the lower part of the frame (sweater) so the face carries the picture
    fade = np.ones(rows, dtype=np.float32)
    start = int(rows * FADE_FROM)
    fade[start:] = np.linspace(1.0, 0.25, rows - start)
    g = g * fade[:, None]
    idx = np.rint(g * (len(RAMP) - 1)).astype(int)  # bright -> dense
    lines = []
    for r in range(rows):
        lines.append("".join(RAMP[idx[r, c]] if a[r, c] > 0.5 else " " for c in range(COLS)))
    return lines


def esc(s: str) -> str:
    # spaces become no-break spaces: browsers collapse runs of normal spaces in SVG text,
    # which would squash the picture (and textLength would then stretch it).
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace(" ", "\u00a0")


def main():
    lines = build_grid()
    rows = len(lines)
    text_w = COLS * CHAR_W
    W = text_w + 2 * PAD_X
    H = BAR_H + PAD_Y * 2 + rows * LINE_H

    out = []
    out.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:.1f} {H:.1f}" '
        f'width="{W:.0f}" height="{H:.0f}" role="img" aria-label="ASCII portrait of Luis Henrique Furlan">'
    )
    out.append(f'<rect width="{W:.1f}" height="{H:.1f}" rx="10" fill="{BG}"/>')
    out.append(
        f'<path d="M0 10a10 10 0 0 1 10-10h{W - 20:.1f}a10 10 0 0 1 10 10v{BAR_H - 10}H0z" fill="{BAR}"/>'
    )
    for i, col in enumerate(("#ff5f56", "#ffbd2e", "#27c93f")):
        out.append(f'<circle cx="{16 + i * 16}" cy="{BAR_H / 2}" r="5" fill="{col}"/>')
    out.append(
        f'<text x="{W / 2:.1f}" y="{BAR_H / 2 + 3.5}" text-anchor="middle" fill="#8b949e" '
        f'font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,\'Liberation Mono\',monospace" '
        f'font-size="10">portrait.sh</text>'
    )

    out.append("<defs>")
    ROW_DUR, STAGGER, START = 0.55, 0.045, 0.3
    for i in range(rows):
        y = BAR_H + PAD_Y + i * LINE_H
        begin = START + i * STAGGER
        if STATIC:
            out.append(
                f'<clipPath id="c{i}"><rect x="{PAD_X}" y="{y:.2f}" width="{text_w:.1f}" height="{LINE_H:.2f}"/></clipPath>'
            )
            continue
        out.append(
            f'<clipPath id="c{i}"><rect x="{PAD_X}" y="{y:.2f}" width="0" height="{LINE_H:.2f}">'
            f'<animate attributeName="width" from="0" to="{text_w:.1f}" begin="{begin:.3f}s" '
            f'dur="{ROW_DUR}s" fill="freeze"/></rect></clipPath>'
        )
    out.append("</defs>")

    out.append(
        f'<g fill="{FG}" font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,\'Liberation Mono\',monospace" '
        f'font-size="{FONT_SIZE}" xml:space="preserve" style="white-space:pre">'
    )
    for i, line in enumerate(lines):
        if not line.strip():
            continue
        y = BAR_H + PAD_Y + i * LINE_H
        out.append(
            f'<text x="{PAD_X}" y="{y + FONT_SIZE:.2f}" textLength="{text_w:.1f}" lengthAdjust="spacing" '
            f'clip-path="url(#c{i})">{esc(line)}</text>'
        )
    out.append("</g>")

    # block cursor riding the wipe edge of every row
    for i, line in enumerate(lines):
        if STATIC:
            break
        y = BAR_H + PAD_Y + i * LINE_H
        begin = START + i * STAGGER
        out.append(
            f'<rect x="{PAD_X}" y="{y:.2f}" width="{CHAR_W:.1f}" height="{LINE_H:.2f}" fill="{CURSOR}" opacity="0">'
            f'<set attributeName="opacity" to="0.9" begin="{begin:.3f}s"/>'
            f'<animate attributeName="x" from="{PAD_X}" to="{PAD_X + text_w - CHAR_W:.1f}" begin="{begin:.3f}s" '
            f'dur="{ROW_DUR}s" fill="freeze"/>'
            f'<set attributeName="opacity" to="0" begin="{begin + ROW_DUR:.3f}s"/></rect>'
        )

    out.append("</svg>")
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(out))
    print(f"wrote {OUT}: {COLS}x{rows} chars, {W:.0f}x{H:.0f}px")


if __name__ == "__main__":
    main()
