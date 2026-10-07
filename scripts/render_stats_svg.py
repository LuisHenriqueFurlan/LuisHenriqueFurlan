"""Render data/contributions.json as a stats panel (stats-card.svg): six stat tiles plus a
contributions-per-month bar chart. Tiles fade in and bars grow once on load, then freeze.
Without data (before the workflow's first run) every value shows as a dash.

Usage: python scripts/render_stats_svg.py      (STATIC=1 for a frozen frame)
"""
import json
import os
from datetime import date

DATA = os.path.join("data", "contributions.json")
OUT = os.environ.get("OUT", "stats-card.svg")
STATIC = os.environ.get("STATIC") == "1"

W, H = 420, 540          # README shows it at 420, next to the 440-wide portrait (same height)
BAR_H, PAD, GAP = 28, 12, 8
TILE_H = 80

USER = "luis"
BG, BAR, LINE, TILE = "#0d1117", "#161b22", "#30363d", "#0d1117"
MUTED, TEXT, KEY, BARC, PEAK = "#8b949e", "#c9d1d9", "#39d353", "#26a641", "#69f0a0"
FONT = "ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace"
MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]


def load():
    try:
        with open(DATA, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def n(v) -> str:
    return f"{v:,}".replace(",", ".")


def d(iso) -> str:
    if not iso:
        return ""
    x = date.fromisoformat(iso)
    return f"{x.day} {MESES[x.month - 1]}"


def span(s) -> str:
    if not s or not s.get("days"):
        return "sem sequência ativa"
    return f"{d(s['start'])} – {d(s['end'])}"


def tiles(data):
    if not data:
        dash = ("—", "", "aguardando o primeiro update")
        return [("sequência atual", *dash), ("maior sequência", *dash), ("contribuições", *dash),
                ("dias ativos", *dash), ("melhor dia", *dash), ("média / dia ativo", *dash)]
    cur, lon = data["current_streak"], data["longest_streak"]
    active, total_days = data["active_days"], data["total_days"]
    pct = round(100 * active / total_days) if total_days else 0
    avg = f"{data['avg_per_active_day']:.1f}".replace(".", ",")
    dia = lambda k: "dia" if k == 1 else "dias"
    return [
        ("sequência atual", str(cur["days"]), dia(cur["days"]), span(cur)),
        ("maior sequência", str(lon["days"]), dia(lon["days"]), span(lon)),
        ("contribuições", n(data["total"]), "", "no último ano"),
        ("dias ativos", str(active), f"/ {total_days}", f"{pct}% do ano"),
        ("melhor dia", str(data["best_day"]["count"]), "", d(data["best_day"]["date"])),
        ("média / dia ativo", avg, "", "contribuições"),
    ]


def main():
    data = load()
    tw = (W - 2 * PAD - GAP) / 2
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
        f'role="img" aria-label="Estatísticas de contribuição no GitHub">',
        "<style>",
        f"text{{font-family:{FONT};fill:{MUTED}}}",
        f".l{{font-size:10px}}.v{{font-size:26px;font-weight:700;fill:{KEY}}}.u{{font-size:11px;fill:{TEXT}}}"
        f".s{{font-size:9.5px}}.m{{font-size:9px;text-anchor:middle}}.p{{font-size:9px;fill:{PEAK};text-anchor:middle}}",
    ]
    if not STATIC:
        out += [
            ".t{opacity:0;animation:in .45s ease-out forwards}",
            "@keyframes in{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}",
            ".b{transform-box:fill-box;transform-origin:bottom;transform:scaleY(0);"
            "animation:grow .6s cubic-bezier(.2,.8,.3,1) forwards}",
            "@keyframes grow{to{transform:scaleY(1)}}",
        ]
    out.append("</style>")
    out.append(f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="8" fill="{BG}" stroke="{LINE}"/>')
    out.append(f'<path d="M1 9a8 8 0 0 1 8-8h{W - 18}a8 8 0 0 1 8 8v{BAR_H - 9}H1z" fill="{BAR}"/>')
    for i, col in enumerate(("#ff5f56", "#ffbd2e", "#27c93f")):
        out.append(f'<circle cx="{16 + i * 15}" cy="{BAR_H / 2}" r="4.5" fill="{col}"/>')
    out.append(f'<text x="{W / 2}" y="{BAR_H / 2 + 3.5}" text-anchor="middle" font-size="10">'
               f'{USER}@github ~ ./stats.sh</text>')

    delay = lambda k: "" if STATIC else f' style="animation-delay:{0.4 + k * 0.15:.2f}s"'

    y0 = BAR_H + PAD
    for k, (label, value, unit, sub) in enumerate(tiles(data)):
        col, row = k % 2, k // 2
        x, y = PAD + col * (tw + GAP), y0 + row * (TILE_H + GAP)
        unit_x = x + 12 + len(value) * 15.6 + 6
        out.append(
            f'<g class="t"{delay(k)}>'
            f'<rect x="{x:.1f}" y="{y}" width="{tw:.1f}" height="{TILE_H}" rx="6" fill="{TILE}" stroke="{LINE}"/>'
            f'<text class="l" x="{x + 12:.1f}" y="{y + 19}">$ {label}</text>'
            f'<text class="v" x="{x + 12:.1f}" y="{y + 50}">{value}</text>'
            + (f'<text class="u" x="{unit_x:.1f}" y="{y + 49}">{unit}</text>' if unit else "")
            + f'<text class="s" x="{x + 12:.1f}" y="{y + 68}">{sub}</text></g>'
        )

    # contributions / month
    cy = y0 + 3 * (TILE_H + GAP)
    ch = H - PAD - cy
    cw = W - 2 * PAD
    out.append(f'<g class="t"{delay(6)}>'
               f'<rect x="{PAD}" y="{cy}" width="{cw}" height="{ch}" rx="6" fill="{TILE}" stroke="{LINE}"/>'
               f'<text class="l" x="{PAD + 12}" y="{cy + 19}">$ contribuições / mês</text></g>')

    months = list((data or {}).get("monthly", {}).items())[-12:]
    if not months:
        out.append(f'<text class="s" x="{W / 2}" y="{cy + ch / 2 + 4}" text-anchor="middle">aguardando dados…</text>')
    else:
        base = cy + ch - 26
        top = cy + 48
        slot = (cw - 32) / len(months)
        bw = slot * 0.62
        peak = max(v for _, v in months) or 1
        pk = max(range(len(months)), key=lambda i: months[i][1])
        for i, (ym, v) in enumerate(months):
            bx = PAD + 16 + i * slot + (slot - bw) / 2
            bh = max(2.0, (base - top) * v / peak) if v else 2.0
            fill = PEAK if i == pk and v else (BARC if v else LINE)
            st = "" if STATIC else f' style="animation-delay:{1.5 + i * 0.07:.2f}s"'
            out.append(f'<rect class="b"{st} x="{bx:.1f}" y="{base - bh:.1f}" width="{bw:.1f}" height="{bh:.1f}" '
                       f'rx="2" fill="{fill}"><title>{ym}: {n(v)}</title></rect>')
            out.append(f'<text class="m" x="{bx + bw / 2:.1f}" y="{base + 15}">'
                       f'{MESES[int(ym[5:]) - 1][0].upper()}</text>')
            if i == pk and v:
                ps = "" if STATIC else f' style="animation-delay:{2.4:.2f}s"'
                out.append(f'<text class="p t"{ps} x="{bx + bw / 2:.1f}" y="{base - bh - 5:.1f}">{n(v)}</text>')
        out.append(f'<line x1="{PAD + 12}" y1="{base + .5}" x2="{PAD + cw - 12}" y2="{base + .5}" stroke="{LINE}"/>')

    out.append("</svg>")
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(out))
    print(f"wrote {OUT}: {W}x{H}")


if __name__ == "__main__":
    main()
