"""Fetch the public contribution calendar (no token) and write data/contributions.json.

GitHub serves the calendar as an HTML fragment at
https://github.com/users/<username>/contributions (the one the profile page uses).
Standard library only, so the daily workflow needs no pip install.

Usage: python scripts/fetch_contributions.py [username]
       python scripts/fetch_contributions.py --html saved.html   # parse a saved copy
"""
import json
import os
import re
import sys
import urllib.request
from collections import OrderedDict
from datetime import datetime, timezone
from html.parser import HTMLParser

USERNAME = os.environ.get("GH_USER", "LuisHenriqueFurlan")
OUT = os.path.join("data", "contributions.json")


def fetch_html(user: str) -> str:
    req = urllib.request.Request(
        f"https://github.com/users/{user}/contributions",
        headers={"User-Agent": "profile-readme-heatmap", "Accept": "text/html"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8")


class Calendar(HTMLParser):
    """Collects <td class="ContributionCalendar-day" data-date data-level id> cells and
    the <tool-tip for="id">N contributions on ...</tool-tip> that carry exact counts."""

    def __init__(self):
        super().__init__()
        self.cells, self.tips, self.header = [], {}, ""
        self._tip_for = None
        self._in_header = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "td" and "ContributionCalendar-day" in (a.get("class") or "") and a.get("data-date"):
            self.cells.append(a)
        elif tag == "tool-tip" and a.get("for"):
            self._tip_for, self.tips[a["for"]] = a["for"], ""
        elif tag == "h2" and a.get("id") == "js-contribution-activity-description":
            self._in_header = True

    def handle_endtag(self, tag):
        if tag == "tool-tip":
            self._tip_for = None
        elif tag == "h2":
            self._in_header = False

    def handle_data(self, data):
        if self._tip_for:
            self.tips[self._tip_for] += data
        elif self._in_header:
            self.header += data


def parse(html: str):
    p = Calendar()
    p.feed(html)
    days = []
    for c in p.cells:
        tip = " ".join(p.tips.get(c.get("id"), "").split())
        m = re.match(r"([\d,]+)\s+contribution", tip)
        count = int(m.group(1).replace(",", "")) if m else int(c.get("data-count", 0) or 0)
        days.append({"date": c["data-date"], "count": count, "level": int(c.get("data-level", 0))})
    if not days:
        raise SystemExit("no contribution cells found: GitHub may have changed its markup")
    days.sort(key=lambda d: d["date"])

    total = sum(d["count"] for d in days)
    m = re.search(r"([\d,]+)\s+contribution", " ".join(p.header.split()))
    if m:
        total = int(m.group(1).replace(",", ""))
    return days, total


def streaks(days):
    """Longest run and current run (today may still be empty), with start/end dates."""
    longest = {"days": 0, "start": None, "end": None}
    run_start, run = None, 0
    for d in days:
        if d["count"] > 0:
            run_start = d["date"] if run == 0 else run_start
            run += 1
            if run > longest["days"]:
                longest = {"days": run, "start": run_start, "end": d["date"]}
        else:
            run = 0

    tail = list(reversed(days))
    if tail and tail[0]["count"] == 0:
        tail = tail[1:]
    current = {"days": 0, "start": None, "end": None}
    for d in tail:
        if d["count"] == 0:
            break
        current["days"] += 1
        current["start"] = d["date"]
        current["end"] = current["end"] or d["date"]
    return current, longest


def main(argv):
    if len(argv) >= 2 and argv[0] == "--html":
        html, user = open(argv[1], encoding="utf-8").read(), USERNAME
    else:
        user = argv[0] if argv else USERNAME
        html = fetch_html(user)

    days, total = parse(html)
    current, longest = streaks(days)
    best = max(days, key=lambda d: d["count"])
    active = sum(1 for d in days if d["count"] > 0)
    months = OrderedDict()
    for d in days:
        months[d["date"][:7]] = months.get(d["date"][:7], 0) + d["count"]

    data = {
        "username": user,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "range": {"from": days[0]["date"], "to": days[-1]["date"]},
        "total": total,
        "current_streak": current,
        "longest_streak": longest,
        "best_day": {"date": best["date"], "count": best["count"]},
        "active_days": active,
        "total_days": len(days),
        "avg_per_active_day": round(sum(d["count"] for d in days) / active, 1) if active else 0,
        "monthly": months,
        "days": days,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print(f"wrote {OUT}: {len(days)} days, {total} contributions, streak {current['days']}")


if __name__ == "__main__":
    main(sys.argv[1:])
