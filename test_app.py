import urllib.request
import urllib.parse
import json

BASE_URL = "http://127.0.0.1:8000"

def test_root():
    print("Testing GET / ...")
    req = urllib.request.urlopen(f"{BASE_URL}/")
    assert req.status == 200
    html = req.read().decode('utf-8')
    assert "DCF | PLAYER HUB" in html
    print("[OK] GET / OK")

def test_players():
    print("Testing GET /api/players ...")
    req = urllib.request.urlopen(f"{BASE_URL}/api/players")
    assert req.status == 200
    players = json.loads(req.read().decode('utf-8'))
    assert isinstance(players, list)
    assert len(players) >= 7
    print(f"[OK] GET /api/players OK ({len(players)} players retrieved)")

def test_search_and_filter():
    print("Testing search & filter endpoints ...")
    # Search by name
    req = urllib.request.urlopen(f"{BASE_URL}/api/players?search=Arjun")
    players = json.loads(req.read().decode('utf-8'))
    assert len(players) >= 1
    assert "Arjun" in players[0]["name"]
    print("[OK] Search by name OK")

    # Filter by position
    req = urllib.request.urlopen(f"{BASE_URL}/api/players?primary_pos=Goalkeeper")
    players = json.loads(req.read().decode('utf-8'))
    assert all(p["primary_position"] == "Goalkeeper" for p in players)
    print("[OK] Filter by Goalkeeper OK")

    # Filter by foot
    req = urllib.request.urlopen(f"{BASE_URL}/api/players?foot=Left")
    players = json.loads(req.read().decode('utf-8'))
    assert all(p["strong_foot"] == "Left" for p in players)
    print("[OK] Filter by Left foot OK")

def test_admin_flow():
    print("Testing admin authentication & endpoints ...")
    # Login
    data = json.dumps({"password": "admin123"}).encode('utf-8')
    req = urllib.request.Request(f"{BASE_URL}/api/admin/login", data=data, headers={'Content-Type': 'application/json'})
    resp = urllib.request.urlopen(req)
    res_json = json.loads(resp.read().decode('utf-8'))
    token = res_json.get("token")
    assert token is not None
    print("[OK] Admin Login OK")

    # Stats
    req = urllib.request.Request(f"{BASE_URL}/api/admin/stats", headers={'Authorization': f'Bearer {token}'})
    stats = json.loads(urllib.request.urlopen(req).read().decode('utf-8'))
    assert stats["total_players"] >= 7
    print(f"[OK] Admin Stats OK (Total: {stats['total_players']}, Active: {stats['active_players']})")

    # CSV Export
    req = urllib.request.Request(f"{BASE_URL}/api/admin/export", headers={'Authorization': f'Bearer {token}'})
    csv_str = urllib.request.urlopen(req).read().decode('utf-8')
    assert "Player ID,Name" in csv_str
    assert "DCF-001" in csv_str
    print("[OK] Admin CSV Export OK")

if __name__ == "__main__":
    test_root()
    test_players()
    test_search_and_filter()
    test_admin_flow()
    print("\nALL VERIFICATION TESTS PASSED SUCCESSFULLY!")
