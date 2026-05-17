from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import sqlite3
import json
import requests
import urllib3
from datetime import datetime
import os
import shutil

# Suppress SSL warnings caused by corporate network certificate interception
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

APP_DIR = os.path.dirname(os.path.abspath(__file__))


def _app_dir_writable():
    try:
        probe = os.path.join(APP_DIR, '.write_probe')
        with open(probe, 'w', encoding='utf-8') as f:
            f.write('ok')
        os.remove(probe)
        return True
    except OSError:
        return False


def _resolve_database_path():
    """Prefer a DB beside the app; fall back to AppData when the folder is read-only."""
    local_db = os.path.join(APP_DIR, 'afl_tipping.db')
    if _app_dir_writable():
        return local_db

    data_dir = os.path.join(
        os.environ.get('LOCALAPPDATA', os.path.expanduser('~')),
        'afl-tipping',
    )
    os.makedirs(data_dir, exist_ok=True)
    user_db = os.path.join(data_dir, 'afl_tipping.db')
    if not os.path.exists(user_db) and os.path.exists(local_db):
        shutil.copy2(local_db, user_db)
    return user_db


DATABASE = _resolve_database_path()

app = Flask(__name__)
app.secret_key = 'afl_tipping_2026_secret'
AFL_COMP_SEASON_ID = 85  # 2026 Toyota AFL Premiership

PARTICIPANTS = ["Matt", "Brett", "Tim", "Johno"]

# All 18 AFL teams (fallback if API is unavailable)
AFL_TEAMS_FALLBACK = [
    "Adelaide Crows", "Brisbane Lions", "Carlton", "Collingwood", "Essendon",
    "Fremantle", "Geelong Cats", "Gold Coast SUNS", "GWS GIANTS", "Hawthorn",
    "Melbourne", "North Melbourne", "Port Adelaide", "Richmond", "St Kilda",
    "Sydney Swans", "West Coast Eagles", "Western Bulldogs"
]


# ── Database helpers ──────────────────────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    db = get_db()
    db.execute('''CREATE TABLE IF NOT EXISTS participants (
        id   INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL
    )''')
    db.execute('''CREATE TABLE IF NOT EXISTS predictions (
        id             INTEGER PRIMARY KEY AUTOINCREMENT,
        participant_id INTEGER NOT NULL,
        position       INTEGER NOT NULL,
        team_name      TEXT NOT NULL,
        UNIQUE(participant_id, position),
        FOREIGN KEY (participant_id) REFERENCES participants(id)
    )''')
    db.execute('''CREATE TABLE IF NOT EXISTS rounds (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        round_number INTEGER UNIQUE NOT NULL,
        fetched_at   TEXT NOT NULL,
        ladder_json  TEXT NOT NULL
    )''')
    db.commit()

    # Migrate old names to "Johno"; remove any stale "John" or "Matt2" entries
    johno_exists = db.execute("SELECT 1 FROM participants WHERE name='Johno'").fetchone()
    if not johno_exists:
        # Prefer renaming Matt2 first, then John if Matt2 is gone
        renamed = db.execute("UPDATE participants SET name='Johno' WHERE name='Matt2'").rowcount
        if not renamed:
            db.execute("UPDATE participants SET name='Johno' WHERE name='John'")
    else:
        # Johno already exists — remove any leftover Matt2 or John rows
        db.execute("DELETE FROM participants WHERE name IN ('Matt2', 'John')")
    for name in PARTICIPANTS:
        db.execute('INSERT OR IGNORE INTO participants (name) VALUES (?)', (name,))
    db.commit()
    db.close()


# ── AFL API helpers ───────────────────────────────────────────────────────────

def fetch_afl_ladder():
    """Fetch current ladder from AFL API. Returns list of {position, team} sorted 1–18."""
    url = f"https://aflapi.afl.com.au/afl/v2/compseasons/{AFL_COMP_SEASON_ID}/ladders"
    resp = requests.get(url, timeout=10, verify=False)
    resp.raise_for_status()
    data = resp.json()
    entries = data['ladders'][0]['entries']
    ladder = [{'position': e['position'], 'team': e['team']['name']} for e in entries]
    return sorted(ladder, key=lambda x: x['position'])


def get_teams_from_api():
    """Return sorted list of all team names from the current ladder."""
    try:
        ladder = fetch_afl_ladder()
        return sorted(t['team'] for t in ladder)
    except Exception:
        return AFL_TEAMS_FALLBACK


# ── Scoring ───────────────────────────────────────────────────────────────────

