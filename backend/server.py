"""
S.E.X.T.A - F.E.I.R.A (MAVIS) - Web Control Panel Backend
FastAPI server expondo o cérebro neural, banco de rotas, memória e relatórios.
"""
import os
import json
import asyncio
import logging
import uuid
import io
import tempfile
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from pathlib import Path

from fastapi import FastAPI, APIRouter, HTTPException, WebSocket, WebSocketDisconnect, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

# ---------- Configuração ----------
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

MONGO_URL = os.environ["MONGO_URL"]
DB_NAME = os.environ["DB_NAME"]
CHAVE_GEMINI = os.environ.get("CHAVE_GEMINI", "")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
NOME_IA = os.environ.get("NOME_IA", "Sexta-feira")
VOZ_SINTETIZADOR = os.environ.get("VOZ_SINTETIZADOR", "pt-BR-ThalitaNeural")

ARQUIVO_MEMORIA = os.environ.get("ARQUIVO_MEMORIA", "/app/memoria_mavis.json")
ARQUIVO_DB = os.environ.get("ARQUIVO_DB", "/app/banco_de_dados.json")
ARQUIVO_RELATORIOS = os.environ.get("ARQUIVO_RELATORIOS", "/app/banco_relatorios.json")

# ---------- Logging ----------
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("sexta-feira")

# Buffer circular de logs para o painel (WebSocket)
LOG_BUFFER: List[Dict[str, Any]] = []
LOG_BUFFER_MAX = 500
WS_CLIENTS: List[WebSocket] = []


def push_log(level: str, message: str, source: str = "system"):
    entry = {
        "id": str(uuid.uuid4()),
        "ts": datetime.now(timezone.utc).isoformat(),
        "level": level.upper(),
        "source": source,
        "message": message,
    }
    LOG_BUFFER.append(entry)
    if len(LOG_BUFFER) > LOG_BUFFER_MAX:
        del LOG_BUFFER[: len(LOG_BUFFER) - LOG_BUFFER_MAX]
    # Broadcast para WS
    for ws in list(WS_CLIENTS):
        try:
            asyncio.create_task(ws.send_json(entry))
        except Exception:
            pass
    return entry


# ---------- Banco Mongo (sessões / metadata) ----------
mongo_client = AsyncIOMotorClient(MONGO_URL)
db = mongo_client[DB_NAME]

# ---------- App ----------
app = FastAPI(title="S.E.X.T.A - F.E.I.R.A Control Panel", version="2.0")
api = APIRouter(prefix="/api")

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- Helpers de arquivos JSON ----------
def _read_json(path: str, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"Falha ao ler {path}: {e}")
        return default


def _write_json(path: str, data):
    tmp_path = path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    os.replace(tmp_path, path)


# ---------- Modelos Pydantic ----------
class ChatRequest(BaseModel):
    message: str
    use_web: bool = True


class ChatResponse(BaseModel):
    reply: str
    espera_resposta: bool = False
    contexto_externo: Optional[str] = None
    duration_ms: int = 0


class TtsRequest(BaseModel):
    text: str
    voice: Optional[str] = None


class Route(BaseModel):
    origem: str
    destino: str
    km: float


class RouteUpdate(BaseModel):
    km: float


class Report(BaseModel):
    id: Optional[str] = None
    periodo: str
    conteudo_relatorio: str
    gerado_em: Optional[str] = None


class ConfigUpdate(BaseModel):
    voz_sintetizador: Optional[str] = None
    nome_ia: Optional[str] = None
    pause_threshold: Optional[float] = None


# ==============================================================
# HEALTH / STATUS
# ==============================================================
@api.get("/health")
async def health():
    return {"status": "ok", "service": NOME_IA, "ts": datetime.now(timezone.utc).isoformat()}


@api.get("/status")
async def status():
    memoria = _read_json(ARQUIVO_MEMORIA, [])
    db_data = _read_json(ARQUIVO_DB, {"rotas_km": {}})
    relatorios = _read_json(ARQUIVO_RELATORIOS, [])
    return {
        "ia": NOME_IA,
        "modelo": GEMINI_MODEL,
        "voz": VOZ_SINTETIZADOR,
        "gemini_configurado": bool(CHAVE_GEMINI),
        "total_rotas": len(db_data.get("rotas_km", {})),
        "total_memorias": len(memoria),
        "total_relatorios": len(relatorios),
        "uptime_iso": datetime.now(timezone.utc).isoformat(),
    }


