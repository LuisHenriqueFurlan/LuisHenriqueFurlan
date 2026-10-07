"""Neofetch-style info card (SVG) that prints itself line by line.

Edit the CONTENT below, then: python scripts/make_info_card.py   # writes info-card.svg
STATIC=1 writes a frozen frame (handy for local previews).
"""
import os
import re

USER = "luis"
HOST = "furlan"

# (key, value) rows. A key of "" continues the previous key on a new line.
# A row of None draws a blank spacer line.
CONTENT = [
    ("Nome", "Luís Henrique Furlan"),
    ("Curso", "Engenharia de Software"),
    ("Agora", "Dev Backend @ Software House UNIVAG"),
    ("Estudo", "Formação Back-End Node.js (Alura)"),
    ("Foco", "APIs · bancos de dados · AppSec"),
    ("Buscando", "estágio em TI / dados"),
    None,
    ("Stack", "TypeScript · Node.js · Fastify"),
    ("", "Prisma · PostgreSQL · MySQL"),
    ("", "SQL Server · Python · React"),
    None,
    ("Destaques", "store-management-api"),
    ("", "  - gestão de loja, em uso real"),
    ("", "nobres-assados-project"),
    ("", "  - pedidos online + painel admin"),
    ("", "pncp-dispensa-cli"),
    ("", "  - CLI de licitações abertas no PNCP"),
    ("", "robo-sumo-arduino"),
    ("", "  - robô autônomo, máquina de estados"),
    None,
    ("Contato", "luishenriquefurlan0@gmail.com"),
]

W, H = 490, 640            # H is replaced by the portrait's on-screen height when available
PORTRAIT_SVG, PORTRAIT_SHOWN_W = "ascii-portrait.svg", 370   # README widths: 370 + 490 = 860
BAR_H = 28
PAD_X = 22
FONT = "ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace"
FS = 13
LINE = 24
KEY_W = 92                 # x offset of values

BG, BAR, MUTED = "#0d1117", "#161b22", "#8b949e"
KEY, VAL, ACCENT = "#7ee787", "#c9d1d9", "#79c0ff"
PALETTE = ["#ff7b72", "#ffa657", "#f2cc60", "#7ee787", "#79c0ff", "#d2a8ff", "#c9d1d9", "#484f58"]

STATIC = os.environ.get("STATIC") == "1"
OUT = os.environ.get("OUT", "info-card.svg")


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def target_height() -> float:
    """Match the portrait panel's height as it is displayed in the README."""
    try:
        head = open(PORTRAIT_SVG, encoding="utf-8").read(400)
        vb = re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', head)
        pw, ph = float(vb.group(1)), float(vb.group(2))
        return ph * PORTRAIT_SHOWN_W / pw * (W / 490)
    except (OSError, AttributeError):
        return H


def main():
    title = f"{USER}@{HOST}"
    rows = []  # list of svg snippets, one per printed line
    y = BAR_H + 34

    rows.append(
        (y, f'<text x="{PAD_X}" y="{y}"><tspan fill="{KEY}" font-weight="700">{USER}</tspan>'
            f'<tspan fill="{VAL}">@</tspan><tspan fill="{KEY}" font-weight="700">{HOST}</tspan></text>')
    )
    y += LINE * 0.8
    rows.append((y, f'<text x="{PAD_X}" y="{y}" fill="{MUTED}">{"-" * len(title)}</text>'))
    y += LINE

    rows_key = ""
    for item in CONTENT:
        if item is None:
            y += LINE * 0.55
            continue
        key, val = item
        is_sub = val.startswith("  - ")
        fill = MUTED if is_sub else (ACCENT if key == "Destaques" or (key == "" and rows_key == "Destaques") else VAL)
        if key:
            rows_key = key
        key_svg = f'<tspan fill="{KEY}" font-weight="700">{esc(key)}</tspan><tspan fill="{VAL}">:</tspan>' if key else ""
        rows.append(
            (y, f'<text x="{PAD_X}" y="{y}">{key_svg}</text>'
                f'<text x="{PAD_X + KEY_W}" y="{y}" fill="{fill}">{esc(val)}</text>')
        )
        y += LINE

    # neofetch colour blocks
    y += 6
    blocks = "".join(
        f'<rect x="{PAD_X + i * 24}" y="{y - 12}" width="22" height="14" rx="2" fill="{c}"/>'
        for i, c in enumerate(PALETTE)
    )
    rows.append((y, blocks))
    y += LINE

    # blinking prompt at the end
    prompt_y = y + 8
    height = max(target_height(), prompt_y + 24)

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {height:.0f}" width="{W}" height="{height:.0f}" '
        f'role="img" aria-label="Info card: {esc(title)}">',
        "<style>",
        f"text{{font-family:{FONT};font-size:{FS}px;white-space:pre}}",
    ]
    if not STATIC:
        out += [
            ".l{opacity:0;animation:in .35s ease-out forwards}",
            "@keyframes in{from{opacity:0;transform:translateX(-8px)}to{opacity:1;transform:none}}",
            ".cur{animation:blink 1s steps(1) infinite}",
            "@keyframes blink{50%{opacity:0}}",
        ]
    out.append("</style>")
    out.append(f'<rect width="{W}" height="{height:.0f}" rx="10" fill="{BG}"/>')
    out.append(f'<path d="M0 10a10 10 0 0 1 10-10h{W - 20}a10 10 0 0 1 10 10v{BAR_H - 10}H0z" fill="{BAR}"/>')
    for i, col in enumerate(("#ff5f56", "#ffbd2e", "#27c93f")):
        out.append(f'<circle cx="{16 + i * 16}" cy="{BAR_H / 2}" r="5" fill="{col}"/>')
    out.append(
        f'<text x="{W / 2}" y="{BAR_H / 2 + 3.5}" text-anchor="middle" fill="{MUTED}" style="font-size:10px">neofetch</text>'
    )

    START, STEP = 0.6, 0.12
    for i, (_, svg) in enumerate(rows):
        style = "" if STATIC else f' style="animation-delay:{START + i * STEP:.2f}s"'
        out.append(f'<g class="l"{style}>{svg}</g>')

    end = START + len(rows) * STEP
    style = "" if STATIC else f' style="animation-delay:{end:.2f}s"'
    out.append(
        f'<g class="l"{style}><text x="{PAD_X}" y="{prompt_y}"><tspan fill="{KEY}">{USER}@github</tspan>'
        f'<tspan fill="{VAL}"> ~ $ </tspan></text>'
        f'<rect class="cur" x="{PAD_X + 15 * FS * 0.6:.1f}" y="{prompt_y - 11}" width="8" height="14" fill="{VAL}"/></g>'
    )
    out.append("</svg>")

    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(out))
    print(f"wrote {OUT}: {W}x{height:.0f}")


if __name__ == "__main__":
    main()
