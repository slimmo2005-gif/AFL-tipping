#!/usr/bin/env python3
"""Backfill Quattro Formaggi history from Squiggle API."""
from __future__ import annotations

import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib.afltables_attendance import load_season_matches
from lib.quattro_logic import (
    QUATTRO_TEAM_IDS,
    build_ladder_lookup,
    enrich_games_with_afl,
    find_quattro_events,
)
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
    afl_by_year = {}
    for year in seasons:
        print(f"Fetching Squiggle {year}...", flush=True)
        all_games_by_year[year] = fetch_games(year)
        print(f"  AFL Tables matches {year}...", flush=True)
        afl_by_year[year] = load_season_matches(year)

    ladder_lookup = build_ladder_lookup(all_games_by_year, fetch_standings)

    events = []
    for year in seasons:
        games = enrich_games_with_afl(all_games_by_year[year], afl_by_year[year])
        found = find_quattro_events(games, ladder_lookup)
        events.extend(found)
        print(f"  {year}: {len(found)} quattro round(s)")

    events.sort(key=lambda e: (e["season"], e["round"]))

    _enrich_gaps(events)

    missing_afl = sum(
        1 for ev in events for m in ev["matches"] if m.get("attendance") is None
    )

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
            "round_note": "Round numbers from Squiggle (matches official AFL fixture rounds).",
            "attendance_note": "Crowd joined by date, home team, away team and venue (never row order).",
            "unmatched_attendance": missing_afl,
        },
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"\nWrote {len(events)} events to {OUTPUT}")
    if missing_afl:
        print(f"  Warning: {missing_afl} match(es) missing AFL Tables attendance", flush=True)


if __name__ == "__main__":
    main()
