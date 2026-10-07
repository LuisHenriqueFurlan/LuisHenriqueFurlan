"""A `cat sobre.json` terminal panel (about-json.svg) that types itself line by line.
It sits in the README's whoami row, next to the stats panel, at the same height.

Edit ABOUT below, then: python scripts/make_about_json.py      (STATIC=1 for a frozen frame)
Lists listed in INLINE_LISTS stay on one line; other lists print one item per line.
"""
import json
import os

ABOUT = {
    "nome": "Luís Henrique Furlan",
    "curso": "Engenharia de Software",
    "faculdade": "UNIVAG",
    "email": "luishenriquefurlan0@gmail.com",
    "software_house": "Software House UNIVAG",
    "atuacao": ["Fullstack", "Cibersegurança"],
    "stacks": [
        "TypeScript",
        "JavaScript",
        "Node.js",
        "Fastify",
        "React",
        "Prisma",
        "PostgreSQL",
        "MySQL",
        "Python",
    ],
}
INLINE_LISTS = {"atuacao"}

USER = "luis"
W, H = 440, 540                  # same size as the stats panel's row partner
BAR_H, FOOT_H = 28, 0
FS = 12.5
CW = FS * 0.6                    # monospace advance
X_NUM, X_CODE = 18, 44

BG, BAR, BORDER, MUTED = "#0d1117", "#161b22", "#30363d", "#8b949e"
PUNCT, KEYC, STR, CURSOR = "#c9d1d9", "#7ee787", "#a5d6ff", "#7ee787"
FONT = "ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace"
OUT = os.environ.get("OUT", "about-json.svg")
STATIC = os.environ.get("STATIC") == "1"


def esc(s: str) -> str:
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
             .replace(" ", " "))


def t(color, text):
    return f'<tspan fill="{color}">{esc(text)}</tspan>'


def q(s):
    return json.dumps(s, ensure_ascii=False)


def code_lines():
    """[(plain_text, svg)] for each printed line."""
    out = [("{", t(PUNCT, "{"))]
    items = list(ABOUT.items())
    for i, (k, v) in enumerate(items):
        comma = "," if i < len(items) - 1 else ""
        head_plain, head_svg = f"  {q(k)}: ", t(PUNCT, "  ") + t(KEYC, q(k)) + t(PUNCT, ": ")
        if isinstance(v, list) and k in INLINE_LISTS:
            parts = [t(STR, q(x)) for x in v]
            body_svg = t(PUNCT, "[") + t(PUNCT, ", ").join(parts) + t(PUNCT, "]" + comma)
            out.append((head_plain + "[" + ", ".join(q(x) for x in v) + "]" + comma, head_svg + body_svg))
        elif isinstance(v, list):
            out.append((head_plain + "[", head_svg + t(PUNCT, "[")))
            for j, x in enumerate(v):
                c = "," if j < len(v) - 1 else ""
                out.append((f"    {q(x)}{c}", t(PUNCT, "    ") + t(STR, q(x)) + t(PUNCT, c)))
            out.append(("  ]" + comma, t(PUNCT, "  ]" + comma)))
        else:
            out.append((head_plain + q(v) + comma, head_svg + t(STR, q(v)) + t(PUNCT, comma)))
    out.append(("}", t(PUNCT, "}")))
    return out


def main():
    lines = code_lines()
    widest = max(len(p) for p, _ in lines) * CW + X_CODE
    if widest > W - 10:
        raise SystemExit(f"longest line is {widest:.0f}px wide (> {W - 10}); shorten a value or lower FS")

    pad_y = 18
    line_h = min(26.0, (H - BAR_H - FOOT_H - 2 * pad_y) / len(lines))
    block_h = line_h * len(lines)
    y0 = BAR_H + (H - BAR_H - FOOT_H - block_h) / 2

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

    START, PER_CHAR, GAP_S = 0.4, 0.012, 0.05
    clock = START
    defs, body = [], []
    for i, (plain, svg) in enumerate(lines):
        y = y0 + i * line_h
        baseline = y + line_h / 2 + FS * 0.36
        w = len(plain) * CW + 2
        dur = max(0.08, len(plain) * PER_CHAR)
        body.append(f'<text x="{X_NUM + 10}" y="{baseline:.1f}" fill="{BORDER}" style="font-size:10.5px" '
                    f'text-anchor="end">{i + 1}</text>')
        if STATIC:
            body.append(f'<text x="{X_CODE}" y="{baseline:.1f}">{svg}</text>')
        else:
            defs.append(
                f'<clipPath id="j{i}"><rect x="{X_CODE}" y="{y:.1f}" width="0" height="{line_h:.1f}">'
                f'<animate attributeName="width" from="0" to="{w:.1f}" begin="{clock:.2f}s" dur="{dur:.2f}s" '
                f'fill="freeze"/></rect></clipPath>'
            )
            body.append(f'<text x="{X_CODE}" y="{baseline:.1f}" clip-path="url(#j{i})">{svg}</text>')
            body.append(
                f'<rect x="{X_CODE}" y="{baseline - FS * 0.85:.1f}" width="{CW:.1f}" height="{FS * 1.1:.1f}" '
                f'fill="{CURSOR}" opacity="0">'
                f'<set attributeName="opacity" to="0.85" begin="{clock:.2f}s"/>'
                f'<animate attributeName="x" from="{X_CODE}" to="{X_CODE + w - 2:.1f}" begin="{clock:.2f}s" '
                f'dur="{dur:.2f}s" fill="freeze"/>'
                f'<set attributeName="opacity" to="0" begin="{clock + dur:.2f}s"/></rect>'
            )
        clock += dur + GAP_S

    if defs:
        out.append("<defs>" + "".join(defs) + "</defs>")
    out += body

    # resting cursor after the closing brace
    last_base = y0 + (len(lines) - 1) * line_h + line_h / 2 + FS * 0.36
    cur = (f'<rect class="cur" x="{X_CODE + CW * 1.5:.1f}" y="{last_base - FS * 0.85:.1f}" '
           f'width="{CW:.1f}" height="{FS * 1.1:.1f}" fill="{PUNCT}"/>')
    if STATIC:
        out.append(cur)
    else:  # the group gates visibility; the CSS blink lives on the rect inside it
        out.append(f'<g opacity="0"><set attributeName="opacity" to="1" begin="{clock:.2f}s"/>{cur}</g>')
    out.append("</svg>")

    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(out))
    print(f"wrote {OUT}: {W}x{H}, {len(lines)} lines, typing ends at {clock:.1f}s")


if __name__ == "__main__":
    main()
