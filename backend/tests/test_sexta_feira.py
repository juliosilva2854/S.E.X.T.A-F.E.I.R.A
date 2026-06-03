"""
Backend tests for S.E.X.T.A - F.E.I.R.A (MAVIS) Web Control Panel.
Covers: health, status, chat (Gemini), TTS (Edge), routes CRUD, reports CRUD,
memory, logs, config and commands router.

IMPORTANT: Não-destrutivo. Cria/limpa apenas dados com prefixo TESTE_*.
NÃO deleta memoria_mavis.json real nem rotas/relatórios pré-existentes.
"""
import os
import json
import time
import uuid
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://ai-assistant-hub-472.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"


@pytest.fixture(scope="module")
def client():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


# -------------------- HEALTH / STATUS --------------------
class TestHealth:
    def test_health(self, client):
        r = client.get(f"{API}/health", timeout=15)
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "ok"
        assert data["service"] == "Sexta-feira"

    def test_status(self, client):
        r = client.get(f"{API}/status", timeout=15)
        assert r.status_code == 200
        d = r.json()
        assert d["ia"] == "Sexta-feira"
        assert d["modelo"] == "gemini-2.5-flash"
        assert d["gemini_configurado"] is True
        assert isinstance(d["total_rotas"], int) and d["total_rotas"] >= 200
        assert isinstance(d["total_memorias"], int)
        assert isinstance(d["total_relatorios"], int)


# -------------------- CONFIG --------------------
class TestConfig:
    def test_config(self, client):
        r = client.get(f"{API}/config", timeout=15)
        assert r.status_code == 200
        d = r.json()
        assert d["nome_ia"] == "Sexta-feira"
        assert d["modelo_gemini"] == "gemini-2.5-flash"
        assert d["tem_chave_gemini"] is True
        assert "..." in d["chave_gemini_mask"]


# -------------------- CHAT (Gemini) --------------------
class TestChat:
    def test_chat_distancia_casa_box(self, client):
        # Captura memória atual
        m_before = client.get(f"{API}/memory", timeout=15).json()
        before_count = len(m_before)

        r = client.post(f"{API}/chat", json={
            "message": "qual a distancia de casa pra box?",
            "use_web": False
        }, timeout=60)
        assert r.status_code == 200, r.text
        d = r.json()
        assert "reply" in d
        assert "35" in d["reply"], f"Esperava km '35' (CASA_BOX:35) na resposta. Got: {d['reply']}"

        # Persistência: deve adicionar 2 mensagens (user + assistant)
        m_after = client.get(f"{API}/memory", timeout=15).json()
        assert len(m_after) >= before_count + 1  # memória limita a 30, pode ser >=

    def test_chat_pergunta_marca_espera(self, client):
        # Mensagem aberta - resposta pode ou não terminar em "?"
        r = client.post(f"{API}/chat", json={
            "message": "olá, tudo bem?",
            "use_web": False
        }, timeout=60)
        assert r.status_code == 200
        d = r.json()
        # [ESPERAR] não deve aparecer no texto retornado (foi removido)
        assert "[ESPERAR]" not in d["reply"]
        assert isinstance(d["espera_resposta"], bool)

    def test_chat_empty_message(self, client):
        r = client.post(f"{API}/chat", json={"message": "", "use_web": False}, timeout=15)
        assert r.status_code == 400


# -------------------- TTS (Edge) --------------------
class TestTts:
    def test_tts_synthesis(self, client):
        r = client.post(f"{API}/tts", json={"text": "Pronta para operar, senhor."}, timeout=30)
        assert r.status_code == 200, r.text
        assert r.headers.get("content-type", "").startswith("audio/")
        assert len(r.content) > 5000, f"áudio muito pequeno: {len(r.content)}"

    def test_tts_voices(self, client):
        r = client.get(f"{API}/tts/voices", timeout=30)
        assert r.status_code == 200
        voices = r.json()
        assert isinstance(voices, list)
        ptbr = [v for v in voices if v["locale"].startswith("pt-BR")]
        assert len(ptbr) >= 2  # pt-BR ao menos algumas vozes
        # garante ThalitaNeural presente
        assert any("Thalita" in v["short_name"] for v in voices)

    def test_tts_empty_text(self, client):
        r = client.post(f"{API}/tts", json={"text": ""}, timeout=15)
        assert r.status_code == 400


