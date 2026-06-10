"""Tests for daily Google Sheets auto-sync (APScheduler) endpoints.

Endpoints:
  GET  /api/sheets/autosync                 -> {enabled, hour, next_run}
  POST /api/sheets/autosync/toggle          -> ?enabled=&hour=
Regression:
  GET  /api/sheets/status
  GET  /api/sheets/rows
  POST /api/chat ('sincroniza planilha')
  GET  /api/analytics/kpis
"""
import os
import re
import time
import pytest
import requests
from pathlib import Path

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL")
if not BASE_URL:
    env_path = Path("/app/frontend/.env")
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if line.startswith("REACT_APP_BACKEND_URL="):
                BASE_URL = line.split("=", 1)[1].strip()
                break
BASE_URL = (BASE_URL or "").rstrip("/")
assert BASE_URL, "REACT_APP_BACKEND_URL not set"

BACKEND_ENV = Path("/app/backend/.env")


def _read_env_value(key: str):
    if not BACKEND_ENV.exists():
        return None
    for line in BACKEND_ENV.read_text().splitlines():
        if line.startswith(f"{key}="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None


@pytest.fixture(scope="module")
def client():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


# ---------- /api/sheets/autosync (GET) ----------
class TestAutosyncStatus:
    def test_get_schema(self, client):
        r = client.get(f"{BASE_URL}/api/sheets/autosync", timeout=15)
        assert r.status_code == 200, r.text
        j = r.json()
        assert set(j.keys()) >= {"enabled", "hour", "next_run"}, j
        assert isinstance(j["enabled"], bool)
        assert isinstance(j["hour"], int)
        assert j["next_run"] is None or isinstance(j["next_run"], str)


# ---------- /api/sheets/autosync/toggle ----------
class TestAutosyncToggle:
    def test_enable_at_hour_7(self, client):
        r = client.post(
            f"{BASE_URL}/api/sheets/autosync/toggle",
            params={"enabled": "true", "hour": 7},
            timeout=15,
        )
        assert r.status_code == 200, r.text
        j = r.json()
        assert j["enabled"] is True
        assert j["hour"] == 7
        assert isinstance(j["next_run"], str) and j["next_run"], j
        # .env persisted
        assert _read_env_value("MAVIS_SHEETS_AUTOSYNC") == "1"
        assert _read_env_value("MAVIS_SHEETS_AUTOSYNC_HOUR") == "7"
        # Status endpoint reflects state
        time.sleep(0.3)
        s = client.get(f"{BASE_URL}/api/sheets/autosync", timeout=15).json()
        assert s["enabled"] is True
        assert s["hour"] == 7
        assert s["next_run"], "scheduler should expose next_run when enabled"

    def test_reschedule_hour_8(self, client):
        r = client.post(
            f"{BASE_URL}/api/sheets/autosync/toggle",
            params={"enabled": "true", "hour": 8},
            timeout=15,
        )
        assert r.status_code == 200, r.text
        j = r.json()
        assert j["enabled"] is True
        assert j["hour"] == 8
        assert isinstance(j["next_run"], str)
        # next_run should contain 08:00 (UTC or local, depends on scheduler tz)
        assert re.search(r"08:00", j["next_run"]) or re.search(r"T08", j["next_run"]) or "08:" in j["next_run"], (
            f"next_run does not seem to use hour=8: {j['next_run']}"
        )
        assert _read_env_value("MAVIS_SHEETS_AUTOSYNC_HOUR") == "8"

    def test_disable(self, client):
        r = client.post(
            f"{BASE_URL}/api/sheets/autosync/toggle",
            params={"enabled": "false"},
            timeout=15,
        )
        assert r.status_code == 200, r.text
        j = r.json()
        assert j["enabled"] is False
        assert j["next_run"] is None
        assert _read_env_value("MAVIS_SHEETS_AUTOSYNC") == "0"
        # Status endpoint reflects state
        s = client.get(f"{BASE_URL}/api/sheets/autosync", timeout=15).json()
        assert s["enabled"] is False
        assert s["next_run"] is None

    def test_cleanup_disabled(self, client):
        """Ensure scheduler is disabled at the end (cleanup)."""
        client.post(
            f"{BASE_URL}/api/sheets/autosync/toggle",
            params={"enabled": "false"},
            timeout=15,
        )
        assert _read_env_value("MAVIS_SHEETS_AUTOSYNC") == "0"


# ---------- Regression ----------
class TestRegression:
    def test_sheets_status(self, client):
        r = client.get(f"{BASE_URL}/api/sheets/status", timeout=15)
        assert r.status_code == 200
        j = r.json()
        for key in ("configured", "last_sync", "planilha", "total_rows", "abas"):
            assert key in j

    def test_sheets_rows(self, client):
        r = client.get(f"{BASE_URL}/api/sheets/rows", timeout=15)
        assert r.status_code == 200
        j = r.json()
        assert "total" in j and "rows" in j

    def test_chat_sync_intent(self, client):
        r = client.post(
            f"{BASE_URL}/api/chat",
            json={"message": "sincroniza planilha", "use_web": False},
            timeout=90,
        )
        assert r.status_code == 200, r.text[:500]
        j = r.json()
        assert j.get("intent") == "route.legacy"
        sr = j.get("skill_result") or {}
        assert sr.get("action") == "sheets.sync"

    def test_analytics_kpis(self, client):
        r = client.get(f"{BASE_URL}/api/analytics/kpis", timeout=30)
        assert r.status_code == 200
        assert isinstance(r.json(), dict)
