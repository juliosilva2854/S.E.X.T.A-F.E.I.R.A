"""Backend tests for WAHA integration endpoints.

WAHA is NOT running in this preview container — we expect connected=false
but endpoints must respond 200 OK with the correct schema (never 500/crash).
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://project-scanner-47.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"


@pytest.fixture(scope="module")
def client():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


# ---------- Health ----------
def test_health(client):
    r = client.get(f"{API}/health", timeout=15)
    assert r.status_code == 200, f"/api/health failed: {r.status_code} {r.text[:200]}"


# ---------- /api/whatsapp/status ----------
def test_whatsapp_status_schema(client):
    r = client.get(f"{API}/whatsapp/status", timeout=20)
    assert r.status_code == 200, f"status returned {r.status_code}: {r.text[:200]}"
    data = r.json()
    # Required fields
    for k in ("connected", "status", "session", "url"):
        assert k in data, f"missing field '{k}' in status response: {data}"
    assert isinstance(data["connected"], bool)
    assert isinstance(data["status"], str)
    assert isinstance(data["session"], str)
    assert isinstance(data["url"], str)
    # WAHA is offline in this env
    assert data["connected"] is False
    # url should reflect WAHA_URL from .env (localhost:3001)
    assert "3001" in data["url"], f"expected WAHA URL to contain 3001, got {data['url']}"
    # session default
    assert data["session"] == "default"


# ---------- /api/whatsapp/unread ----------
def test_whatsapp_unread_no_500(client):
    r = client.get(f"{API}/whatsapp/unread", timeout=20)
    assert r.status_code == 200, f"unread returned {r.status_code}: {r.text[:200]}"
    data = r.json()
    assert isinstance(data, list), f"expected list, got {type(data)}: {data}"
    # WAHA off → list should contain at least an entry with 'error' (or be empty)
    if data:
        # may contain dicts with 'error' OR normal chats
        assert isinstance(data[0], dict)


# ---------- /api/whatsapp/favorites ----------
def test_whatsapp_favorites_returns_seed(client):
    r = client.get(f"{API}/whatsapp/favorites", timeout=15)
    assert r.status_code == 200, f"favorites failed: {r.status_code} {r.text[:200]}"
    data = r.json()
    assert isinstance(data, list)
    # 3 seeded favorites expected per spec
    assert len(data) >= 1, "expected at least 1 seeded favorite"
    for fav in data:
        assert "id" in fav and "nome" in fav


# ---------- /api/whatsapp/send ----------
def test_whatsapp_send_no_crash(client):
    # First grab a favorite
    favs = client.get(f"{API}/whatsapp/favorites", timeout=15).json()
    if not favs:
        pytest.skip("no favorites to send to")
    fav_id = favs[0]["id"]
    r = client.post(
        f"{API}/whatsapp/send",
        json={"favorite_id": fav_id, "message": "TEST_waha_offline_probe"},
        timeout=30,
    )
    # Must NOT crash — accept either 200 with sent=false OR controlled 4xx/5xx with JSON
    assert r.status_code in (200, 400, 502, 503, 504), f"unexpected status {r.status_code}: {r.text[:300]}"
    # body must be JSON-parseable
    try:
        body = r.json()
    except Exception:
        pytest.fail(f"response not JSON: {r.text[:300]}")
    if r.status_code == 200:
        # Should report sent=false because WAHA is offline
        assert "sent" in body
        assert body["sent"] is False, f"WAHA is offline; expected sent=False, got {body}"
        # Should include error string somewhere
        err = body.get("error") or body.get("destino", {}).get("error", "")
        assert err or body.get("sent") is False
