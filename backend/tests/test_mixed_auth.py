"""
Tests for the MAVIS mixed-auth + publish flow (IS_CLOUD=true).
Covers:
  - cloud_auth_guard (401 on protected /api/*)
  - /api/auth/password (correct/incorrect) + cookie + Bearer
  - /api/auth/me (with Bearer)
  - /api/public/* bypass (own validation error, not the guard message)
  - /api/allowed-emails CRUD (authed)
  - /api/publish protection via X-Publish-Key
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    # Fallback to frontend .env (the test environment uses this)
    try:
        with open("/app/frontend/.env") as fh:
            for line in fh:
                if line.startswith("REACT_APP_BACKEND_URL="):
                    BASE_URL = line.split("=", 1)[1].strip().rstrip("/")
                    break
    except Exception:
        pass
assert BASE_URL, "REACT_APP_BACKEND_URL is required"

ADMIN_PASSWORD = "fVcuKJmpJ6_TbyF3"
PUBLISH_KEY = "AyCwjongfdwJsyjEw7gKKC2I9D1NGSxo"
SEED_EMAIL = "julio.silva2854@gmail.com"


@pytest.fixture(scope="module")
def http():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="module")
def session_token(http):
    r = http.post(f"{BASE_URL}/api/auth/password", json={"password": ADMIN_PASSWORD}, timeout=15)
    assert r.status_code == 200, f"login failed: {r.status_code} {r.text}"
    data = r.json()
    assert data.get("ok") is True
    assert "session_token" in data and isinstance(data["session_token"], str)
    return data["session_token"]


@pytest.fixture
def authed(http, session_token):
    s = requests.Session()
    s.headers.update({
        "Content-Type": "application/json",
        "Authorization": f"Bearer {session_token}",
    })
    return s


# ---------- cloud_auth_guard ----------
class TestGuard:
    def test_status_unauth_returns_401(self):
        r = requests.get(f"{BASE_URL}/api/status", timeout=10)
        assert r.status_code == 401, r.text
        body = r.json()
        assert body.get("detail") == "Não autenticado"

    def test_auth_config_is_public(self):
        r = requests.get(f"{BASE_URL}/api/auth/config", timeout=10)
        assert r.status_code == 200
        data = r.json()
        assert data["is_cloud"] is True
        assert data["password_enabled"] is True


# ---------- /api/auth/password ----------
class TestPasswordAuth:
    def test_wrong_password_returns_401(self, http):
        r = http.post(f"{BASE_URL}/api/auth/password", json={"password": "wrong-password"}, timeout=10)
        assert r.status_code == 401

    def test_correct_password_returns_token_and_cookie(self, http):
        r = http.post(f"{BASE_URL}/api/auth/password", json={"password": ADMIN_PASSWORD}, timeout=15)
        assert r.status_code == 200
        data = r.json()
        assert data["ok"] is True
        assert isinstance(data["session_token"], str) and len(data["session_token"]) > 10
        assert data["user"]["auth"] == "password"
        # cookie set
        assert "session_token" in r.cookies, f"cookies: {r.cookies.items()}"


# ---------- /api/auth/me ----------
class TestAuthMe:
    def test_me_with_bearer(self, authed):
        r = authed.get(f"{BASE_URL}/api/auth/me", timeout=10)
        assert r.status_code == 200
        u = r.json()
        assert "user_id" in u
        assert u.get("auth") in ("password", "google", "local")

    def test_status_with_bearer(self, authed):
        r = authed.get(f"{BASE_URL}/api/status", timeout=10)
        assert r.status_code == 200, r.text


# ---------- public bypass ----------
class TestPublicBypass:
    def test_public_validate_bypasses_guard(self):
        """
        /api/public/* must NOT hit the cloud_auth_guard. So unauth call
        should NOT return the guard's 'Não autenticado'; instead it should
        return the endpoint's own token-missing error (401/403/422).
        """
        r = requests.get(f"{BASE_URL}/api/public/validate", timeout=10)
        # not the guard message
        try:
            body = r.json()
        except Exception:
            body = {}
        detail = (body.get("detail") or "").lower() if isinstance(body, dict) else ""
        assert detail != "não autenticado", f"guard wrongly fired: {r.status_code} {r.text}"
        # endpoint runs its own validation -> should be 401/403/422
        assert r.status_code in (401, 403, 422), r.text


# ---------- /api/allowed-emails CRUD ----------
class TestAllowedEmails:
    def test_list_contains_seed(self, authed):
        r = authed.get(f"{BASE_URL}/api/allowed-emails", timeout=10)
        assert r.status_code == 200
        emails = [item.get("email") for item in r.json()]
        assert SEED_EMAIL in emails, f"missing seed; got: {emails}"

    def test_add_and_delete(self, authed):
        test_email = "test_mixedauth+autotest@example.com"
        try:
            r = authed.post(
                f"{BASE_URL}/api/allowed-emails",
                json={"email": test_email}, timeout=10,
            )
            assert r.status_code == 200
            assert r.json().get("email") == test_email

            r2 = authed.get(f"{BASE_URL}/api/allowed-emails", timeout=10)
            assert r2.status_code == 200
            emails = [it["email"] for it in r2.json()]
            assert test_email in emails
        finally:
            r3 = authed.delete(f"{BASE_URL}/api/allowed-emails/{test_email}", timeout=10)
            assert r3.status_code == 200
            r4 = authed.get(f"{BASE_URL}/api/allowed-emails", timeout=10)
            emails = [it["email"] for it in r4.json()]
            assert test_email not in emails

    def test_list_requires_auth(self):
        r = requests.get(f"{BASE_URL}/api/allowed-emails", timeout=10)
        assert r.status_code == 401


# ---------- /api/publish ----------
class TestPublish:
    def test_wrong_key_401(self):
        r = requests.post(
            f"{BASE_URL}/api/publish",
            json={"banco_de_dados": {"_test": 1}},
            headers={"Content-Type": "application/json", "X-Publish-Key": "wrong"},
            timeout=15,
        )
        assert r.status_code == 401

    def test_no_key_401(self):
        r = requests.post(
            f"{BASE_URL}/api/publish",
            json={"banco_de_dados": {"_test": 1}},
            headers={"Content-Type": "application/json"},
            timeout=15,
        )
        assert r.status_code == 401

    def test_correct_key_ok(self):
        r = requests.post(
            f"{BASE_URL}/api/publish",
            json={"banco_de_dados": {"_test": 1}},
            headers={"Content-Type": "application/json", "X-Publish-Key": PUBLISH_KEY},
            timeout=20,
        )
        assert r.status_code == 200, r.text
        data = r.json()
        assert data.get("ok") is True
        assert "banco_de_dados" in (data.get("written") or [])
