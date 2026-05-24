#!/usr/bin/env python3
"""Backfill Quattro Formaggi history from Squiggle API."""
from __future__ import annotations

import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib.afltables_attendance import lookup_attendance
from lib.quattro_logic import QUATTRO_TEAM_IDS, build_ladder_lookup, find_quattro_events
from lib.squiggle_client import fetch_games, fetch_standings

OUTPUT = ROOT / "data" / "quattro-formaggi.json"
DEFAULT_YEARS = 20  # 20-season window (e.g. 2006–2025 when run in 2026)


def _parse_event_date(matches: list) -> date | None:
    dates = []
    for m in matches:
        raw = (m.get("date") or "").strip()
        if not raw:
            continue
        try:
            dates.append(datetime.strptime(raw[:10], "%Y-%m-%d").date())
        except ValueError:
            continue
    return max(dates) if dates else None


def _enrich_gaps(events: list) -> None:
    """Add days_since_previous and days_since_today to each event."""
    today = date.today()
    prev_date: date | None = None
    for ev in events:
        ev_date = _parse_event_date(ev.get("matches") or [])
        ev["event_date"] = ev_date.isoformat() if ev_date else None
        if prev_date and ev_date:
            ev["days_since_previous"] = (ev_date - prev_date).days
        else:
            ev["days_since_previous"] = None
        if ev_date:
            prev_date = ev_date
    if events:
        latest = _parse_event_date(events[-1].get("matches") or [])
        days_since = (today - latest).days if latest else None
        events[-1]["days_since_today"] = days_since


def main():
    current_year = datetime.now(timezone.utc).year
    end_season = current_year if current_year >= 2026 else current_year
    seasons = list(range(end_season - DEFAULT_YEARS, end_season))

    all_games_by_year = {}
    for year in seasons:
        print(f"Fetching Squiggle {year}...", flush=True)
        all_games_by_year[year] = fetch_games(year)

    ladder_lookup = build_ladder_lookup(all_games_by_year, fetch_standings)

    events = []
    for year in seasons:
        found = find_quattro_events(all_games_by_year[year], ladder_lookup)
        events.extend(found)
        print(f"  {year}: {len(found)} quattro round(s)")

    events.sort(key=lambda e: (e["season"], e["round"]))

    att_cache: dict = {}
    for ev in events:
        year = ev["season"]
        for m in ev["matches"]:
            crowd = lookup_attendance(att_cache, year, m["team"], m["opponent"])
            m["attendance"] = crowd

    _enrich_gaps(events)

    payload = {
        "teams": [
            {"id": tid, "name": name, "slug": name.lower().replace(" ", "-")}
            for tid, name in sorted(QUATTRO_TEAM_IDS.items(), key=lambda x: x[1])
        ],
        "people": [
            {"name": "Matt", "team": "Essendon"},
            {"name": "Brett", "team": "Carlton"},
            {"name": "Tim", "team": "Hawthorn"},
            {"name": "Johno", "team": "Geelong"},
        ],
        "events": events,
        "meta": {
            "source": "Squiggle API (api.squiggle.com.au); attendance via AFL Tables (afltables.com)",
            "seasons_scanned": seasons,
            "last_backfill": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
            "attendance_note": "Crowd figures from AFL Tables when a match can be matched.",
        },
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"\nWrote {len(events)} events to {OUTPUT}")


if __name__ == "__main__":
    main()
