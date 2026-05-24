"""Fetch match attendance from AFL Tables season pages."""
from __future__ import annotations

import re
import urllib.error
import urllib.request
from datetime import datetime
from functools import lru_cache

# Squiggle / common names -> AFL Tables link text
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

ROW_PAIR_RE = re.compile(
    r'<tr[^>]*>\s*'
    r'<td[^>]*><a href="\.\./teams/[^"]+">([^<]+)</a></td>'
    r'.*?'
    r'(?:[A-Za-z]{3}\s+)?(\d{1,2}-[A-Za-z]{3}-\d{4}).*?'
    r'<b>Att:\s*</b>([\d,]+)'
    r'.*?'
    r'</tr>\s*'
    r'<tr[^>]*>\s*'
    r'<td[^>]*><a href="\.\./teams/[^"]+">([^<]+)</a></td>',
    re.DOTALL | re.IGNORECASE,
)

DATE_FMT = "%d-%b-%Y"


def _norm(name: str) -> str:
    n = (name or "").strip().lower()
    n = TEAM_ALIASES.get(n, n)
    return re.sub(r"\s+", " ", n)


def _pair_key(home: str, away: str) -> tuple[str, str]:
    a, b = sorted([_norm(home), _norm(away)])
    return (a, b)


def _parse_tables_date(raw: str) -> str | None:
    """AFL Tables '20-Apr-2024' -> ISO '2024-04-20'."""
    try:
        return datetime.strptime(raw.strip(), DATE_FMT).date().isoformat()
    except ValueError:
        return None


def _squiggle_date_iso(match_date: str | None) -> str | None:
    if not match_date:
        return None
    raw = match_date.strip()[:10]
    try:
        datetime.strptime(raw, "%Y-%m-%d")
        return raw
    except ValueError:
        return None


@lru_cache(maxsize=32)
def _fetch_season_html(year: int) -> str:
    url = f"https://afltables.com/afl/seas/{year}.html"
    req = urllib.request.Request(url, headers={"User-Agent": "AFL-Tipping/1.0 (quattro backfill)"})
    with urllib.request.urlopen(req, timeout=45) as resp:
        return resp.read().decode("latin-1", "replace")


def load_season_attendance(year: int) -> dict[tuple[tuple[str, str], str], int]:
    """
    Map (sorted team pair, match date ISO) -> crowd.
    Teams that meet twice in a season each get their own dated entry.
    """
    try:
        html = _fetch_season_html(year)
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as ex:
        print(f"  AFL Tables {year}: {ex}", flush=True)
        return {}

    out: dict[tuple[tuple[str, str], str], int] = {}
    for home, date_raw, att_s, away in ROW_PAIR_RE.findall(html):
        iso = _parse_tables_date(date_raw)
        if not iso:
            continue
        try:
            crowd = int(att_s.replace(",", ""))
        except ValueError:
            continue
        key = (_pair_key(home, away), iso)
        out[key] = crowd
    return out


def lookup_attendance(
    cache: dict[int, dict[tuple[tuple[str, str], str], int]],
    year: int,
    team: str,
    opponent: str,
    match_date: str | None = None,
) -> int | None:
    if year not in cache:
        print(f"  AFL Tables attendance {year}...", flush=True)
        cache[year] = load_season_attendance(year)

    season = cache[year]
    pair = _pair_key(team, opponent)
    iso = _squiggle_date_iso(match_date)

    if iso:
        hit = season.get((pair, iso))
        if hit is not None:
            return hit

    # Same pair met once this season — safe fallback
    dated = [(d, c) for (p, d), c in season.items() if p == pair]
    if len(dated) == 1:
        return dated[0][1]

    if iso and dated:
        # Nearest date within the season (timezone / listing quirks)
        target = datetime.strptime(iso, "%Y-%m-%d").date()
        best = min(
            dated,
            key=lambda dc: abs((datetime.strptime(dc[0], "%Y-%m-%d").date() - target).days),
        )
        if abs((datetime.strptime(best[0], "%Y-%m-%d").date() - target).days) <= 2:
            return best[1]

    return None
