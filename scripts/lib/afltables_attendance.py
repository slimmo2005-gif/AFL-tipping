"""Fetch match facts (round, attendance) from AFL Tables season pages."""
from __future__ import annotations

import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache

from lib.match_key import match_key_from_afl_row

ROW_PAIR_RE = re.compile(
    r'<tr[^>]*>\s*'
    r'<td[^>]*><a href="\.\./teams/[^"]+">([^<]+)</a></td>'
    r'.*?'
    r'(?:[A-Za-z]{3}\s+)?(\d{1,2}-[A-Za-z]{3}-\d{4}).*?'
    r'<b>Att:\s*</b>([\d,]+)'
    r'.*?'
    r'<b>Venue:</b>\s*<a href="[^"]+">([^<]+)</a>'
    r'.*?'
    r'</tr>\s*'
    r'<tr[^>]*>\s*'
    r'<td[^>]*><a href="\.\./teams/[^"]+">([^<]+)</a></td>',
    re.DOTALL | re.IGNORECASE,
)

DATE_FMT = "%d-%b-%Y"
ROUND_SPLIT_RE = re.compile(r"Round (\d+)</td>")


@dataclass(frozen=True)
class AflMatchRecord:
    round_num: int
    attendance: int
    home_team: str
    away_team: str
    date_iso: str
    venue: str


def _parse_tables_date(raw: str) -> str | None:
    try:
        return datetime.strptime(raw.strip(), DATE_FMT).date().isoformat()
    except ValueError:
        return None


@lru_cache(maxsize=32)
def _fetch_season_html(year: int) -> str:
    url = f"https://afltables.com/afl/seas/{year}.html"
    req = urllib.request.Request(url, headers={"User-Agent": "AFL-Tipping/1.0 (quattro backfill)"})
    with urllib.request.urlopen(req, timeout=45) as resp:
        return resp.read().decode("latin-1", "replace")


def load_season_matches(year: int) -> dict[tuple[str, str, str, str], AflMatchRecord]:
    """
    Index AFL Tables matches by (date, home, away, venue).
    Never relies on row order — each match is parsed in its round section.
    """
    try:
        html = _fetch_season_html(year)
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as ex:
        print(f"  AFL Tables {year}: {ex}", flush=True)
        return {}

    out: dict[tuple[str, str, str, str], AflMatchRecord] = {}
    chunks = ROUND_SPLIT_RE.split(html)

    # chunks: [preamble, round_num, body, round_num, body, ...]
    for i in range(1, len(chunks), 2):
        if i + 1 >= len(chunks):
            break
        try:
            round_num = int(chunks[i])
        except ValueError:
            continue
        body = chunks[i + 1]

        for home, date_raw, att_s, venue, away in ROW_PAIR_RE.findall(body):
            iso = _parse_tables_date(date_raw)
            if not iso:
                continue
            try:
                crowd = int(att_s.replace(",", ""))
            except ValueError:
                continue

            key = match_key_from_afl_row(iso, home, away, venue)
            out[key] = AflMatchRecord(
                round_num=round_num,
                attendance=crowd,
                home_team=home,
                away_team=away,
                date_iso=iso,
                venue=venue.strip(),
            )

    return out


def lookup_match(
    cache: dict[int, dict[tuple[str, str, str, str], AflMatchRecord]],
    year: int,
    key: tuple[str, str, str, str],
) -> AflMatchRecord | None:
    if year not in cache:
        print(f"  AFL Tables matches {year}...", flush=True)
        cache[year] = load_season_matches(year)
    return cache[year].get(key)


# Backwards-compatible helper
def lookup_attendance(
    cache: dict[int, dict[tuple[str, str, str, str], AflMatchRecord]],
    year: int,
    key: tuple[str, str, str, str],
) -> int | None:
    rec = lookup_match(cache, year, key)
    return rec.attendance if rec else None