def calculate_score(predictions, ladder):
    """
    predictions : list of (position, team_name) for positions 1–10
    ladder      : list of {position, team} for all 18 teams
    Returns     : (total_score, details_list)
    """
    # Map team → actual ladder position
    ladder_map = {e['team']: e['position'] for e in ladder}

    total = 0
    details = []

    for pred_pos, team in sorted(predictions, key=lambda x: x[0]):
        actual_pos = ladder_map.get(team)

        if actual_pos is None or actual_pos > 10:
            points = 0
            reason = f"Outside top 10 (actual #{actual_pos})" if actual_pos else "Unknown team"
        elif pred_pos == actual_pos:
            points = 5 if pred_pos == 1 else 2
            reason = "🏆 #1 spot!" if pred_pos == 1 else f"✓ Exact – #{pred_pos}"
        else:
            points = 1
            reason = f"In top 10 (actual #{actual_pos})"

        total += points
        details.append({
            'position': pred_pos,
            'team': team,
            'actual': actual_pos,
            'points': points,
            'reason': reason,
        })

    return total, details


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    db = get_db()
    participants = db.execute('SELECT * FROM participants ORDER BY name').fetchall()
    rounds = db.execute('SELECT * FROM rounds ORDER BY round_number').fetchall()

    # Check which participants have predictions set
    pred_status = {}
    for p in participants:
        count = db.execute(
            'SELECT COUNT(*) as c FROM predictions WHERE participant_id=?', (p['id'],)
        ).fetchone()['c']
        pred_status[p['id']] = count

    db.close()
    return render_template('index.html', participants=participants,
                           rounds=rounds, pred_status=pred_status)


@app.route('/setup', methods=['GET', 'POST'])
def setup():
    db = get_db()
    participants = db.execute('SELECT * FROM participants ORDER BY id').fetchall()
    teams = get_teams_from_api()

    if request.method == 'POST':
        errors = []
        for p in participants:
            picks = []
            for pos in range(1, 11):
                team = request.form.get(f'p{p["id"]}_pos{pos}', '').strip()
                if not team:
                    errors.append(f"{p['name']}: position {pos} is empty.")
                else:
                    picks.append((pos, team))

            # Check for duplicate teams within a participant's picks
            teams_picked = [t for _, t in picks]
            if len(teams_picked) != len(set(teams_picked)):
                errors.append(f"{p['name']}: duplicate team selected.")

        if errors:
            for e in errors:
                flash(e, 'danger')
            # Re-render with existing values
            existing = {}
            for p in participants:
                rows = db.execute(
                    'SELECT position, team_name FROM predictions WHERE participant_id=? ORDER BY position',
                    (p['id'],)
                ).fetchall()
                existing[p['id']] = {r['position']: r['team_name'] for r in rows}
            db.close()
            return render_template('setup.html', participants=participants,
                                   teams=teams, existing=existing)

        # Save predictions
        for p in participants:
            db.execute('DELETE FROM predictions WHERE participant_id=?', (p['id'],))
            for pos in range(1, 11):
                team = request.form.get(f'p{p["id"]}_pos{pos}', '').strip()
                db.execute(
                    'INSERT INTO predictions (participant_id, position, team_name) VALUES (?,?,?)',
                    (p['id'], pos, team)
                )
        db.commit()
        db.close()
        flash('Predictions saved successfully!', 'success')
        return redirect(url_for('index'))

    # GET – load existing picks
    existing = {}
    for p in participants:
        rows = db.execute(
            'SELECT position, team_name FROM predictions WHERE participant_id=? ORDER BY position',
            (p['id'],)
        ).fetchall()
        existing[p['id']] = {r['position']: r['team_name'] for r in rows}

    db.close()
    return render_template('setup.html', participants=participants,
                           teams=teams, existing=existing)


@app.route('/update_ladder', methods=['POST'])
def update_ladder():
    round_number = request.form.get('round_number', '').strip()
    if not round_number or not round_number.isdigit():
        flash('Please enter a valid round number.', 'danger')
        return redirect(url_for('index'))

    round_number = int(round_number)

    try:
        ladder = fetch_afl_ladder()
    except Exception as ex:
        flash(f'Failed to fetch ladder from AFL API: {ex}', 'danger')
        return redirect(url_for('index'))

    db = get_db()
    db.execute(
        'INSERT OR REPLACE INTO rounds (round_number, fetched_at, ladder_json) VALUES (?,?,?)',
        (round_number, datetime.now().strftime('%Y-%m-%d %H:%M'), json.dumps(ladder))
    )
    db.commit()
    db.close()

    flash(f'Round {round_number} ladder saved ({len(ladder)} teams).', 'success')
    return redirect(url_for('leaderboard', round_id=round_number))


