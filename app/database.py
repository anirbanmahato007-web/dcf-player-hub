import sqlite3
import os
import csv
import io
from datetime import datetime

DATABASE_URL = os.environ.get("DATABASE_URL")
DATA_DIR = os.environ.get("DATA_DIR", os.path.dirname(__file__))
os.makedirs(DATA_DIR, exist_ok=True)
DB_PATH = os.path.join(DATA_DIR, "dcf_player_hub.db")

def is_postgres():
    return bool(DATABASE_URL)

def get_db_connection():
    if is_postgres():
        import psycopg2
        import psycopg2.extras
        url = DATABASE_URL
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        conn = psycopg2.connect(url, cursor_factory=psycopg2.extras.RealDictCursor)
        return conn
    else:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    if is_postgres():
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS players (
                id SERIAL PRIMARY KEY,
                player_id VARCHAR(50) UNIQUE NOT NULL,
                name VARCHAR(255) NOT NULL,
                photo_url TEXT NOT NULL,
                primary_position VARCHAR(100) NOT NULL,
                playing_positions VARCHAR(255) NOT NULL,
                strong_foot VARCHAR(50) NOT NULL,
                preferred_jersey_number INT NOT NULL,
                official_jersey_number INT,
                status VARCHAR(100) NOT NULL,
                created_at VARCHAR(100) NOT NULL,
                updated_at VARCHAR(100) NOT NULL
            )
        """)
    else:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS players (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_id TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                photo_url TEXT NOT NULL,
                primary_position TEXT NOT NULL,
                playing_positions TEXT NOT NULL,
                strong_foot TEXT NOT NULL,
                preferred_jersey_number INTEGER NOT NULL,
                official_jersey_number INTEGER,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
    conn.commit()
    conn.close()

def generate_player_id():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM players ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    if row:
        next_id = (row["id"] if isinstance(row, dict) else row[0]) + 1
    else:
        next_id = 1
    return f"DCF-{next_id:03d}"

def create_player(data):
    conn = get_db_connection()
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    player_id = generate_player_id()
    ph = "%s" if is_postgres() else "?"

    cursor.execute(f"""
        INSERT INTO players (
            player_id, name, photo_url, primary_position, playing_positions,
            strong_foot, preferred_jersey_number, official_jersey_number,
            status, created_at, updated_at
        ) VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph})
    """, (
        player_id,
        data["name"],
        data["photo_url"],
        data["primary_position"],
        data["playing_positions"],
        data["strong_foot"],
        int(data["preferred_jersey_number"]),
        data.get("official_jersey_number"),
        data.get("status", "Active"),
        now,
        now
    ))
    conn.commit()

    cursor.execute(f"SELECT * FROM players WHERE player_id = {ph}", (player_id,))
    player = dict(cursor.fetchone())
    conn.close()
    return player

def get_all_players(search=None, primary_pos=None, specific_pos=None, foot=None, status=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    ph = "%s" if is_postgres() else "?"
    like_op = "ILIKE" if is_postgres() else "LIKE"

    query = "SELECT * FROM players WHERE 1=1"
    params = []

    if search:
        search_term = f"%{search.strip()}%"
        query += f" AND (name {like_op} {ph} OR player_id {like_op} {ph} OR CAST(preferred_jersey_number AS TEXT) {like_op} {ph} OR CAST(official_jersey_number AS TEXT) {like_op} {ph} OR primary_position {like_op} {ph} OR playing_positions {like_op} {ph})"
        params.extend([search_term, search_term, search_term, search_term, search_term, search_term])

    if primary_pos and primary_pos.lower() != "all":
        query += f" AND primary_position = {ph}"
        params.append(primary_pos)

    if specific_pos and specific_pos.lower() != "all":
        query += f" AND (playing_positions {like_op} {ph} OR playing_positions = {ph})"
        params.extend([f"%{specific_pos}%", specific_pos])

    if foot and foot.lower() != "all":
        query += f" AND strong_foot = {ph}"
        params.append(foot)

    if status and status.lower() != "all":
        query += f" AND status = {ph}"
        params.append(status)

    query += " ORDER BY id DESC"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_player_by_id(player_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    ph = "%s" if is_postgres() else "?"
    
    cursor.execute(f"SELECT * FROM players WHERE player_id = {ph} OR CAST(id AS TEXT) = {ph}", (str(player_id), str(player_id)))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def update_player(player_id, data):
    conn = get_db_connection()
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    ph = "%s" if is_postgres() else "?"

    current = get_player_by_id(player_id)
    if not current:
        conn.close()
        return None

    db_id = current["id"]

    name = data.get("name", current["name"])
    photo_url = data.get("photo_url", current["photo_url"])
    primary_position = data.get("primary_position", current["primary_position"])
    playing_positions = data.get("playing_positions", current["playing_positions"])
    strong_foot = data.get("strong_foot", current["strong_foot"])
    preferred_jersey_number = int(data.get("preferred_jersey_number", current["preferred_jersey_number"]))
    
    official_val = data.get("official_jersey_number")
    if official_val is not None and str(official_val).strip() != "":
        official_jersey_number = int(official_val)
    elif official_val == "":
        official_jersey_number = None
    else:
        official_jersey_number = current["official_jersey_number"]

    status = data.get("status", current["status"])

    cursor.execute(f"""
        UPDATE players SET
            name = {ph},
            photo_url = {ph},
            primary_position = {ph},
            playing_positions = {ph},
            strong_foot = {ph},
            preferred_jersey_number = {ph},
            official_jersey_number = {ph},
            status = {ph},
            updated_at = {ph}
        WHERE id = {ph}
    """, (
        name, photo_url, primary_position, playing_positions, strong_foot,
        preferred_jersey_number, official_jersey_number, status, now, db_id
    ))
    conn.commit()

    cursor.execute(f"SELECT * FROM players WHERE id = {ph}", (db_id,))
    updated = dict(cursor.fetchone())
    conn.close()
    return updated

def delete_player(player_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    ph = "%s" if is_postgres() else "?"

    cursor.execute(f"SELECT id FROM players WHERE player_id = {ph} OR CAST(id AS TEXT) = {ph}", (str(player_id), str(player_id)))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return False

    target_id = row["id"] if isinstance(row, dict) else row[0]
    cursor.execute(f"DELETE FROM players WHERE id = {ph}", (target_id,))
    conn.commit()
    conn.close()
    return True

def get_dashboard_stats():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) as total FROM players")
    row = cursor.fetchone()
    total = row["total"] if isinstance(row, dict) else row[0]

    cursor.execute("SELECT COUNT(*) as cnt FROM players WHERE status = 'Active'")
    row = cursor.fetchone()
    active = row["cnt"] if isinstance(row, dict) else row[0]

    cursor.execute("SELECT COUNT(*) as cnt FROM players WHERE status = 'Injured'")
    row = cursor.fetchone()
    injured = row["cnt"] if isinstance(row, dict) else row[0]

    cursor.execute("SELECT COUNT(*) as cnt FROM players WHERE status = 'Unavailable'")
    row = cursor.fetchone()
    unavailable = row["cnt"] if isinstance(row, dict) else row[0]

    cursor.execute("SELECT COUNT(*) as cnt FROM players WHERE status = 'Trial'")
    row = cursor.fetchone()
    trial = row["cnt"] if isinstance(row, dict) else row[0]

    cursor.execute("SELECT COUNT(*) as cnt FROM players WHERE status = 'New Player'")
    row = cursor.fetchone()
    new_player = row["cnt"] if isinstance(row, dict) else row[0]

    cursor.execute("SELECT COUNT(*) as cnt FROM players WHERE status = 'Temporarily Inactive'")
    row = cursor.fetchone()
    temporarily_inactive = row["cnt"] if isinstance(row, dict) else row[0]

    cursor.execute("SELECT COUNT(*) as cnt FROM players WHERE primary_position = 'Goalkeeper'")
    row = cursor.fetchone()
    gk = row["cnt"] if isinstance(row, dict) else row[0]

    cursor.execute("SELECT COUNT(*) as cnt FROM players WHERE primary_position = 'Defender'")
    row = cursor.fetchone()
    defenders = row["cnt"] if isinstance(row, dict) else row[0]

    cursor.execute("SELECT COUNT(*) as cnt FROM players WHERE primary_position = 'Midfielder'")
    row = cursor.fetchone()
    midfielders = row["cnt"] if isinstance(row, dict) else row[0]

    cursor.execute("SELECT COUNT(*) as cnt FROM players WHERE primary_position = 'Forward'")
    row = cursor.fetchone()
    forwards = row["cnt"] if isinstance(row, dict) else row[0]

    conn.close()

    return {
        "total_players": total,
        "active_players": active,
        "injured": injured,
        "unavailable": unavailable,
        "trial_players": trial,
        "new_players": new_player,
        "temporarily_inactive": temporarily_inactive,
        "positions": {
            "goalkeepers": gk,
            "defenders": defenders,
            "midfielders": midfielders,
            "forwards": forwards
        }
    }

def check_jersey_conflicts():
    conn = get_db_connection()
    cursor = conn.cursor()
    ph = "%s" if is_postgres() else "?"

    cursor.execute("""
        SELECT preferred_jersey_number, COUNT(*) as player_count
        FROM players
        GROUP BY preferred_jersey_number
        HAVING COUNT(*) > 1
    """)
    conflicts = []
    rows = cursor.fetchall()
    for row in rows:
        num = row["preferred_jersey_number"]
        count = row["player_count"]
        cursor.execute(f"SELECT id, player_id, name, official_jersey_number FROM players WHERE preferred_jersey_number = {ph}", (num,))
        players = [dict(p) for p in cursor.fetchall()]
        conflicts.append({
            "jersey_number": num,
            "count": count,
            "players": players
        })
    conn.close()
    return conflicts

def export_players_csv():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM players ORDER BY id ASC")
    rows = cursor.fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Player ID", "Name", "Primary Position", "Playing Positions",
        "Strong Foot", "Preferred Jersey Number", "Official Jersey Number",
        "Status", "Registration Date", "Last Updated"
    ])

    for r in rows:
        writer.writerow([
            r["player_id"],
            r["name"],
            r["primary_position"],
            r["playing_positions"],
            r["strong_foot"],
            r["preferred_jersey_number"],
            r["official_jersey_number"] if r["official_jersey_number"] is not None else "Unassigned",
            r["status"],
            r["created_at"],
            r["updated_at"]
        ])

    return output.getvalue()
