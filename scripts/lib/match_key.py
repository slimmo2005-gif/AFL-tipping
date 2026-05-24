"""Canonical match keys for joining Squiggle and AFL Tables data."""
from __future__ import annotations

import re
from datetime import datetime

TEAM_ALIASES = {
    "geelong cats": "geelong",
    "gws": "greater western sydney",
    "gws giants": "greater western sydney",
    "greater western sydney": "greater western sydney",
    "west coast eagles": "west coast",
    "west coast": "west coast",
    "north melbourne": "north melbourne",
    "kangaroos": "north melbourne",
    "port adelaide": "port adelaide",
    "brisbane lions": "brisbane lions",
    "st kilda": "st kilda",
    "gold coast": "gold coast",
    "gold coast suns": "gold coast",
}

VENUE_ALIASES = {
    "marvel stadium": "docklands",
    "docklands": "docklands",
    "etihad stadium": "docklands",
    "gabba": "gabba",
    "the gabba": "gabba",
    "brisbane cricket ground": "gabba",
    "m.c.g.": "mcg",
    "mcg": "mcg",
    "melbourne cricket ground": "mcg",
    "adelaide oval": "adelaide oval",
    "perth stadium": "perth stadium",
    "optus stadium": "perth stadium",
    "gmhba stadium": "kardinia park",
    "kardinia park": "kardinia park",
    "skilled stadium": "kardinia park",
    "s.c.g.": "scg",
    "scg": "scg",
    "sydney cricket ground": "scg",
    "carrara": "carrara",
    "metricon stadium": "carrara",
    "people first stadium": "carrara",
    "tio trajectory": "marrara oval",
    "marrara oval": "marrara oval",
    "tio stadium": "marrara oval",
    "bellerive oval": "bellerive oval",
    "york park": "bellerive oval",
    "university of tasmania stadium": "bellerive oval",
    "manuka oval": "manuka oval",
    "giants stadium": "sydney showground",
    "sydney showground": "sydney showground",
    "engie stadium": "sydney showground",
}


def norm_team(name: str) -> str:
    n = (name or "").strip().lower()
    n = TEAM_ALIASES.get(n, n)
    return re.sub(r"\s+", " ", n)


def norm_venue(venue: str) -> str:
    v = (venue or "").strip().lower()
    v = VENUE_ALIASES.get(v, v)
    return re.sub(r"\s+", " ", v)


def date_iso_from_squiggle(date_str: str | None) -> str | None:
    if not date_str:
        return None
    raw = date_str.strip()[:10]
    try:
        datetime.strptime(raw, "%Y-%m-%d")
        return raw
    except ValueError:
        return None


def match_key(date_iso: str, home_team: str, away_team: str, venue: str) -> tuple[str, str, str, str]:
    """Unique match id: date, home, away, venue (all normalized)."""
    return (
        date_iso,
        norm_team(home_team),
        norm_team(away_team),
        norm_venue(venue),
    )


def match_key_from_squiggle(game: dict) -> tuple[str, str, str, str] | None:
    iso = date_iso_from_squiggle(game.get("date"))
    if not iso:
        return None
    return match_key(iso, game["hteam"], game["ateam"], game.get("venue") or "")


def match_key_from_afl_row(
    date_iso: str, home_team: str, away_team: str, venue: str
) -> tuple[str, str, str, str]:
    return match_key(date_iso, home_team, away_team, venue)
