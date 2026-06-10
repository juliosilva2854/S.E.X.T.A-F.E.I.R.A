"""Tests for Google Sheets sync + legacy chat intents (sync, atualizar planilha, etc)."""
import os
import pytest
import requests

BASE_URL = os.environ["REACT_APP_BACKEND_URL"].rstrip("/") if os.environ.get("REACT_APP_BACKEND_URL") else None
if not BASE_URL:
    # fallback to reading frontend/.env
    from pathlib import Path
    env_path = Path("/app/frontend/.env")
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if line.startswith("REACT_APP_BACKEND_URL="):
                BASE_URL = line.split("=", 1)[1].strip().rstrip("/")
                break

assert BASE_URL, "REACT_APP_BACKEND_URL not set"


@pytest.fixture(scope="module")
def client():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


# ---------- Health ----------
def test_health(client):
    r = client.get(f"{BASE_URL}/api/health", timeout=15)
    assert r.status_code == 200
    j = r.json()
    assert j.get("status") == "ok"


# ---------- /api/sheets/* ----------
class TestSheets:
    def test_status(self, client):
        r = client.get(f"{BASE_URL}/api/sheets/status", timeout=15)
        assert r.status_code == 200, r.text
        j = r.json()
        # schema
        for key in ("configured", "last_sync", "planilha", "total_rows", "abas"):
            assert key in j, f"missing key {key}"
        assert isinstance(j["configured"], bool)
        assert isinstance(j["total_rows"], int)
        assert isinstance(j["abas"], list)

    def test_sync_no_credentials(self, client):
        # No credentials in container — must return 200 with ok:false (NEVER 500)
        r = client.post(f"{BASE_URL}/api/sheets/sync", timeout=60)
        assert r.status_code == 200, f"got {r.status_code}: {r.text}"
        j = r.json()
        assert "ok" in j
        assert j["ok"] is False
        assert "error" in j
        # error should mention credenciais / google
        assert any(k in j["error"].lower() for k in ["credenc", "google", "oauth"])

    def test_rows(self, client):
        r = client.get(f"{BASE_URL}/api/sheets/rows", timeout=15)
        assert r.status_code == 200, r.text
        j = r.json()
        assert "total" in j and "rows" in j
        assert isinstance(j["total"], int)
        assert isinstance(j["rows"], list)


# ---------- /api/chat: legacy intents ----------
class TestChatLegacy:
    """We only assert intent + skill_result structure. The Gemini reply text may fail
    (leaked key); the request itself may return 500 if brain raises. We accept 200 only.
    """

    def _post_chat(self, client, msg):
        return client.post(f"{BASE_URL}/api/chat",
                           json={"message": msg, "use_web": False},
                           timeout=90)

    def test_sync_sheets_intent(self, client):
        r = self._post_chat(client, "sincroniza planilha")
        assert r.status_code == 200, f"chat returned {r.status_code}: {r.text[:500]}"
        j = r.json()
        assert j.get("intent") == "route.legacy", f"intent was {j.get('intent')}"
        sr = j.get("skill_result") or {}
        assert sr.get("action") == "sheets.sync"
        data = sr.get("data") or {}
        # skill returned controlled error
        assert data.get("ok") is False
        assert "error" in data

    def test_gerar_relatorio_desktop_only(self, client):
        r = self._post_chat(client, "gerar relatório da semana passada")
        assert r.status_code == 200, f"chat returned {r.status_code}: {r.text[:500]}"
        j = r.json()
        assert j.get("intent") == "route.legacy"
        sr = j.get("skill_result") or {}
        assert sr.get("desktop_only") is True, f"skill_result={sr}"
        assert sr.get("action") == "relatorio.gerar"

    def test_atualizar_planilha(self, client):
        r = self._post_chat(client, "atualizar planilha")
        assert r.status_code == 200, f"chat returned {r.status_code}: {r.text[:500]}"
        j = r.json()
        assert j.get("intent") == "route.legacy"
        sr = j.get("skill_result") or {}
        # either desktop_only OR error OR data — never raw 500
        assert sr.get("action") == "planilha.preencher"
        assert ("desktop_only" in sr) or ("error" in sr) or ("data" in sr)

    def test_aprender_rotas(self, client):
        r = self._post_chat(client, "aprender rotas")
        assert r.status_code == 200, f"chat returned {r.status_code}: {r.text[:500]}"
        j = r.json()
        assert j.get("intent") == "route.legacy"
        sr = j.get("skill_result") or {}
        assert sr.get("action") == "rotas.aprender"


# ---------- /api/analytics/* fallback ----------
class TestAnalyticsFallback:
    def test_kpis(self, client):
        r = client.get(f"{BASE_URL}/api/analytics/kpis", timeout=30)
        assert r.status_code == 200, r.text
        # Should respond with KPI shape — not blow up just because sheets cache is empty
        j = r.json()
        assert isinstance(j, dict)