# ==============================================================
# CHAT (CÉREBRO NEURAL)
# ==============================================================
def _build_prompt(comando: str, historico: list, banco_str: str, contexto_externo: str = ""):
    instrucoes = f"""Você é a {NOME_IA}, uma inteligência artificial corporativa avançada estilo J.A.R.V.I.S.

REGRAS DE OURO (siga rigorosamente):
1. Respostas ágeis, conversacionais e diretas. Vá ao ponto.
2. Sempre se dirija ao usuário como 'senhor'.
3. Proibido emojis, asteriscos (**), markdown ou formatação visual exagerada.
4. Se fizer uma pergunta de retorno ao usuário, termine EXATAMENTE com a tag [ESPERAR].
5. Você TEM acesso ao banco de dados de rotas KM abaixo. Quando perguntarem sobre distâncias, rotas ou KM entre pontos, CONSULTE o banco e responda com o valor exato. NÃO diga que "não pode consultar" se o dado existe.
6. Quando o usuário disser comandos como "aprender rotas", "atualizar planilha", "gerar relatório", "preencher quilometragem" - apenas confirme que vai disparar o protocolo. O sistema externo executa.
7. Tom corporativo, sóbrio, eficiente.

BANCO DE DADOS DE ROTAS (formato ORIGEM_DESTINO: KM):
{banco_str}
"""
    conversa = instrucoes + "\n\n=== HISTÓRICO ===\n"
    for msg in historico[-12:]:
        conversa += f"{msg['role']}: {msg['texto']}\n"
    if contexto_externo:
        conversa += f"\n[DADO EM TEMPO REAL DA WEB]:\n{contexto_externo}\n"
    conversa += f"\nUsuário: {comando}\n{NOME_IA}: "
    return conversa


async def _busca_web(query: str) -> str:
    try:
        from duckduckgo_search import DDGS
        loop = asyncio.get_event_loop()

        def _go():
            try:
                results = DDGS().text(query, region="br-pt", safesearch="moderate", max_results=2)
                out = ""
                for r in results:
                    out += f"- {r.get('title','')}: {r.get('body','')}\n"
                return out.strip()
            except Exception as e:
                return f"(falha na busca: {e})"

        return await loop.run_in_executor(None, _go)
    except Exception as e:
        return f"(busca indisponível: {e})"


@api.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    inicio = datetime.now()
    if not CHAVE_GEMINI:
        raise HTTPException(500, "CHAVE_GEMINI não configurada no .env")

    comando = req.message.strip()
    if not comando:
        raise HTTPException(400, "Mensagem vazia")

    push_log("info", f"USR > {comando}", "chat")

    memoria = _read_json(ARQUIVO_MEMORIA, [])
    db_raw = _read_json(ARQUIVO_DB, {"rotas_km": {}})
    banco_str = json.dumps(db_raw, ensure_ascii=False)

    # Decisão: busca web?
    contexto_externo = ""
    palavras_realtime = ["hoje", "agora", "notícia", "noticia", "clima", "tempo", "dólar",
                         "dolar", "previsão", "previsao", "temperatura", "cotação", "cotacao"]
    if req.use_web and any(p in comando.lower() for p in palavras_realtime):
        push_log("info", "Acessando rede global (DuckDuckGo)...", "chat")
        contexto_externo = await _busca_web(comando)

    prompt = _build_prompt(comando, memoria, banco_str, contexto_externo)

    try:
        from google import genai
        client = genai.Client(api_key=CHAVE_GEMINI)
        loop = asyncio.get_event_loop()
        resposta = await loop.run_in_executor(
            None, lambda: client.models.generate_content(model=GEMINI_MODEL, contents=prompt)
        )
        texto = (resposta.text or "").strip()
    except Exception as e:
        push_log("error", f"Falha Gemini: {e}", "chat")
        raise HTTPException(500, f"Falha no cérebro neural: {e}")

    espera = False
    if "[ESPERAR]" in texto:
        espera = True
        texto = texto.replace("[ESPERAR]", "").strip()
    elif texto.endswith("?"):
        espera = True

    memoria.append({"role": "Usuário", "texto": comando})
    memoria.append({"role": NOME_IA, "texto": texto})
    _write_json(ARQUIVO_MEMORIA, memoria[-30:])

    push_log("info", f"SYS > {texto[:120]}{'...' if len(texto)>120 else ''}", "chat")
    duration = int((datetime.now() - inicio).total_seconds() * 1000)
    return ChatResponse(reply=texto, espera_resposta=espera,
                        contexto_externo=contexto_externo or None, duration_ms=duration)


