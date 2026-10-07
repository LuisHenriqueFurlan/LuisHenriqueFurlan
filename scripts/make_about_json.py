"""A `cat sobre.json` terminal panel (about-json.svg) that types itself line by line.

Edit ABOUT below, then: python scripts/make_about_json.py      (STATIC=1 for a frozen frame)
"""
import json
import os

ABOUT = {
    "nome": "Luís Henrique Furlan",
    "faculdade": "Engenharia de Software · UNIVAG",
    "email": "luishenriquefurlan0@gmail.com",
    "software_house": "Dev Backend @ Software House UNIVAG",
}

USER = "luis"
W = 860
BAR_H, PAD_Y, LINE = 28, 22, 26
FS, CW = 14, 8.4                 # font size and monospace advance (0.6em)
X_NUM, X_CODE = 22, 58

BG, BAR, BORDER, MUTED = "#0d1117", "#161b22", "#30363d", "#8b949e"
PUNCT, KEYC, STR, CURSOR = "#c9d1d9", "#7ee787", "#a5d6ff", "#7ee787"
FONT = "ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace"
OUT = os.environ.get("OUT", "about-json.svg")
STATIC = os.environ.get("STATIC") == "1"


def esc(s: str) -> str:
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
             .replace(" ", " "))


def code_lines():
    """[(plain_text, svg_tspans)] for each printed line."""
    lines = [("{", f'<tspan fill="{PUNCT}">{{</tspan>')]
    items = list(ABOUT.items())
    for i, (k, v) in enumerate(items):
        comma = "," if i < len(items) - 1 else ""
        ks, vs = json.dumps(k, ensure_ascii=False), json.dumps(v, ensure_ascii=False)
        plain = f"  {ks}: {vs}{comma}"
        svg = (f'<tspan fill="{PUNCT}">{esc("  ")}</tspan><tspan fill="{KEYC}">{esc(ks)}</tspan>'
               f'<tspan fill="{PUNCT}">:{esc(" ")}</tspan><tspan fill="{STR}">{esc(vs)}</tspan>'
               f'<tspan fill="{PUNCT}">{comma}</tspan>')
        lines.append((plain, svg))
    lines.append(("}", f'<tspan fill="{PUNCT}">}}</tspan>'))
    return lines


def main():
    lines = code_lines()
    H = BAR_H + 2 * PAD_Y + len(lines) * LINE
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
        f'role="img" aria-label="sobre.json: {esc(ABOUT["nome"])}">',
        f"<style>text{{font-family:{FONT};font-size:{FS}px;white-space:pre}}"
        + ("" if STATIC else ".cur{animation:blink 1s steps(1) infinite}@keyframes blink{50%{opacity:0}}")
        + "</style>",
        f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="8" fill="{BG}" stroke="{BORDER}"/>',
        f'<path d="M1 9a8 8 0 0 1 8-8h{W - 18}a8 8 0 0 1 8 8v{BAR_H - 9}H1z" fill="{BAR}"/>',
    ]
    for i, col in enumerate(("#ff5f56", "#ffbd2e", "#27c93f")):
        out.append(f'<circle cx="{16 + i * 15}" cy="{BAR_H / 2}" r="4.5" fill="{col}"/>')
    out.append(f'<text x="{W / 2}" y="{BAR_H / 2 + 3.5}" text-anchor="middle" fill="{MUTED}" '
               f'style="font-size:10px">{USER}@github ~ cat sobre.json</text>')

    START, PER_CHAR, GAP_S = 0.4, 0.018, 0.12
    t = START
    defs, body = [], []
    for i, (plain, svg) in enumerate(lines):
        y = BAR_H + PAD_Y + i * LINE
        baseline = y + FS + 2
        w = len(plain) * CW + 2
        dur = max(0.15, len(plain) * PER_CHAR)
        body.append(f'<text x="{X_NUM}" y="{baseline}" fill="{BORDER}" text-anchor="start">{i + 1}</text>')
        if STATIC:
            body.append(f'<text x="{X_CODE}" y="{baseline}">{svg}</text>')
        else:
            defs.append(
                f'<clipPath id="j{i}"><rect x="{X_CODE}" y="{y}" width="0" height="{LINE}">'
                f'<animate attributeName="width" from="0" to="{w:.1f}" begin="{t:.2f}s" dur="{dur:.2f}s" '
                f'fill="freeze"/></rect></clipPath>'
            )
            body.append(f'<text x="{X_CODE}" y="{baseline}" clip-path="url(#j{i})">{svg}</text>')
            body.append(
                f'<rect x="{X_CODE}" y="{y + 4}" width="{CW:.1f}" height="{FS + 2}" fill="{CURSOR}" opacity="0">'
                f'<set attributeName="opacity" to="0.85" begin="{t:.2f}s"/>'
                f'<animate attributeName="x" from="{X_CODE}" to="{X_CODE + w - 2:.1f}" begin="{t:.2f}s" '
                f'dur="{dur:.2f}s" fill="freeze"/>'
                f'<set attributeName="opacity" to="0" begin="{t + dur:.2f}s"/></rect>'
            )
        t += dur + GAP_S

    if defs:
        out.append("<defs>" + "".join(defs) + "</defs>")
    out += body

    # resting cursor after the closing brace
    last_y = BAR_H + PAD_Y + (len(lines) - 1) * LINE
    cur = f'<rect class="cur" x="{X_CODE + CW * 1.5:.1f}" y="{last_y + 4}" width="{CW:.1f}" height="{FS + 2}" fill="{PUNCT}"/>'
    if STATIC:
        out.append(cur)
    else:  # the group gates visibility; the CSS blink lives on the rect inside it
        out.append(f'<g opacity="0"><set attributeName="opacity" to="1" begin="{t:.2f}s"/>{cur}</g>')
    out.append("</svg>")

    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(out))
    print(f"wrote {OUT}: {W}x{H}")


if __name__ == "__main__":
    main()
