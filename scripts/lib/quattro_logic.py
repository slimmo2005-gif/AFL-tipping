"""Quattro Formaggi: Essendon, Hawthorn, Carlton, Geelong all play and win same round."""
from collections import defaultdict

QUATTRO_TEAM_IDS = {
    5: "Essendon",
    10: "Hawthorn",
    3: "Carlton",
    7: "Geelong",
}


def _game_for_team(game: dict, team_id: int) -> dict | None:
    if game.get("complete") != 100:
        return None
    if game["hteamid"] == team_id:
        return {
            "team": game["hteam"],
            "team_id": team_id,
            "opponent": game["ateam"],
            "team_score": game["hscore"],
            "opponent_score": game["ascore"],
            "venue": game.get("venue") or "",
            "won": game["winnerteamid"] == team_id,
            "home": True,
            "game_id": game["id"],
            "date": game.get("date", ""),
        }
    if game["ateamid"] == team_id:
        return {
            "team": game["ateam"],
            "team_id": team_id,
            "opponent": game["hteam"],
            "team_score": game["ascore"],
            "opponent_score": game["hscore"],
            "venue": game.get("venue") or "",
            "won": game["winnerteamid"] == team_id,
            "home": False,
            "game_id": game["id"],
            "date": game.get("date", ""),
        }
    return None


def find_quattro_events(games: list, ladder_lookup) -> list:
    """
    ladder_lookup(season, round_num, team_id) -> ladder rank before round, or None.
    Returns list of event dicts.
    """
    completed = [g for g in games if g.get("complete") == 100]
    by_round = defaultdict(list)
    for g in completed:
        key = (g["year"], g["round"], g.get("roundname") or f"Round {g['round']}")
        by_round[key].append(g)

    events = []
    for (season, round_num, round_label), round_games in sorted(by_round.items()):
        match_rows = []
        for team_id in QUATTRO_TEAM_IDS:
            team_games = [g for g in round_games if g["hteamid"] == team_id or g["ateamid"] == team_id]
            if len(team_games) != 1:
                match_rows = None
                break
            row = _game_for_team(team_games[0], team_id)
            if not row or not row["won"]:
                match_rows = None
                break
            row["ladder_position_before"] = ladder_lookup(season, round_num, team_id)
            match_rows.append(row)

        if match_rows and len(match_rows) == 4:
            is_final = max((g.get("is_final") or 0) for g in round_games)
            events.append(
                {
                    "season": season,
                    "round": round_num,
                    "round_label": round_label,
                    "round_type": "finals" if is_final else "home_away",
                    "is_final": bool(is_final),
                    "matches": sorted(match_rows, key=lambda m: QUATTRO_TEAM_IDS[m["team_id"]]),
                }
            )
    return events


def build_ladder_lookup(all_games_by_year: dict, standings_fetch) -> callable:
    """Build ladder_lookup(season, round_num, team_id) using Squiggle standings."""

    def final_round_for_year(year: int) -> int:
        games = all_games_by_year.get(year, [])
        home_away = [g["round"] for g in games if not g.get("is_final")]
        return max(home_away) if home_away else 23

    cache = {}

    def ladder_lookup(season: int, round_num: int, team_id: int) -> int | None:
        if round_num <= 3:
            prev = season - 1
            snap_round = final_round_for_year(prev)
            key = (prev, snap_round, team_id)
        else:
            key = (season, round_num - 1, team_id)

        if key not in cache:
            yr, rnd, _ = key
            try:
                rows = standings_fetch(yr, rnd)
                cache[key] = {r["id"]: r["rank"] for r in rows}
            except Exception:
                cache[key] = {}
        return cache[key].get(team_id)

    return ladder_lookup