# ==============================================================
# TTS (Edge TTS – Voz Neural Premium gratuita)
# ==============================================================
@api.post("/tts")
async def tts(req: TtsRequest):
    import edge_tts
    voice = req.voice or VOZ_SINTETIZADOR
    if not req.text.strip():
        raise HTTPException(400, "Texto vazio")
    try:
        communicate = edge_tts.Communicate(req.text, voice)
        buf = io.BytesIO()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                buf.write(chunk["data"])
        audio_bytes = buf.getvalue()
        if not audio_bytes:
            raise HTTPException(500, "Edge TTS retornou áudio vazio")
        return Response(content=audio_bytes, media_type="audio/mpeg",
                        headers={"Cache-Control": "no-store"})
    except Exception as e:
        push_log("error", f"TTS falhou: {e}", "tts")
        raise HTTPException(500, f"Falha no sintetizador: {e}")


@api.get("/tts/voices")
async def tts_voices():
    import edge_tts
    voices = await edge_tts.list_voices()
    ptbr = [v for v in voices if v.get("Locale", "").startswith("pt-")]
    return [
        {"short_name": v["ShortName"], "gender": v["Gender"], "locale": v["Locale"]}
        for v in ptbr
    ]


# ==============================================================
# MEMÓRIA (conversas)
# ==============================================================
@api.get("/memory")
async def get_memory():
    return _read_json(ARQUIVO_MEMORIA, [])


@api.delete("/memory")
async def clear_memory():
    _write_json(ARQUIVO_MEMORIA, [])
    push_log("warn", "Memória de conversas apagada", "memory")
    return {"ok": True}


# ==============================================================
# ROTAS (banco_de_dados.json)
# ==============================================================
@api.get("/routes")
async def list_routes(q: Optional[str] = None):
    data = _read_json(ARQUIVO_DB, {"rotas_km": {}})
    rotas = data.get("rotas_km", {})
    items = []
    for chave, km in rotas.items():
        if "_" in chave:
            partes = chave.split("_", 1)
            origem, destino = partes[0], partes[1]
        else:
            origem, destino = chave, ""
        if q:
            ql = q.lower()
            if ql not in origem.lower() and ql not in destino.lower():
                continue
        items.append({"key": chave, "origem": origem, "destino": destino, "km": km})
    items.sort(key=lambda x: (x["origem"], x["destino"]))
    return {"total": len(items), "items": items}


@api.post("/routes")
async def add_route(route: Route):
    data = _read_json(ARQUIVO_DB, {"rotas_km": {}})
    if "rotas_km" not in data:
        data["rotas_km"] = {}
    chave = f"{route.origem.strip().upper()}_{route.destino.strip().upper()}"
    km = int(route.km) if float(route.km).is_integer() else route.km
    data["rotas_km"][chave] = km
    _write_json(ARQUIVO_DB, data)
    push_log("info", f"Rota adicionada: {chave} = {km} km", "routes")
    return {"ok": True, "key": chave, "km": km}


@api.put("/routes/{key}")
async def update_route(key: str, body: RouteUpdate):
    data = _read_json(ARQUIVO_DB, {"rotas_km": {}})
    if key not in data.get("rotas_km", {}):
        raise HTTPException(404, "Rota não encontrada")
    km = int(body.km) if float(body.km).is_integer() else body.km
    data["rotas_km"][key] = km
    _write_json(ARQUIVO_DB, data)
    push_log("info", f"Rota atualizada: {key} = {km} km", "routes")
    return {"ok": True}


@api.delete("/routes/{key}")
async def delete_route(key: str):
    data = _read_json(ARQUIVO_DB, {"rotas_km": {}})
    if key not in data.get("rotas_km", {}):
        raise HTTPException(404, "Rota não encontrada")
    del data["rotas_km"][key]
    _write_json(ARQUIVO_DB, data)
    push_log("warn", f"Rota removida: {key}", "routes")
    return {"ok": True}


# ==============================================================
# RELATÓRIOS (banco_relatorios.json)
# ==============================================================
@api.get("/reports")
async def list_reports():
    data = _read_json(ARQUIVO_RELATORIOS, [])
    out = []
    for i, r in enumerate(data):
        out.append({
            "id": r.get("id", str(i)),
            "periodo": r.get("periodo", ""),
            "gerado_em": r.get("gerado_em", ""),
            "preview": (r.get("conteudo_relatorio", "")[:280]).strip(),
        })
    out.reverse()  # mais recente primeiro
    return out


@api.get("/reports/{report_id}")
async def get_report(report_id: str):
    data = _read_json(ARQUIVO_RELATORIOS, [])
    for i, r in enumerate(data):
        rid = r.get("id", str(i))
        if rid == report_id:
            return {**r, "id": rid}
    raise HTTPException(404, "Relatório não encontrado")