@app.route('/leaderboard')
@app.route('/leaderboard/<int:round_id>')
def leaderboard(round_id=None):
    db = get_db()
    participants = db.execute('SELECT * FROM participants ORDER BY id').fetchall()
    rounds = db.execute('SELECT * FROM rounds ORDER BY round_number').fetchall()

    if not rounds:
        db.close()
        return render_template('leaderboard.html', participants=participants,
                               rounds=[], round_data=None, selected_round=None,
                               season_table=None)

    if round_id is None:
        round_id = rounds[-1]['round_number']

    selected_round = db.execute(
        'SELECT * FROM rounds WHERE round_number=?', (round_id,)
    ).fetchone()

    round_data = None
    if selected_round:
        ladder = json.loads(selected_round['ladder_json'])
        round_data = {'round': selected_round, 'participants': []}

        for p in participants:
            preds = db.execute(
                'SELECT position, team_name FROM predictions WHERE participant_id=? ORDER BY position',
                (p['id'],)
            ).fetchall()
            pred_list = [(r['position'], r['team_name']) for r in preds]
            total, details = calculate_score(pred_list, ladder)
            round_data['participants'].append({
                'name': p['name'],
                'total': total,
                'details': details,
            })

        # Sort by total desc for display
        round_data['participants'].sort(key=lambda x: x['total'], reverse=True)

    # ── Season history table ──────────────────────────────────────────────────
    season_table = {'rounds': [], 'rows': []}
    if rounds:
        season_table['rounds'] = [r['round_number'] for r in rounds]
        for p in participants:
            preds = db.execute(
                'SELECT position, team_name FROM predictions WHERE participant_id=? ORDER BY position',
                (p['id'],)
            ).fetchall()
            pred_list = [(r['position'], r['team_name']) for r in preds]

            row = {'name': p['name'], 'scores': [], 'total': 0}
            for rnd in rounds:
                ladder = json.loads(rnd['ladder_json'])
                score, _ = calculate_score(pred_list, ladder)
                row['scores'].append(score)
                row['total'] = max(row['total'], score)  # show latest (highest) cumulative

            # Re-calculate total as the latest round's score
            if rounds:
                latest_ladder = json.loads(rounds[-1]['ladder_json'])
                row['total'], _ = calculate_score(pred_list, latest_ladder)

            season_table['rows'].append(row)

        season_table['rows'].sort(key=lambda x: x['total'], reverse=True)

    db.close()
    return render_template('leaderboard.html', participants=participants,
                           rounds=rounds, round_data=round_data,
                           selected_round=round_id, season_table=season_table)


@app.route('/compare')
def compare():
    db = get_db()
    participants = db.execute('SELECT * FROM participants ORDER BY id').fetchall()

    # Load every participant's predictions keyed by position
    all_preds = {}  # participant_id → {position: team_name}
    for p in participants:
        rows = db.execute(
            'SELECT position, team_name FROM predictions WHERE participant_id=? ORDER BY position',
            (p['id'],)
        ).fetchall()
        all_preds[p['id']] = {r['position']: r['team_name'] for r in rows}

    db.close()

    has_predictions = any(len(v) == 10 for v in all_preds.values())

    # Build a flat set of all teams picked by each participant (for cross-person lookup)
    # picked_teams[participant_id] = set of team names
    picked_teams = {p['id']: set(all_preds[p['id']].values()) for p in participants}

    # Build the 10-row matrix
    # Each row: position + list of cells {name, team, highlight, shared_count}
    #   highlight: 'same-spot'  → 2+ people share this exact team at this exact position
    #              'diff-spot'  → team appears in another person's predictions (any position)
    #              ''           → unique across all predictions
    matrix = []
    for pos in range(1, 11):
        # Teams picked at this exact position by each participant
        teams_at_pos = {}
        for p in participants:
            team = all_preds[p['id']].get(pos, '')
            teams_at_pos[p['id']] = team

        # Count how many participants have the same team at this exact position
        pos_team_counts = {}
        for team in teams_at_pos.values():
            if team:
                pos_team_counts[team] = pos_team_counts.get(team, 0) + 1

        cells = []
        for p in participants:
            team = teams_at_pos[p['id']]
            if not team:
                cells.append({'name': p['name'], 'team': '', 'highlight': 'empty', 'shared_count': 0})
                continue

            same_spot_count = pos_team_counts.get(team, 1)

            if same_spot_count >= 2:
                highlight = 'same-spot'
                # Count how many others share this same-spot pick
                shared_count = same_spot_count
            else:
                # Check if any other participant picked this team at a different position
                picked_by_others = sum(
                    1 for other in participants
                    if other['id'] != p['id'] and team in picked_teams[other['id']]
                )
                if picked_by_others > 0:
                    highlight = 'diff-spot'
                    shared_count = picked_by_others + 1
                else:
                    highlight = ''
                    shared_count = 1

            cells.append({
                'name': p['name'],
                'team': team,
                'highlight': highlight,
                'shared_count': shared_count,
            })

        matrix.append({'position': pos, 'cells': cells})

    return render_template('compare.html', participants=participants,
                           matrix=matrix, has_predictions=has_predictions)


@app.route('/api/teams')
def api_teams():
    return jsonify(get_teams_from_api())


if __name__ == '__main__':
    init_db()
    print("\n  AFL Tipping Leaderboard")
    print(f"  Database: {DATABASE}")
    print("  Open http://127.0.0.1:5000 in your browser\n")
    app.run(debug=True)
