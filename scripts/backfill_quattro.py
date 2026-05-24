#!/usr/bin/env python3
"""Backfill Quattro Formaggi history from Squiggle API."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib.quattro_logic import QUATTRO_TEAM_IDS, build_ladder_lookup, find_quattro_events
from lib.squiggle_client import fetch_games, fetch_standings

OUTPUT = ROOT / "data" / "quattro-formaggi.json"
DEFAULT_YEARS = 5  # most recent 5 completed seasons window


def main():
    current_year = datetime.now(timezone.utc).year
    # AFL season labelled by start year; use Y-1 .. Y-5 for a 5-season window
    end_season = current_year if current_year >= 2026 else current_year
    seasons = list(range(end_season - DEFAULT_YEARS, end_season))

    all_games_by_year = {}
    for year in seasons:
        print(f"Fetching {year}...", flush=True)
        all_games_by_year[year] = fetch_games(year)

    ladder_lookup = build_ladder_lookup(all_games_by_year, fetch_standings)

    events = []
    for year in seasons:
        found = find_quattro_events(all_games_by_year[year], ladder_lookup)
        events.extend(found)
        print(f"  {year}: {len(found)} quattro round(s)")

    events.sort(key=lambda e: (e["season"], e["round"]))

    payload = {
        "teams": [
            {"id": tid, "name": name, "slug": name.lower().replace(" ", "-")}
            for tid, name in sorted(QUATTRO_TEAM_IDS.items(), key=lambda x: x[1])
        ],
        "people": [
            {"name": "Matt", "team": "Essendon"},
            {"name": "Brett", "team": "Hawthorn"},
            {"name": "Tim", "team": "Carlton"},
            {"name": "Johno", "team": "Geelong"},
        ],
        "events": events,
        "meta": {
            "source": "Squiggle API (api.squiggle.com.au)",
            "seasons_scanned": seasons,
            "last_backfill": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
            "attendance_note": "Attendance not available from Squiggle; venue shown when known.",
        },
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"\nWrote {len(events)} events to {OUTPUT}")


if __name__ == "__main__":
    main()