# -------------------- ROUTES --------------------
class TestRoutes:
    def test_list_routes_filter(self, client):
        r = client.get(f"{API}/routes?q=CASA", timeout=15)
        assert r.status_code == 200
        d = r.json()
        assert "items" in d and "total" in d
        assert d["total"] > 0
        for it in d["items"]:
            assert "CASA" in it["origem"].upper() or "CASA" in it["destino"].upper()

    def test_route_crud_full(self, client):
        # CREATE (using single-word origem/destino to avoid split("_",1) ambiguity)
        r = client.post(f"{API}/routes", json={
            "origem": "TESTEA", "destino": "TESTEB", "km": 99
        }, timeout=15)
        assert r.status_code == 200
        d = r.json()
        assert d["ok"] is True
        # key real (server faz upper + monta com underscore entre origem/destino)
        created_key = d["key"]
        assert created_key == "TESTEA_TESTEB"
        assert d["km"] == 99

        # VERIFY via list
        r2 = client.get(f"{API}/routes?q=TESTEA", timeout=15)
        keys = [it["key"] for it in r2.json()["items"]]
        assert created_key in keys

        # UPDATE
        r3 = client.put(f"{API}/routes/{created_key}", json={"km": 123}, timeout=15)
        assert r3.status_code == 200

        r4 = client.get(f"{API}/routes?q=TESTEA", timeout=15)
        item = next((i for i in r4.json()["items"] if i["key"] == created_key), None)
        assert item is not None
        assert item["km"] == 123

        # DELETE (cleanup)
        r5 = client.delete(f"{API}/routes/{created_key}", timeout=15)
        assert r5.status_code == 200

        # Confirm removal
        r6 = client.get(f"{API}/routes?q=TESTEA", timeout=15)
        keys = [it["key"] for it in r6.json()["items"]]
        assert created_key not in keys

    def test_route_update_404(self, client):
        r = client.put(f"{API}/routes/NAOEXISTE_XYZ", json={"km": 1}, timeout=15)
        assert r.status_code == 404

    def test_route_delete_404(self, client):
        r = client.delete(f"{API}/routes/NAOEXISTE_XYZ", timeout=15)
        assert r.status_code == 404


# -------------------- REPORTS --------------------
class TestReports:
    def test_list_reports(self, client):
        r = client.get(f"{API}/reports", timeout=15)
        assert r.status_code == 200
        lst = r.json()
        assert isinstance(lst, list)
        # 4 relatórios reais existem
        assert len(lst) >= 1
        if lst:
            assert "id" in lst[0]
            assert "periodo" in lst[0]
            assert "preview" in lst[0]

    def test_report_crud_full(self, client):
        # CREATE
        payload = {
            "periodo": "TESTE_PERIODO_PYTEST",
            "conteudo_relatorio": "Conteúdo de teste gerado por pytest. " + str(uuid.uuid4()),
        }
        r = client.post(f"{API}/reports", json=payload, timeout=15)
        assert r.status_code == 200
        new = r.json()
        assert "id" in new
        assert new["periodo"] == payload["periodo"]
        rid = new["id"]

        # VERIFY via GET by id
        r2 = client.get(f"{API}/reports/{rid}", timeout=15)
        assert r2.status_code == 200
        assert r2.json()["periodo"] == payload["periodo"]

        # DELETE
        r3 = client.delete(f"{API}/reports/{rid}", timeout=15)
        assert r3.status_code == 200

        # 404 after delete
        r4 = client.get(f"{API}/reports/{rid}", timeout=15)
        assert r4.status_code == 404


# -------------------- MEMORY --------------------
class TestMemory:
    def test_get_memory(self, client):
        r = client.get(f"{API}/memory", timeout=15)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    # NÃO testa DELETE /api/memory para não corromper dados reais.


# -------------------- LOGS --------------------
class TestLogs:
    def test_logs(self, client):
        r = client.get(f"{API}/logs?limit=20", timeout=15)
        assert r.status_code == 200
        logs = r.json()
        assert isinstance(logs, list)
        if logs:
            e = logs[0]
            for k in ["id", "ts", "level", "source", "message"]:
                assert k in e


# -------------------- COMMANDS --------------------
class TestCommands:
    def test_command_aprender_rotas_skipped(self, client):
        r = client.post(f"{API}/commands/execute", json={"command": "aprender rotas"}, timeout=15)
        assert r.status_code == 200
        d = r.json()
        assert d["status"] == "skipped"
        assert "desktop" in d["message"].lower()

    def test_command_chat_freeform(self, client):
        r = client.post(f"{API}/commands/execute", json={
            "command": "qual a distancia entre upa pedreira e casa?"
        }, timeout=60)
        assert r.status_code == 200
        d = r.json()
        assert d["status"] == "chat"
        assert "reply" in d
        # deve conter algum número (km) na resposta
        assert any(ch.isdigit() for ch in d["reply"]), f"sem número na resposta: {d['reply']}"
