"""Minimal Squiggle API client (https://api.squiggle.com.au/)."""
import json
import time
import urllib.error
import urllib.request

USER_AGENT = "AFL-Tipping-Quattro/1.0 (github.com/slimmo2005-gif/AFL-tipping)"
BASE = "https://api.squiggle.com.au/"


def fetch(query: str, retries: int = 3) -> dict:
    url = f"{BASE}?{query};format=json"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    last_err = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=90) as resp:
                return json.load(resp)
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as ex:
            last_err = ex
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"Squiggle request failed: {url}") from last_err


def fetch_games(year: int) -> list:
    data = fetch(f"q=games;year={year}")
    return data.get("games") or []


def fetch_standings(year: int, round_num: int) -> list:
    data = fetch(f"q=standings;year={year};round={round_num}")
    return data.get("standings") or []
