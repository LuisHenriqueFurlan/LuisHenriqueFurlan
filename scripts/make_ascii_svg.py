"""Turn the prepped photo into a self-typing, monochrome ASCII portrait (SVG).

Needs source-prepped.png and source-mask.png from prep_photo.py.
Dark pixels pick dense glyphs, bright skin and the background become blank, so the
face reads like a light pencil drawing on the dark panel. Each row is revealed by a
left-to-right clip wipe with a block cursor riding the edge, staggered top to bottom;
it plays once and freezes (SMIL, which GitHub renders).

Usage: python scripts/make_ascii_svg.py   # writes ascii-portrait.svg
       STATIC=1 OUT=/tmp/x.svg python scripts/make_ascii_svg.py   # frozen frame
"""
import os

import numpy as np
from PIL import Image, ImageFilter

RAMP = " .`:-=+*cs#%@"   # bright (sparse) -> dark (dense); leading space clears the background

# panel geometry (README shows it at width 440, next to the 420-wide stats panel)
W, H = 440, 540
BAR_H, FOOT_H = 28, 30
PAD_X, PAD_Y = 12, 10
FONT_SIZE, CHAR_W, LINE_H = 7.0, 4.2, 7.6
COLS = int((W - 2 * PAD_X) // CHAR_W)                       # 99
ROWS = int((H - BAR_H - FOOT_H - 2 * PAD_Y) // LINE_H)      # 60

CROP = (45, 50, 505, 555)          # head (hair to chin) on the prepped image (x0, y0, x1, y1)
BLANK_BOXES = [(0, 0, 208, 168)]   # leftover wallpaper bit in the cut-out
LO, HI, GAMMA = 60, 215, 1.2       # levels: <=LO is full ink, >=HI is blank
SHARPEN = 250                      # unsharp-mask strength, keeps eyes/brows/mouth crisp

USER, NAME = "luis", "Luís Henrique Furlan"
BG, BAR, MUTED, FG, KEY = "#0d1117", "#161b22", "#8b949e", "#c9d1d9", "#7ee787"
FONT = "ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace"
OUT = os.environ.get("OUT", "ascii-portrait.svg")
STATIC = os.environ.get("STATIC") == "1"


def build_grid():
    gray = Image.open("source-prepped.png").convert("L")
    mask = Image.open("source-mask.png").convert("L")
    m = np.array(mask).astype(np.float32)
    for x0, y0, x1, y1 in BLANK_BOXES:
        m[y0:y1, x0:x1] = 0
    mask = Image.fromarray(m.astype(np.uint8))

    gray = gray.crop(CROP).filter(ImageFilter.UnsharpMask(radius=6, percent=SHARPEN, threshold=2))
    mask = mask.crop(CROP)
    g = np.array(gray.resize((COLS, ROWS), Image.LANCZOS)).astype(np.float32)
    a = np.array(mask.resize((COLS, ROWS), Image.BOX)).astype(np.float32) / 255.0

    t = ((g - LO) / (HI - LO)).clip(0, 1) ** GAMMA   # 0 = dark .. 1 = bright
    idx = np.rint((1 - t) * (len(RAMP) - 1)).astype(int)
    return ["".join(RAMP[idx[r, c]] if a[r, c] > 0.5 else " " for c in range(COLS)) for r in range(ROWS)]


def esc(s: str) -> str:
    # no-break spaces: browsers collapse runs of normal spaces in SVG text
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace(" ", " ")


def main():
    lines = build_grid()
    text_w = COLS * CHAR_W
    x0 = (W - text_w) / 2
    y_top = BAR_H + PAD_Y

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
        f'role="img" aria-label="Retrato ASCII de {NAME}">',
        f"<style>text{{font-family:{FONT}}}"
        + ("" if STATIC else ".cur{animation:blink 1s steps(1) infinite}@keyframes blink{50%{opacity:0}}")
        + "</style>",
        f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="8" fill="{BG}" stroke="#30363d"/>',
        f'<path d="M1 9a8 8 0 0 1 8-8h{W - 18}a8 8 0 0 1 8 8v{BAR_H - 9}H1z" fill="{BAR}"/>',
    ]
    for i, col in enumerate(("#ff5f56", "#ffbd2e", "#27c93f")):
        out.append(f'<circle cx="{16 + i * 15}" cy="{BAR_H / 2}" r="4.5" fill="{col}"/>')
    out.append(f'<text x="{W / 2}" y="{BAR_H / 2 + 3.5}" text-anchor="middle" fill="{MUTED}" '
               f'font-size="10">{USER}@github ~ ./portrait.sh</text>')

    ROW_DUR, STAGGER, START = 0.5, 0.06, 0.3
    out.append("<defs>")
    for i in range(ROWS):
        y = y_top + i * LINE_H
        if STATIC:
            out.append(f'<clipPath id="c{i}"><rect x="{x0}" y="{y:.2f}" width="{text_w:.1f}" height="{LINE_H}"/></clipPath>')
        else:
            out.append(
                f'<clipPath id="c{i}"><rect x="{x0}" y="{y:.2f}" width="0" height="{LINE_H}">'
                f'<animate attributeName="width" from="0" to="{text_w:.1f}" begin="{START + i * STAGGER:.3f}s" '
                f'dur="{ROW_DUR}s" fill="freeze"/></rect></clipPath>'
            )
    out.append("</defs>")

    out.append(f'<g fill="{FG}" font-size="{FONT_SIZE}" xml:space="preserve" style="white-space:pre">')
    for i, line in enumerate(lines):
        if line.strip():
            y = y_top + i * LINE_H + FONT_SIZE
            out.append(f'<text x="{x0}" y="{y:.2f}" textLength="{text_w:.1f}" lengthAdjust="spacing" '
                       f'clip-path="url(#c{i})">{esc(line)}</text>')
    out.append("</g>")

    if not STATIC:
        for i, line in enumerate(lines):
            if not line.strip():
                continue
            y, begin = y_top + i * LINE_H, START + i * STAGGER
            out.append(
                f'<rect x="{x0}" y="{y:.2f}" width="{CHAR_W}" height="{LINE_H}" fill="{KEY}" opacity="0">'
                f'<set attributeName="opacity" to="0.9" begin="{begin:.3f}s"/>'
                f'<animate attributeName="x" from="{x0}" to="{x0 + text_w - CHAR_W:.1f}" begin="{begin:.3f}s" '
                f'dur="{ROW_DUR}s" fill="freeze"/>'
                f'<set attributeName="opacity" to="0" begin="{begin + ROW_DUR:.3f}s"/></rect>'
            )

    # footer prompt, like a shell after the command finished
    fy = H - FOOT_H / 2 + 4
    done = START + ROWS * STAGGER + ROW_DUR
    appear = "" if STATIC else (f'<set attributeName="opacity" to="1" begin="{done:.2f}s"/>')
    out.append(
        f'<g opacity="{1 if STATIC else 0}">{appear}'
        f'<text x="{PAD_X + 2}" y="{fy}" font-size="9"><tspan fill="{KEY}">{USER}@github</tspan>'
        f'<tspan fill="{MUTED}">:~$ whoami</tspan><tspan fill="{FG}">  {NAME}</tspan></text>'
        f'<rect class="cur" x="{PAD_X + 2 + (len(f"{USER}@github:~$ whoami  {NAME}") + 1) * 5.4:.1f}" y="{fy - 8}" '
        f'width="5" height="10" fill="{FG}"/></g>'
    )
    out.append("</svg>")
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(out))
    print(f"wrote {OUT}: {COLS}x{ROWS} chars, {W}x{H}")


if __name__ == "__main__":
    main()
