import os
import uuid
from typing import Optional, List
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Depends, Query, status
from fastapi.responses import HTMLResponse, Response, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.database import (
    init_db, create_player, get_all_players, get_player_by_id,
    update_player, delete_player, get_dashboard_stats, check_jersey_conflicts,
    export_players_csv
)
from app.auth import authenticate_admin, verify_token

app = FastAPI(title="DCF | PLAYER HUB API", version="1.0.0")

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.environ.get("DATA_DIR", BASE_DIR)
STATIC_DIR = os.path.join(BASE_DIR, "static")
UPLOADS_BASE_DIR = os.path.join(DATA_DIR, "uploads")
UPLOADS_DIR = os.path.join(UPLOADS_BASE_DIR, "players")

os.makedirs(UPLOADS_DIR, exist_ok=True)

# Mount Static & Uploads
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.mount("/uploads", StaticFiles(directory=UPLOADS_BASE_DIR), name="uploads")

@app.on_event("startup")
def startup_event():
    init_db()

@app.api_route("/", methods=["GET", "HEAD"], response_class=HTMLResponse)
def read_root():
    index_file = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_file):
        with open(index_file, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>DCF | PLAYER HUB API Running</h1>"

@app.get("/api/db-status")
def db_status():
    from app.database import is_postgres, get_db_connection
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as cnt FROM players")
        row = cursor.fetchone()
        conn.close()
        count = row["cnt"] if hasattr(row, "__getitem__") and "cnt" in row else row[0]
        return {
            "status": "healthy",
            "database_engine": "PostgreSQL (Persistent Cloud DB)" if is_postgres() else "SQLite (Local File DB)",
            "is_postgres": is_postgres(),
            "connected": True,
            "total_players_in_db": count
        }
    except Exception as e:
        return {
            "status": "error",
            "database_engine": "PostgreSQL" if is_postgres() else "SQLite",
            "connected": False,
            "error_message": str(e)
        }

# --- PUBLIC PLAYER ENDPOINTS ---

@app.get("/api/players")
def list_players(
    search: Optional[str] = Query(None),
    primary_pos: Optional[str] = Query(None, alias="primary_pos"),
    specific_pos: Optional[str] = Query(None, alias="specific_pos"),
    foot: Optional[str] = Query(None),
    status: Optional[str] = Query(None)
):
    return get_all_players(
        search=search,
        primary_pos=primary_pos,
        specific_pos=specific_pos,
        foot=foot,
        status=status
    )

@app.get("/api/players/{player_id}")
def get_player(player_id: str):
    player = get_player_by_id(player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    return player

@app.post("/api/register")
async def register_player(
    name: str = Form(...),
    primary_position: str = Form(...),
    playing_positions: str = Form(...),
    strong_foot: str = Form(...),
    preferred_jersey_number: int = Form(...),
    status: str = Form("Active"),
    photo: UploadFile = File(...)
):
    # Form Validations
    if not name or len(name.strip()) < 2:
        raise HTTPException(status_code=400, detail="Please enter a valid player name.")

    if not primary_position:
        raise HTTPException(status_code=400, detail="Please select your primary position.")

    if not playing_positions:
        raise HTTPException(status_code=400, detail="Please select your specific position(s) of play.")

    if not strong_foot:
        raise HTTPException(status_code=400, detail="Please select your strong foot.")

    if preferred_jersey_number < 1 or preferred_jersey_number > 99:
        raise HTTPException(status_code=400, detail="Please enter a valid jersey number between 1 and 99.")

    # Image Validation
    if not photo or not photo.filename:
        raise HTTPException(status_code=400, detail="Please upload a player photograph.")

    allowed_exts = [".jpg", ".jpeg", ".png", ".webp"]
    file_ext = os.path.splitext(photo.filename)[1].lower()
    if file_ext not in allowed_exts:
        raise HTTPException(status_code=400, detail="Only JPG, JPEG, PNG, and WEBP image files are allowed.")

    # Check file size (5MB max)
    contents = await photo.read()
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Player photo size must not exceed 5MB.")

    # Convert photo to Base64 Data URI for 100% database persistence
    import base64
    encoded_str = base64.b64encode(contents).decode('utf-8')
    mime = photo.content_type if photo.content_type else f"image/{file_ext.replace('.', '')}"
    photo_url = f"data:{mime};base64,{encoded_str}"

    player_data = {
        "name": name.strip(),
        "photo_url": photo_url,
        "primary_position": primary_position,
        "playing_positions": playing_positions,
        "strong_foot": strong_foot,
        "preferred_jersey_number": preferred_jersey_number,
        "status": status,
    }

    new_player = create_player(player_data)
    return {
        "success": True,
        "message": "Your information has been successfully added to the DCF Player Database.",
        "player": new_player
    }

# --- ADMIN ENDPOINTS ---

@app.post("/api/admin/login")
def admin_login(data: dict):
    password = data.get("password")
    if not password:
        raise HTTPException(status_code=400, detail="Password is required")

    token = authenticate_admin(password)
    if not token:
        raise HTTPException(status_code=401, detail="Invalid admin password")

    return {"success": True, "token": token}

@app.get("/api/admin/stats")
def admin_stats(token: str = Depends(verify_token)):
    return get_dashboard_stats()

@app.get("/api/admin/jersey-conflicts")
def admin_jersey_conflicts(token: str = Depends(verify_token)):
    return check_jersey_conflicts()

@app.put("/api/admin/players/{player_id}")
async def admin_update_player(
    player_id: str,
    name: Optional[str] = Form(None),
    primary_position: Optional[str] = Form(None),
    playing_positions: Optional[str] = Form(None),
    strong_foot: Optional[str] = Form(None),
    preferred_jersey_number: Optional[int] = Form(None),
    official_jersey_number: Optional[str] = Form(None),
    status: Optional[str] = Form(None),
    photo: Optional[UploadFile] = File(None),
    token: str = Depends(verify_token)
):
    update_data = {}
    if name is not None:
        update_data["name"] = name.strip()
    if primary_position is not None:
        update_data["primary_position"] = primary_position
    if playing_positions is not None:
        update_data["playing_positions"] = playing_positions
    if strong_foot is not None:
        update_data["strong_foot"] = strong_foot
    if preferred_jersey_number is not None:
        update_data["preferred_jersey_number"] = preferred_jersey_number
    if official_jersey_number is not None:
        update_data["official_jersey_number"] = official_jersey_number
    if status is not None:
        update_data["status"] = status

    if photo and photo.filename:
        allowed_exts = [".jpg", ".jpeg", ".png", ".webp"]
        file_ext = os.path.splitext(photo.filename)[1].lower()
        if file_ext in allowed_exts:
            contents = await photo.read()
            if len(contents) <= 5 * 1024 * 1024:
                import base64
                encoded_str = base64.b64encode(contents).decode('utf-8')
                mime = photo.content_type if photo.content_type else f"image/{file_ext.replace('.', '')}"
                update_data["photo_url"] = f"data:{mime};base64,{encoded_str}"

    updated = update_player(player_id, update_data)
    if not updated:
        raise HTTPException(status_code=404, detail="Player record not found")

    return {"success": True, "player": updated}

@app.delete("/api/players/{player_id}")
def delete_player_public(player_id: str):
    success = delete_player(player_id)
    if not success:
        raise HTTPException(status_code=404, detail="Player record not found or already deleted")
    return {"success": True, "message": f"Player {player_id} deleted successfully"}

@app.delete("/api/admin/players/{player_id}")
def admin_delete_player(player_id: str, token: str = Depends(verify_token)):
    success = delete_player(player_id)
    if not success:
        raise HTTPException(status_code=404, detail="Player not found or deletion failed")
    return {"success": True, "message": f"Player {player_id} deleted successfully"}

@app.get("/api/admin/export")
def admin_export_csv(token: str = Depends(verify_token)):
    csv_data = export_players_csv()
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=DCF_Player_Database.csv"}
    )
