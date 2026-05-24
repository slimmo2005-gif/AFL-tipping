"""Fetch match attendance from AFL Tables season pages."""
from __future__ import annotations

import re
import urllib.error
import urllib.request
from functools import lru_cache

# Squiggle / common names -> AFL Tables link text
TEAM_ALIASES = {
    "geelong cats": "geelong",
    "gws": "greater western sydney",
    "gws giants": "greater western sydney",
    "greater western sydney": "greater western sydney",
    "west coast eagles": "west coast",
    "west coast": "west coast",
    "north melbourne": "kangaroos",
    "kangaroos": "kangaroos",
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
    r'<b>Att:\s*</b>([\d,]+)'
    r'.*?'
    r'</tr>\s*'
    r'<tr[^>]*>\s*'
    r'<td[^>]*><a href="\.\./teams/[^"]+">([^<]+)</a></td>',
    re.DOTALL | re.IGNORECASE,
)


def _norm(name: str) -> str:
    n = (name or "").strip().lower()
    n = TEAM_ALIASES.get(n, n)
    return re.sub(r"\s+", " ", n)


def _pair_key(home: str, away: str) -> tuple[str, str]:
    a, b = sorted([_norm(home), _norm(away)])
    return (a, b)


@lru_cache(maxsize=32)
def _fetch_season_html(year: int) -> str:
    url = f"https://afltables.com/afl/seas/{year}.html"
    req = urllib.request.Request(url, headers={"User-Agent": "AFL-Tipping/1.0 (quattro backfill)"})
    with urllib.request.urlopen(req, timeout=45) as resp:
        return resp.read().decode("latin-1", "replace")


def load_season_attendance(year: int) -> dict[tuple[str, str], int]:
    """Map sorted normalized team pair -> crowd for that season."""
    try:
        html = _fetch_season_html(year)
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as ex:
        print(f"  AFL Tables {year}: {ex}", flush=True)
        return {}

    out: dict[tuple[str, str], int] = {}
    for home, att_s, away in ROW_PAIR_RE.findall(html):
        try:
            crowd = int(att_s.replace(",", ""))
        except ValueError:
            continue
        out[_pair_key(home, away)] = crowd
    return out


def lookup_attendance(
    cache: dict[int, dict[tuple[str, str], int]],
    year: int,
    team: str,
    opponent: str,
) -> int | None:
    if year not in cache:
        print(f"  AFL Tables attendance {year}...", flush=True)
        cache[year] = load_season_attendance(year)
    return cache[year].get(_pair_key(team, opponent))