@api.post("/reports")
async def add_report(report: Report):
    data = _read_json(ARQUIVO_RELATORIOS, [])
    new = {
        "id": report.id or str(uuid.uuid4()),
        "gerado_em": report.gerado_em or datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "periodo": report.periodo,
        "conteudo_relatorio": report.conteudo_relatorio,
    }
    data.append(new)
    _write_json(ARQUIVO_RELATORIOS, data)
    push_log("info", f"Relatório adicionado: {report.periodo}", "reports")
    return new


@api.delete("/reports/{report_id}")
async def delete_report(report_id: str):
    data = _read_json(ARQUIVO_RELATORIOS, [])
    novos = []
    removido = False
    for i, r in enumerate(data):
        rid = r.get("id", str(i))
        if rid == report_id:
            removido = True
            continue
        novos.append(r)
    if not removido:
        raise HTTPException(404, "Relatório não encontrado")
    _write_json(ARQUIVO_RELATORIOS, novos)
    push_log("warn", f"Relatório removido: {report_id}", "reports")
    return {"ok": True}


# ==============================================================
# COMANDOS (gatilhos manuais)
# ==============================================================
class CommandRequest(BaseModel):
    command: str  # texto livre, será roteado igual ao desktop


@api.post("/commands/execute")
async def execute_command(req: CommandRequest):
    """
    Executa o roteador local (similar ao rotinas.executar_rotina_local do desktop).
    Operações RPA pesadas (FieldControl/WhatsApp) e Sheets que dependem de
    credenciais Google e navegador visual NÃO rodam neste container — retornam
    instrução clara. Apenas comandos seguros são executados.
    """
    cmd = req.command.lower().strip()
    push_log("info", f"CMD > {cmd}", "commands")

    if any(x in cmd for x in ["aprender rotas", "estudar rotas"]):
        return {"status": "skipped",
                "message": "Aprendizado de rotas requer credenciais Google (credenciais.json) e roda no app desktop."}

    if any(x in cmd for x in ["atualizar planilha", "preencher quilometragem",
                              "fazer planilha", "preencher planilha"]):
        return {"status": "skipped",
                "message": "Atualização da planilha Google só roda no app desktop (precisa do credenciais.json local)."}

    if any(x in cmd for x in ["gerar relatório", "resumo da semana", "gerar relatorio"]):
        return {"status": "skipped",
                "message": "Geração de relatório usa Playwright em modo visual (FieldControl). Rode no desktop."}

    # Comando livre: trata como chat
    resposta = await chat(ChatRequest(message=req.command))
    return {"status": "chat", "reply": resposta.reply, "espera": resposta.espera_resposta}


# ==============================================================
# LOGS
# ==============================================================
@api.get("/logs")
async def get_logs(limit: int = 100):
    return LOG_BUFFER[-limit:]


@app.websocket("/api/logs/stream")
async def logs_ws(websocket: WebSocket):
    await websocket.accept()
    WS_CLIENTS.append(websocket)
    try:
        # Envia buffer inicial
        for e in LOG_BUFFER[-50:]:
            await websocket.send_json(e)
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        if websocket in WS_CLIENTS:
            WS_CLIENTS.remove(websocket)


# ==============================================================
# CONFIG
# ==============================================================
@api.get("/config")
async def get_config():
    return {
        "nome_ia": NOME_IA,
        "modelo_gemini": GEMINI_MODEL,
        "voz": VOZ_SINTETIZADOR,
        "pause_threshold": float(os.environ.get("PAUSE_THRESHOLD", "1.0")),
        "tem_chave_gemini": bool(CHAVE_GEMINI),
        "chave_gemini_mask": (CHAVE_GEMINI[:6] + "..." + CHAVE_GEMINI[-4:]) if CHAVE_GEMINI else "",
        "whatsapp_grupo": os.environ.get("WHATSAPP_GRUPO", ""),
        "fieldcontrol_email": os.environ.get("FIELDCONTROL_EMAIL", ""),
    }


# ==============================================================
# Inclui o router
# ==============================================================
app.include_router(api)


@app.on_event("startup")
async def startup():
    push_log("info", f"{NOME_IA} online. Núcleo cognitivo Gemini {GEMINI_MODEL}.", "system")
    push_log("info", f"Voz neural: {VOZ_SINTETIZADOR}", "system")


@app.on_event("shutdown")
async def shutdown():
    mongo_client.close()
