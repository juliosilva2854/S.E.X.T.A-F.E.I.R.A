"""
Backend tests for S.E.X.T.A - F.E.I.R.A (MAVIS) v3.0 NEW endpoints:
- /api/status (campos novos: total_facts, total_reminders, personality, google_ready)
- /api/long-memory CRUD
- /api/reminders CRUD + /natural (Gemini smart_extract)
- /api/vision/analyze (multipart upload, Gemini Vision)
- /api/google/status, /api/google/calendar/today (esperado erro sem credenciais)
- /api/skills, /api/system/info, /api/news, /api/weather
- /api/chat com intents (system.battery, reminder.create, memory.save_fact, fallback rotas)
- /api/config PATCH personalidade

IMPORTANTE: usa prefixo TESTE_PYTEST e limpa sempre.
"""
import os
import io
import json
import time
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
assert BASE_URL, "REACT_APP_BACKEND_URL must be set"
API = f"{BASE_URL}/api"


@pytest.fixture(scope="module")
def client():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


# -------------------- STATUS v3 fields --------------------
class TestStatusV3:
    def test_status_has_v3_fields(self, client):
        r = client.get(f"{API}/status", timeout=15)
        assert r.status_code == 200
        d = r.json()
        for key in ("total_facts", "total_reminders", "personality", "google_ready"):
            assert key in d, f"missing key {key}"
        assert isinstance(d["total_facts"], int)
        assert isinstance(d["total_reminders"], int)
        assert isinstance(d["google_ready"], bool)
        assert d["personality"] in ("corporativa", "casual", "sarcastica")


# -------------------- SKILLS / SYSTEM / NEWS / WEATHER --------------------
class TestStaticSkills:
    def test_skills_catalog(self, client):
        r = client.get(f"{API}/skills", timeout=15)
        assert r.status_code == 200
        d = r.json()
        nomes = [c["nome"] for c in d["categorias"]]
        for expected in ("Sistema", "Computador", "Visão", "WhatsApp", "Google",
                         "Mídia", "Informação", "Memória", "Relatórios"):
            assert expected in nomes, f"categoria ausente: {expected}"

    def test_system_info(self, client):
        r = client.get(f"{API}/system/info", timeout=15)
        assert r.status_code == 200
        d = r.json()
        for k in ("battery", "cpu", "ram", "disk"):
            assert k in d
        # cpu and ram precisam ter "percent"
        assert "percent" in d["cpu"]
        assert "percent" in d["ram"]
        assert isinstance(d["cpu"]["percent"], (int, float))
        assert isinstance(d["ram"]["percent"], (int, float))

    def test_news(self, client):
        r = client.get(f"{API}/news?limit=2", timeout=30)
        assert r.status_code == 200
        lst = r.json()
        assert isinstance(lst, list)
        # G1 RSS é estável; tolerar lista vazia se houver falha de rede
        if lst:
            assert len(lst) <= 2
            it = lst[0]
            for k in ("title", "link", "published"):
                assert k in it, f"missing {k} in news item: {it}"

    def test_weather(self, client):
        r = client.get(f"{API}/weather", timeout=30)
        assert r.status_code == 200
        d = r.json()
        # Open-Meteo => esperado temp_c/max_c/min_c/rain_prob
        # tolerar erro só se chave "error" presente
        if "error" not in d:
            for k in ("temp_c", "max_c", "min_c", "rain_prob"):
                assert k in d, f"missing weather key {k}: {d}"


# -------------------- LONG-MEMORY CRUD --------------------
class TestLongMemory:
    fact_id = None

    def test_create_fact(self, client):
        payload = {"category": "pessoal", "fact": "TESTE_PYTEST_FACT carro azul"}
        r = client.post(f"{API}/long-memory", json=payload, timeout=15)
        assert r.status_code == 200, r.text
        d = r.json()
        assert "id" in d
        assert d["category"] == "pessoal"
        assert "TESTE_PYTEST_FACT" in d["fact"]
        TestLongMemory.fact_id = d["id"]

    def test_list_fact_contains(self, client):
        r = client.get(f"{API}/long-memory", timeout=15)
        assert r.status_code == 200
        ids = [f["id"] for f in r.json()]
        assert TestLongMemory.fact_id in ids

    def test_update_fact(self, client):
        fid = TestLongMemory.fact_id
        r = client.put(f"{API}/long-memory/{fid}",
                       json={"fact": "TESTE_PYTEST_FACT_UPDATED"}, timeout=15)
        assert r.status_code == 200
        # verifica
        r2 = client.get(f"{API}/long-memory", timeout=15)
        item = next(f for f in r2.json() if f["id"] == fid)
        assert "UPDATED" in item["fact"]

    def test_delete_fact(self, client):
        fid = TestLongMemory.fact_id
        r = client.delete(f"{API}/long-memory/{fid}", timeout=15)
        assert r.status_code == 200
        r2 = client.get(f"{API}/long-memory", timeout=15)
        ids = [f["id"] for f in r2.json()]
        assert fid not in ids


# -------------------- REMINDERS --------------------
class TestReminders:
    reminder_id = None
    natural_id = None

    def test_create_reminder(self, client):
        payload = {"text": "TESTE_PYTEST lembrete",
                   "when": "2030-01-01T12:00:00-03:00"}
        r = client.post(f"{API}/reminders", json=payload, timeout=15)
        assert r.status_code == 200, r.text
        d = r.json()
        assert "id" in d
        assert d["text"] == payload["text"]
        TestReminders.reminder_id = d["id"]

    def test_list_reminders(self, client):
        r = client.get(f"{API}/reminders", timeout=15)
        assert r.status_code == 200
        ids = [x["id"] for x in r.json()]
        assert TestReminders.reminder_id in ids

    def test_create_natural(self, client):
        r = client.post(f"{API}/reminders/natural",
                        json={"phrase": "TESTE_PYTEST me lembra de tomar agua amanha as 10h"},
                        timeout=60)
        assert r.status_code == 200, r.text
        d = r.json()
        assert "id" in d
        assert d["text"]
        assert d.get("when")
        TestReminders.natural_id = d["id"]

    def test_cleanup_reminders(self, client):
        for rid in (TestReminders.reminder_id, TestReminders.natural_id):
            if rid:
                r = client.delete(f"{API}/reminders/{rid}", timeout=15)
                assert r.status_code == 200


