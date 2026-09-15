import sqlite3
import os
import csv
import io
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "dcf_player_hub.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
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

    # Database initialization (starts clean)
    conn.close()

def seed_sample_players(conn):
    sample_players = [
        {
            "player_id": "DCF-001",
            "name": "Marcus Sterling",
            "photo_url": "/static/img/sample_player_1.svg",
            "primary_position": "Goalkeeper",
            "playing_positions": "GK",
            "strong_foot": "Right",
            "preferred_jersey_number": 1,
            "official_jersey_number": 1,
            "status": "Active",
            "created_at": "2026-09-01T10:00:00",
            "updated_at": "2026-09-01T10:00:00"
        },
        {
            "player_id": "DCF-002",
            "name": "Arjun Kumar",
            "photo_url": "/static/img/sample_player_2.svg",
            "primary_position": "Midfielder",
            "playing_positions": "CM, CAM",
            "strong_foot": "Right",
            "preferred_jersey_number": 10,
            "official_jersey_number": 10,
            "status": "Active",
            "created_at": "2026-09-02T11:30:00",
            "updated_at": "2026-09-02T11:30:00"
        },
        {
            "player_id": "DCF-003",
            "name": "Diego Vance",
            "photo_url": "/static/img/sample_player_3.svg",
            "primary_position": "Forward",
            "playing_positions": "ST, CF",
            "strong_foot": "Right",
            "preferred_jersey_number": 9,
            "official_jersey_number": 9,
            "status": "Active",
            "created_at": "2026-09-03T14:15:00",
            "updated_at": "2026-09-03T14:15:00"
        },
        {
            "player_id": "DCF-004",
            "name": "Lucas Silva",
            "photo_url": "/static/img/sample_player_4.svg",
            "primary_position": "Defender",
            "playing_positions": "CB, LWB",
            "strong_foot": "Left",
            "preferred_jersey_number": 4,
            "official_jersey_number": 4,
            "status": "Active",
            "created_at": "2026-09-04T09:45:00",
            "updated_at": "2026-09-04T09:45:00"
        },
        {
            "player_id": "DCF-005",
            "name": "Vikram Patel",
            "photo_url": "/static/img/sample_player_5.svg",
            "primary_position": "Midfielder",
            "playing_positions": "CDM, CM",
            "strong_foot": "Right",
            "preferred_jersey_number": 6,
            "official_jersey_number": 6,
            "status": "Injured",
            "created_at": "2026-09-05T16:20:00",
            "updated_at": "2026-09-12T08:10:00"
        },
        {
            "player_id": "DCF-006",
            "name": "Mateo Rossi",
            "photo_url": "/static/img/sample_player_6.svg",
            "primary_position": "Forward",
            "playing_positions": "LW, RW",
            "strong_foot": "Both",
            "preferred_jersey_number": 7,
            "official_jersey_number": 7,
            "status": "Trial",
            "created_at": "2026-09-10T12:00:00",
            "updated_at": "2026-09-10T12:00:00"
        },
        {
            "player_id": "DCF-007",
            "name": "Rahul Singh",
            "photo_url": "/static/img/sample_player_7.svg",
            "primary_position": "Defender",
            "playing_positions": "RB, RWB",
            "strong_foot": "Right",
            "preferred_jersey_number": 10,
            "official_jersey_number": None,
            "status": "New Player",
            "created_at": "2026-09-14T17:30:00",
            "updated_at": "2026-09-14T17:30:00"
        }
    ]

    cursor = conn.cursor()
    for p in sample_players:
        cursor.execute("""
            INSERT INTO players (
                player_id, name, photo_url, primary_position, playing_positions,
                strong_foot, preferred_jersey_number, official_jersey_number,
                status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            p["player_id"], p["name"], p["photo_url"], p["primary_position"],
            p["playing_positions"], p["strong_foot"], p["preferred_jersey_number"],
            p["official_jersey_number"], p["status"], p["created_at"], p["updated_at"]
        ))
    conn.commit()

def generate_player_id():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM players ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    if row:
        next_id = row["id"] + 1
    else:
        next_id = 1
    return f"DCF-{next_id:03d}"

def create_player(data):
    conn = get_db_connection()
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    player_id = generate_player_id()

    cursor.execute("""
        INSERT INTO players (
            player_id, name, photo_url, primary_position, playing_positions,
            strong_foot, preferred_jersey_number, official_jersey_number,
            status, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
    inserted_id = cursor.lastrowid
    cursor.execute("SELECT * FROM players WHERE id = ?", (inserted_id,))
    player = dict(cursor.fetchone())
    conn.close()
    return player

def get_all_players(search=None, primary_pos=None, specific_pos=None, foot=None, status=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = "SELECT * FROM players WHERE 1=1"
    params = []

    if search:
        search_term = f"%{search.strip()}%"
        query += " AND (name LIKE ? OR player_id LIKE ? OR CAST(preferred_jersey_number AS TEXT) LIKE ? OR CAST(official_jersey_number AS TEXT) LIKE ? OR primary_position LIKE ? OR playing_positions LIKE ?)"
        params.extend([search_term, search_term, search_term, search_term, search_term, search_term])

    if primary_pos and primary_pos.lower() != "all":
        query += " AND primary_position = ?"
        params.append(primary_pos)

    if specific_pos and specific_pos.lower() != "all":
        query += " AND (playing_positions LIKE ? OR playing_positions = ?)"
        params.extend([f"%{specific_pos}%", specific_pos])

    if foot and foot.lower() != "all":
        query += " AND strong_foot = ?"
        params.append(foot)

    if status and status.lower() != "all":
        query += " AND status = ?"
        params.append(status)

    query += " ORDER BY id DESC"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_player_by_id(player_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM players WHERE player_id = ? OR id = ?", (player_id, player_id))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def update_player(player_id, data):
    conn = get_db_connection()
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    
    cursor.execute("SELECT * FROM players WHERE id = ? OR player_id = ?", (player_id, player_id))
    current = cursor.fetchone()
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

    cursor.execute("""
        UPDATE players SET
            name = ?,
            photo_url = ?,
            primary_position = ?,
            playing_positions = ?,
            strong_foot = ?,
            preferred_jersey_number = ?,
            official_jersey_number = ?,
            status = ?,
            updated_at = ?
        WHERE id = ?
    """, (
        name, photo_url, primary_position, playing_positions, strong_foot,
        preferred_jersey_number, official_jersey_number, status, now, db_id
    ))
    conn.commit()

    cursor.execute("SELECT * FROM players WHERE id = ?", (db_id,))
    updated = dict(cursor.fetchone())
    conn.close()
    return updated

def delete_player(player_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM players WHERE id = ? OR player_id = ?", (player_id, player_id))
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected > 0

def get_dashboard_stats():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) as total FROM players")
    total = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) as cnt FROM players WHERE status = 'Active'")
    active = cursor.fetchone()["cnt"]

    cursor.execute("SELECT COUNT(*) as cnt FROM players WHERE status = 'Injured'")
    injured = cursor.fetchone()["cnt"]

    cursor.execute("SELECT COUNT(*) as cnt FROM players WHERE status = 'Unavailable'")
    unavailable = cursor.fetchone()["cnt"]

    cursor.execute("SELECT COUNT(*) as cnt FROM players WHERE status = 'Trial'")
    trial = cursor.fetchone()["cnt"]

    cursor.execute("SELECT COUNT(*) as cnt FROM players WHERE status = 'New Player'")
    new_player = cursor.fetchone()["cnt"]

    cursor.execute("SELECT COUNT(*) as cnt FROM players WHERE status = 'Temporarily Inactive'")
    temporarily_inactive = cursor.fetchone()["cnt"]

    # Position breakdowns
    cursor.execute("SELECT COUNT(*) as cnt FROM players WHERE primary_position = 'Goalkeeper'")
    gk = cursor.fetchone()["cnt"]

    cursor.execute("SELECT COUNT(*) as cnt FROM players WHERE primary_position = 'Defender'")
    defenders = cursor.fetchone()["cnt"]

    cursor.execute("SELECT COUNT(*) as cnt FROM players WHERE primary_position = 'Midfielder'")
    midfielders = cursor.fetchone()["cnt"]

    cursor.execute("SELECT COUNT(*) as cnt FROM players WHERE primary_position = 'Forward'")
    forwards = cursor.fetchone()["cnt"]

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
    cursor.execute("""
        SELECT preferred_jersey_number, COUNT(*) as player_count
        FROM players
        GROUP BY preferred_jersey_number
        HAVING player_count > 1
    """)
    conflicts = []
    rows = cursor.fetchall()
    for row in rows:
        num = row["preferred_jersey_number"]
        count = row["player_count"]
        cursor.execute("SELECT player_id, name, official_jersey_number FROM players WHERE preferred_jersey_number = ?", (num,))
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
