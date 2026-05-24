#!/usr/bin/env python3
"""Check one season/round for Quattro Formaggi; merge into data/quattro-formaggi.json."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib.quattro_logic import build_ladder_lookup, find_quattro_events
from lib.squiggle_client import fetch_games, fetch_standings

DATA_FILE = ROOT / "data" / "quattro-formaggi.json"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", type=int, required=True)
    parser.add_argument("--round", type=int, required=True)
    args = parser.parse_args()

    games = fetch_games(args.year)
    all_by_year = {args.year: games}
    ladder_lookup = build_ladder_lookup(all_by_year, fetch_standings)
    found = find_quattro_events(games, ladder_lookup)
    match = [e for e in found if e["season"] == args.year and e["round"] == args.round]

    if not DATA_FILE.exists():
        raise SystemExit("Missing data/quattro-formaggi.json — run scripts/backfill_quattro.py first.")
    data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    existing = data.get("events", [])
    existing = [e for e in existing if not (e["season"] == args.year and e["round"] == args.round)]

    if match:
        existing.append(match[0])
        existing.sort(key=lambda e: (e["season"], e["round"]))
        print(f"Quattro Formaggi YES — round {args.round} {args.year} added.")
    else:
        print(f"No Quattro Formaggi for round {args.round} {args.year}.")

    data["events"] = existing
    data.setdefault("meta", {})["last_weekly_check"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    DATA_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
