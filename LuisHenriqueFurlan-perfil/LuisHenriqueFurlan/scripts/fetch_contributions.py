"""Fetch the public contribution calendar (no token) and write data/contributions.json.

GitHub serves the calendar as an HTML fragment at
https://github.com/users/<username>/contributions (the one the profile page uses).

Usage: python scripts/fetch_contributions.py [username]
       python scripts/fetch_contributions.py --html saved.html   # parse a saved copy
"""
import json
import os
import re
import sys
from collections import OrderedDict
from datetime import date, datetime, timezone

import requests
from bs4 import BeautifulSoup

USERNAME = os.environ.get("GH_USER", "LuisHenriqueFurlan")
OUT = os.path.join("data", "contributions.json")


def fetch_html(user: str) -> str:
    r = requests.get(
        f"https://github.com/users/{user}/contributions",
        headers={"User-Agent": "profile-readme-heatmap", "Accept": "text/html"},
        timeout=30,
    )
    r.raise_for_status()
    return r.text


def parse(html: str):
    soup = BeautifulSoup(html, "html.parser")

    # tooltips carry the exact count: "3 contributions on March 4th." / "No contributions on ..."
    tips = {}
    for tip in soup.select("tool-tip[for]"):
        text = tip.get_text(" ", strip=True)
        m = re.match(r"([\d,]+)\s+contribution", text)
        tips[tip["for"]] = int(m.group(1).replace(",", "")) if m else 0

    days = []
    for cell in soup.select("td.ContributionCalendar-day[data-date]"):
        level = int(cell.get("data-level", 0))
        count = tips.get(cell.get("id"))
        if count is None:  # older markup kept the count on the cell
            count = int(cell.get("data-count", 0) or 0)
        days.append({"date": cell["data-date"], "count": count, "level": level})

    if not days:
        raise SystemExit("no contribution cells found: GitHub may have changed its markup")

    days.sort(key=lambda d: d["date"])
    total = sum(d["count"] for d in days)
    header = soup.select_one("#js-contribution-activity-description")
    if header:
        m = re.search(r"([\d,]+)\s+contribution", header.get_text(" ", strip=True))
        if m:
            total = int(m.group(1).replace(",", ""))
    return days, total


def stats(days):
    longest = run = 0
    for d in days:
        run = run + 1 if d["count"] > 0 else 0
        longest = max(longest, run)

    # current streak: today may still be empty, so start from the last active of today/yesterday
    current = 0
    tail = list(reversed(days))
    if tail and tail[0]["count"] == 0:
        tail = tail[1:]
    for d in tail:
        if d["count"] == 0:
            break
        current += 1

    best = max(days, key=lambda d: d["count"])
    months = OrderedDict()
    for d in days:
        months[d["date"][:7]] = months.get(d["date"][:7], 0) + d["count"]

    return {
        "current_streak": current,
        "longest_streak": longest,
        "best_day": {"date": best["date"], "count": best["count"]},
        "active_days": sum(1 for d in days if d["count"] > 0),
        "monthly": months,
    }


def main(argv):
    if len(argv) >= 2 and argv[0] == "--html":
        html, user = open(argv[1], encoding="utf-8").read(), USERNAME
    else:
        user = argv[0] if argv else USERNAME
        html = fetch_html(user)

    days, total = parse(html)
    data = {
        "username": user,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "range": {"from": days[0]["date"], "to": days[-1]["date"]},
        "total": total,
        **stats(days),
        "days": days,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print(f"wrote {OUT}: {len(days)} days, {total} contributions, streak {data['current_streak']}")


if __name__ == "__main__":
    main(sys.argv[1:])