# -------------------- VISION --------------------
class TestVision:
    def test_vision_analyze(self, client):
        # Cria PNG mínimo 100x100 amarelo
        try:
            from PIL import Image
        except Exception:
            pytest.skip("PIL não instalado")
        img = Image.new("RGB", (100, 100), (255, 215, 0))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        files = {"file": ("test.png", buf, "image/png")}
        data = {"instruction": "describe in one short sentence"}
        # multipart -> remover header content-type json
        s = requests.Session()
        r = s.post(f"{API}/vision/analyze", files=files, data=data, timeout=90)
        assert r.status_code == 200, r.text
        d = r.json()
        assert "description" in d
        assert isinstance(d["description"], str)
        assert len(d["description"]) > 5


# -------------------- GOOGLE (esperado sem credenciais) --------------------
class TestGoogle:
    def test_google_status(self, client):
        r = client.get(f"{API}/google/status", timeout=15)
        assert r.status_code == 200
        d = r.json()
        # esperamos has_credenciais_json/has_token/ready (ou error)
        if "error" not in d:
            for k in ("has_credenciais_json", "has_token", "ready"):
                assert k in d, f"missing {k}: {d}"
            assert d["ready"] is False  # sem credenciais no container

    def test_google_calendar_today_no_creds(self, client):
        r = client.get(f"{API}/google/calendar/today", timeout=15)
        # esperado 400 (HTTPException) por falta de credenciais
        assert r.status_code in (400, 401, 500), r.text


# -------------------- CHAT com INTENTS --------------------
class TestChatIntents:
    created_fact_ids = []
    created_reminder_ids = []

    def test_intent_system_battery(self, client):
        r = client.post(f"{API}/chat",
                        json={"message": "qual a bateria do servidor?", "use_web": False},
                        timeout=60)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d.get("intent") == "system.battery"
        assert d.get("skill_result") is not None
        # skill_result.data contém status da bateria (pode ser sem bateria em servidor)
        sr = d["skill_result"]
        assert "data" in sr

    def test_intent_reminder_create(self, client):
        # snapshot
        before = client.get(f"{API}/reminders", timeout=15).json()
        before_ids = {x["id"] for x in before}
        r = client.post(f"{API}/chat",
                        json={"message": "TESTE_PYTEST me lembra de revisar relatório amanhã às 9h",
                              "use_web": False},
                        timeout=60)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d.get("intent") == "reminder.create"
        # busca o lembrete novo criado
        after = client.get(f"{API}/reminders", timeout=15).json()
        new = [x for x in after if x["id"] not in before_ids]
        # deve ter criado pelo menos um
        if d.get("skill_result", {}).get("data"):
            assert len(new) >= 1
            for x in new:
                TestChatIntents.created_reminder_ids.append(x["id"])
        # se a Gemini retornou error em extracted, o teste vira soft (skill_result.error)
        elif d.get("skill_result", {}).get("error"):
            pytest.skip(f"smart_extract não extraiu lembrete: {d['skill_result']}")

    def test_intent_memory_save_fact(self, client):
        before = client.get(f"{API}/long-memory", timeout=15).json()
        before_ids = {f["id"] for f in before}
        r = client.post(f"{API}/chat",
                        json={"message": "lembre disso: TESTE_PYTEST meu carro é um Onix preto placa ABC1234",
                              "use_web": False},
                        timeout=60)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d.get("intent") == "memory.save_fact"
        after = client.get(f"{API}/long-memory", timeout=15).json()
        new = [f for f in after if f["id"] not in before_ids]
        if d.get("skill_result", {}).get("data"):
            assert len(new) >= 1
            for f in new:
                TestChatIntents.created_fact_ids.append(f["id"])

    def test_intent_fallback_route(self, client):
        # casa->box = 35 km, deve cair no brain (sem intent match esperado)
        r = client.post(f"{API}/chat",
                        json={"message": "qual a distancia de casa pra box?", "use_web": False},
                        timeout=60)
        assert r.status_code == 200, r.text
        d = r.json()
        assert "35" in d["reply"], f"esperava 35 km. Got: {d['reply']}"

    def test_cleanup_chat_artifacts(self, client):
        for fid in TestChatIntents.created_fact_ids:
            client.delete(f"{API}/long-memory/{fid}", timeout=15)
        for rid in TestChatIntents.created_reminder_ids:
            client.delete(f"{API}/reminders/{rid}", timeout=15)


# -------------------- CONFIG personality --------------------
class TestConfigPersonality:
    def test_patch_to_casual_and_revert(self, client):
        # patch
        r = client.patch(f"{API}/config", json={"personality": "casual"}, timeout=15)
        assert r.status_code == 200
        # confirm
        g = client.get(f"{API}/config", timeout=15).json()
        assert g["personality"] == "casual"
        # status também reflete
        s = client.get(f"{API}/status", timeout=15).json()
        assert s["personality"] == "casual"
        # revert
        r2 = client.patch(f"{API}/config", json={"personality": "corporativa"}, timeout=15)
        assert r2.status_code == 200
        g2 = client.get(f"{API}/config", timeout=15).json()
        assert g2["personality"] == "corporativa"
