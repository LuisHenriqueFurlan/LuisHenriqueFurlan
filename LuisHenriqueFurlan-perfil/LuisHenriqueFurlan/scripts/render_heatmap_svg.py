"""Render data/contributions.json as an animated 53x7 heatmap (contrib-heatmap.svg).

Boxes slide in diagonally once on load, then freeze (CSS keyframes, no loop).
Without data (first commit, before the workflow has run) it draws an empty calendar.

Usage: python scripts/render_heatmap_svg.py      (STATIC=1 for a frozen frame)
"""
import json
import os
from datetime import date, timedelta

DATA = os.path.join("data", "contributions.json")
OUT = os.environ.get("OUT", "contrib-heatmap.svg")
STATIC = os.environ.get("STATIC") == "1"

PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]
#          none -> brightest (level 5 is a neon top end for the very best days)

W = 860
BAR_H = 28
PAD_X = 22
LEFT = 34          # room for weekday labels
TOP = BAR_H + 36   # room for month labels
CELL, GAP = 12, 3
STEP = CELL + GAP

BG, BAR, MUTED, TEXT, KEY = "#0d1117", "#161b22", "#8b949e", "#c9d1d9", "#7ee787"
FONT = "ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace"
MONTHS = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]


def load():
    try:
        with open(DATA, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def empty_days():
    today = date.today()
    start = today - timedelta(days=364 + (today.weekday() + 1) % 7)
    return [{"date": (start + timedelta(i)).isoformat(), "count": 0, "level": 0}
            for i in range((today - start).days + 1)]


def fmt(n: int) -> str:
    return f"{n:,}".replace(",", ".")


def main():
    data = load()
    days = data["days"] if data else empty_days()

    # level 5: the top days of the year (top ~3% of active days, at least level 4)
    active = sorted((d["count"] for d in days if d["count"] > 0), reverse=True)
    neon = active[max(0, int(len(active) * 0.03) - 1)] if len(active) >= 20 else None

    first = date.fromisoformat(days[0]["date"])
    offset = (first.weekday() + 1) % 7  # GitHub weeks start on Sunday
    cells, month_labels, last_month = [], [], None
    for i, d in enumerate(days):
        k = i + offset
        week, dow = divmod(k, 7)
        level = d.get("level", 0)
        if neon is not None and level >= 4 and d["count"] >= neon:
            level = 5
        cells.append((week, dow, level, d))
        dt = date.fromisoformat(d["date"])
        if dow == 0 and dt.month != last_month:  # label the first week that starts in a month
            month_labels.append((week, MONTHS[dt.month - 1]))
            last_month = dt.month

    weeks = cells[-1][0] + 1
    grid_w = weeks * STEP - GAP
    x0 = PAD_X + LEFT + (W - 2 * PAD_X - LEFT - grid_w) / 2
    grid_bottom = TOP + 7 * STEP - GAP
    H = grid_bottom + 64

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
        f'role="img" aria-label="Contribution heatmap">',
        "<style>",
        f"text{{font-family:{FONT};font-size:10px;fill:{MUTED}}}",
        ".s{font-size:11.5px;fill:" + TEXT + "}",
        ".k{fill:" + KEY + ";font-weight:700}",
    ]
    if not STATIC:
        out += [
            ".c{opacity:0;transform-box:fill-box;transform-origin:center;"
            "animation:drop .45s cubic-bezier(.2,.8,.3,1) forwards}",
            "@keyframes drop{from{opacity:0;transform:translateY(-10px) scale(.6)}"
            "to{opacity:1;transform:none}}",
            ".f{opacity:0;animation:fade .6s ease-out forwards}",
            "@keyframes fade{to{opacity:1}}",
        ]
    out.append("</style>")
    out.append(f'<rect width="{W}" height="{H}" rx="10" fill="{BG}"/>')
    out.append(f'<path d="M0 10a10 10 0 0 1 10-10h{W - 20}a10 10 0 0 1 10 10v{BAR_H - 10}H0z" fill="{BAR}"/>')
    for i, col in enumerate(("#ff5f56", "#ffbd2e", "#27c93f")):
        out.append(f'<circle cx="{16 + i * 16}" cy="{BAR_H / 2}" r="5" fill="{col}"/>')
    out.append(f'<text x="{W / 2}" y="{BAR_H / 2 + 3.5}" text-anchor="middle">contributions.sh</text>')

    for week, name in month_labels:
        if week <= weeks - 2:
            out.append(f'<text x="{x0 + week * STEP:.1f}" y="{TOP - 8}">{name}</text>')
    for dow, name in ((1, "seg"), (3, "qua"), (5, "sex")):
        out.append(f'<text x="{x0 - 8:.1f}" y="{TOP + dow * STEP + 9}" text-anchor="end">{name}</text>')

    for week, dow, level, d in cells:
        x, y = x0 + week * STEP, TOP + dow * STEP
        delay = "" if STATIC else f' style="animation-delay:{0.2 + (week + dow) * 0.022:.3f}s"'
        label = "contribuição" if d["count"] == 1 else "contribuições"
        out.append(
            f'<rect class="c"{delay} x="{x:.1f}" y="{y}" width="{CELL}" height="{CELL}" rx="2.5" '
            f'fill="{PALETTE[level]}"><title>{d["date"]}: {d["count"]} {label}</title></rect>'
        )

    end = 0.2 + (weeks + 6) * 0.022
    fstyle = "" if STATIC else f' style="animation-delay:{end:.2f}s"'
    fy = grid_bottom + 34
    if data:
        stats = (
            f'<tspan class="k">{fmt(data["total"])}</tspan> contribuições no último ano'
            f' · sequência <tspan class="k">{data["current_streak"]}d</tspan>'
            f' · recorde <tspan class="k">{data["longest_streak"]}d</tspan>'
            f' · melhor dia <tspan class="k">{data["best_day"]["count"]}</tspan>'
        )
    else:
        stats = "aguardando a primeira atualização do GitHub Actions…"
    out.append(f'<g class="f"{fstyle}><text class="s" x="{PAD_X}" y="{fy}">{stats}</text>')

    # Less -> More legend, right-aligned
    lx = W - PAD_X - len(PALETTE) * STEP - 40
    out.append(f'<text x="{lx - 6}" y="{fy - 1}" text-anchor="end">menos</text>')
    for i, c in enumerate(PALETTE):
        out.append(f'<rect x="{lx + i * STEP}" y="{fy - 11}" width="{CELL}" height="{CELL}" rx="2.5" fill="{c}"/>')
    out.append(f'<text x="{lx + len(PALETTE) * STEP + 4}" y="{fy - 1}">mais</text></g>')

    out.append("</svg>")
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(out))
    print(f"wrote {OUT}: {weeks} weeks, {W}x{H}")


if __name__ == "__main__":
    main()
