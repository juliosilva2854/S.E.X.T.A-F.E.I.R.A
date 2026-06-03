"""
S.E.X.T.A - F.E.I.R.A (MAVIS) v3.0 — Web Control Panel Backend
FastAPI server expondo cérebro neural, visão, memória longa, lembretes,
Google ecosystem (Calendar/Gmail/Drive) e skills do sistema.
"""
import os
import sys
import json
import asyncio
import logging
import uuid
import io
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
from pathlib import Path

from fastapi import FastAPI, APIRouter, HTTPException, WebSocket, WebSocketDisconnect, Response, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

# ---------- Configuração ----------
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

# Permite importar o pacote mavis/ (que vive em /app/mavis)
sys.path.insert(0, str(ROOT_DIR.parent))

from mavis.core import storage as _storage
from mavis.core import long_memory as lm_core
from mavis.core import reminders as rem_core
from mavis.core import brain as brain_core
from mavis.core import router as router_core
from mavis.core.paths import (
    ARQUIVO_MEMORIA, ARQUIVO_DB_ROTAS, ARQUIVO_RELATORIOS,
    ARQUIVO_TOKEN_GOOGLE, ARQUIVO_CREDENCIAIS_GOOGLE,
)
from mavis.skills import system_info as sys_skill
from mavis.skills import news_weather as nw_skill
from mavis.skills import scheduler as sched_skill

MONGO_URL = os.environ["MONGO_URL"]
DB_NAME = os.environ["DB_NAME"]
CHAVE_GEMINI = os.environ.get("CHAVE_GEMINI", "")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
NOME_IA = os.environ.get("NOME_IA", "Sexta-feira")
VOZ_SINTETIZADOR = os.environ.get("VOZ_SINTETIZADOR", "pt-BR-ThalitaNeural")

# ---------- Logging ----------
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("sexta-feira")

LOG_BUFFER: List[Dict[str, Any]] = []
LOG_BUFFER_MAX = 500
WS_CLIENTS: List[WebSocket] = []
MAIN_LOOP: Optional[asyncio.AbstractEventLoop] = None


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
    for ws in list(WS_CLIENTS):
        try:
            if MAIN_LOOP and MAIN_LOOP.is_running():
                asyncio.run_coroutine_threadsafe(ws.send_json(entry), MAIN_LOOP)
        except Exception:
            pass
    return entry


# ---------- Banco Mongo (sessões / metadata) ----------
mongo_client = AsyncIOMotorClient(MONGO_URL)
db = mongo_client[DB_NAME]

# ---------- App ----------
app = FastAPI(title="S.E.X.T.A - F.E.I.R.A Control Panel", version="3.0")
api = APIRouter(prefix="/api")

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==============================================================
# MODELOS
# ==============================================================
class ChatRequest(BaseModel):
    message: str
    use_web: bool = True


class ChatResponse(BaseModel):
    reply: str
    espera_resposta: bool = False
    intent: Optional[str] = None
    skill_result: Optional[Any] = None
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


class FactIn(BaseModel):
    category: str
    fact: str


class FactUpdate(BaseModel):
    category: Optional[str] = None
    fact: Optional[str] = None


class ReminderIn(BaseModel):
    text: str
    when: str  # ISO date or natural "amanha 14h" (será parseado)
    recurrence: Optional[str] = None


class ReminderNatural(BaseModel):
    phrase: str  # ex: "me lembra de tomar remédio amanhã às 8 da manhã"


class CommandRequest(BaseModel):
    command: str


# ==============================================================
# HEALTH / STATUS
# ==============================================================
@api.get("/health")
async def health():
    return {"status": "ok", "service": NOME_IA, "ts": datetime.now(timezone.utc).isoformat()}


@api.get("/status")
async def status():
    memoria = _storage.read_json(ARQUIVO_MEMORIA, [])
    db_data = _storage.read_json(ARQUIVO_DB_ROTAS, {"rotas_km": {}})
    relatorios = _storage.read_json(ARQUIVO_RELATORIOS, [])
    facts = lm_core.list_facts()
    rems = rem_core.list_reminders(only_active=True)

    google_ready = os.path.exists(ARQUIVO_CREDENCIAIS_GOOGLE) and os.path.exists(ARQUIVO_TOKEN_GOOGLE)
    return {
        "ia": NOME_IA,
        "modelo": GEMINI_MODEL,
        "voz": VOZ_SINTETIZADOR,
        "personality": os.environ.get("MAVIS_PERSONALITY", "corporativa"),
        "gemini_configurado": bool(CHAVE_GEMINI),
        "google_ready": google_ready,
        "total_rotas": len(db_data.get("rotas_km", {})),
        "total_memorias": len(memoria),
        "total_relatorios": len(relatorios),
        "total_facts": len(facts),
        "total_reminders": len(rems),
        "uptime_iso": datetime.now(timezone.utc).isoformat(),
    }


# ==============================================================
# CHAT (Cérebro com roteamento de skills)
# ==============================================================
async def _execute_skill(intent: str, raw_text: str) -> Dict[str, Any]:
    """Executa skill server-side. Skills desktop-only retornam {desktop_only: True}."""
    try:
        if intent in ("computer.open_app", "computer.close_app", "computer.screenshot",
                      "computer.type_text", "system.shutdown", "system.lock",
                      "media.play", "media.pause", "media.next",
                      "whatsapp.read_unread", "whatsapp.send",
                      "vision.read_screen", "route.legacy"):
            return {"desktop_only": True, "message": "Operação requer execução no app desktop."}

        if intent == "system.battery":
            return {"data": sys_skill.battery()}
        if intent == "system.cpu":
            return {"data": sys_skill.cpu()}
        if intent == "system.ram":
            return {"data": sys_skill.ram()}

        if intent == "news.headlines":
            return {"data": nw_skill.headlines("g1", 5)}
        if intent == "weather.today":
            return {"data": nw_skill.weather()}

        if intent == "calendar.today":
            from mavis.skills import google_calendar as gc
            return {"data": gc.list_today()}
        if intent == "calendar.week":
            from mavis.skills import google_calendar as gc
            return {"data": gc.list_week()}
        if intent == "calendar.create":
            extracted = brain_core.smart_extract(
                raw_text,
                'Schema: {"summary": str, "start_iso": "YYYY-MM-DDTHH:MM:SS-03:00", '
                '"end_iso": str|null, "location": str|null, "description": str|null}. '
                'Se faltar informação, use null.'
            )
            if not extracted.get("summary") or not extracted.get("start_iso"):
                return {"error": "Não consegui extrair título/horário do evento."}
            from mavis.skills import google_calendar as gc
            return {"data": gc.create_event(
                extracted["summary"], extracted["start_iso"],
                extracted.get("end_iso"), extracted.get("description") or "",
                extracted.get("location") or ""
            )}

        if intent == "gmail.unread":
            from mavis.skills import google_gmail as gm
            return {"data": gm.list_unread(10)}
        if intent == "gmail.summary":
            from mavis.skills import google_gmail as gm
            return {"data": gm.summarize_unread(5)}

        if intent == "drive.search":
            from mavis.skills import google_drive as gd
            # Extrai termo após "drive"
            term = raw_text.lower().split("drive", 1)[-1].strip().replace("?", "")
            term = term.replace("no", "").replace("o", "").strip() or raw_text
            return {"data": gd.search(term, 10)}

        if intent == "reminder.create":
            extracted = brain_core.smart_extract(
                raw_text,
                'Schema: {"text": str, "when_iso": "YYYY-MM-DDTHH:MM:SS-03:00", '
                '"recurrence": "daily"|"weekly"|"monthly"|null}. '
                'Hoje no fuso de São Paulo. Se a frase disser "amanhã às 8", use a data de amanhã às 08:00.'
            )
            if not extracted.get("text") or not extracted.get("when_iso"):
                return {"error": "Não entendi o lembrete. Tente: 'me lembra de X amanhã às 8h'."}
            r = rem_core.add_reminder(extracted["text"], extracted["when_iso"], extracted.get("recurrence"))
            return {"data": r}

        if intent == "reminder.list":
            return {"data": rem_core.list_reminders(only_active=True)}

        if intent == "memory.save_fact":
            extracted = brain_core.smart_extract(
                raw_text,
                'Schema: {"category": "pessoal"|"preferencia"|"trabalho"|"contato"|"lugar"|"agenda"|"outro", "fact": str}. '
                'Extraia o fato a ser memorizado.'
            )
            if not extracted.get("fact"):
                return {"error": "Não entendi o fato."}
            f = lm_core.add_fact(extracted.get("category", "outro"), extracted["fact"])
            return {"data": f}

        return {"unhandled": True}
    except Exception as e:
        return {"error": str(e)}


@api.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    inicio = datetime.now()
    if not CHAVE_GEMINI:
        raise HTTPException(500, "CHAVE_GEMINI não configurada")

    comando = req.message.strip()
    if not comando:
        raise HTTPException(400, "Mensagem vazia")
    push_log("info", f"USR > {comando}", "chat")

    # 1) Tenta roteamento por intent
    matched = router_core.match_intent(comando)
    skill_result = None
    intent_name = None
    extra_ctx = ""

    if matched:
        intent_name = matched["intent"]
        push_log("info", f"INTENT > {intent_name}", "router")
        skill_result = await _execute_skill(intent_name, comando)
        if skill_result:
            extra_ctx = (
                f"[RESULTADO DA SKILL '{intent_name}']:\n"
                f"{json.dumps(skill_result, ensure_ascii=False, default=str)}\n"
                "Use esse dado para responder ao operador de forma natural e útil. "
                "Se o resultado disser 'desktop_only', informe que vai executar no app desktop."
            )

    # 2) Chama cérebro
    loop = asyncio.get_event_loop()
    reply, espera = await loop.run_in_executor(
        None,
        lambda: brain_core.chat_text(
            comando, extra_context=extra_ctx, use_web=req.use_web,
        ),
    )

    push_log("info", f"SYS > {reply[:140]}", "chat")
    duration = int((datetime.now() - inicio).total_seconds() * 1000)
    return ChatResponse(
        reply=reply,
        espera_resposta=espera,
        intent=intent_name,
        skill_result=skill_result,
        duration_ms=duration,
    )


# ==============================================================
# VISION (recebe imagem upload e analisa)
# ==============================================================
@api.post("/vision/analyze")
async def vision_analyze(file: UploadFile = File(...), instruction: str = Form("Descreva o que está nesta imagem.")):
    image_bytes = await file.read()
    if not image_bytes:
        raise HTTPException(400, "imagem vazia")
    loop = asyncio.get_event_loop()
    text = await loop.run_in_executor(
        None, lambda: brain_core.vision_describe(image_bytes, instruction)
    )
    push_log("info", f"VISION > {text[:140]}", "vision")
    return {"description": text}


# ==============================================================
# TTS
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
    return [{"short_name": v["ShortName"], "gender": v["Gender"], "locale": v["Locale"]} for v in ptbr]


# ==============================================================
# MEMÓRIA CURTA
# ==============================================================
@api.get("/memory")
async def get_memory():
    return _storage.read_json(ARQUIVO_MEMORIA, [])


@api.delete("/memory")
async def clear_memory():
    _storage.write_json(ARQUIVO_MEMORIA, [])
    push_log("warn", "Memória curta apagada", "memory")
    return {"ok": True}


# ==============================================================
# MEMÓRIA LONGA (fatos)
# ==============================================================
@api.get("/long-memory")
async def list_long_memory():
    return lm_core.list_facts()


@api.post("/long-memory")
async def add_long_memory(fact: FactIn):
    novo = lm_core.add_fact(fact.category, fact.fact)
    push_log("info", f"Fato salvo: [{novo['category']}] {novo['fact']}", "long-memory")
    return novo


@api.put("/long-memory/{fact_id}")
async def update_long_memory(fact_id: str, body: FactUpdate):
    if not lm_core.update_fact(fact_id, body.category, body.fact):
        raise HTTPException(404, "Fato não encontrado")
    return {"ok": True}


@api.delete("/long-memory/{fact_id}")
async def delete_long_memory(fact_id: str):
    if not lm_core.remove_fact(fact_id):
        raise HTTPException(404, "Fato não encontrado")
    push_log("warn", f"Fato removido: {fact_id}", "long-memory")
    return {"ok": True}


# ==============================================================
# REMINDERS
# ==============================================================
@api.get("/reminders")
async def list_reminders(only_active: bool = True):
    return rem_core.list_reminders(only_active=only_active)


@api.post("/reminders")
async def add_reminder(body: ReminderIn):
    r = rem_core.add_reminder(body.text, body.when, body.recurrence)
    _schedule_reminder_job(r)
    push_log("info", f"Lembrete criado: {body.text} @ {body.when}", "reminders")
    return r


@api.post("/reminders/natural")
async def add_reminder_natural(body: ReminderNatural):
    """Cria lembrete a partir de frase natural ('amanhã às 8 me lembra de X')."""
    loop = asyncio.get_event_loop()
    try:
        extracted = await loop.run_in_executor(
            None,
            lambda: brain_core.smart_extract(
                body.phrase,
                'Schema: {"text": str, "when_iso": "YYYY-MM-DDTHH:MM:SS-03:00", '
                '"recurrence": "daily"|"weekly"|"monthly"|null}.'
            ),
        )
    except ValueError as e:
        if str(e) == "RATE_LIMIT":
            raise HTTPException(429, "IA ocupada (rate limit). Tente em ~15s.")
        raise HTTPException(400, str(e))
    if not extracted.get("text") or not extracted.get("when_iso"):
        raise HTTPException(400, "Não consegui extrair lembrete da frase")
    r = rem_core.add_reminder(extracted["text"], extracted["when_iso"], extracted.get("recurrence"))
    _schedule_reminder_job(r)
    return r


@api.delete("/reminders/{reminder_id}")
async def delete_reminder(reminder_id: str):
    if not rem_core.remove_reminder(reminder_id):
        raise HTTPException(404, "Não encontrado")
    sched_skill.remove_job(f"rem-{reminder_id}")
    return {"ok": True}


@api.post("/reminders/{reminder_id}/done")
async def done_reminder(reminder_id: str):
    if not rem_core.mark_done(reminder_id):
        raise HTTPException(404, "Não encontrado")
    return {"ok": True}


def _on_reminder_fire(reminder_id: str, text: str):
    push_log("warn", f"⏰ LEMBRETE: {text}", "reminders")
    rem_core.mark_done(reminder_id)


def _schedule_reminder_job(r: dict):
    try:
        sched_skill.schedule_one_shot(
            r["when"],
            _on_reminder_fire,
            args=[r["id"], r["text"]],
            job_id=f"rem-{r['id']}",
        )
    except Exception as e:
        push_log("error", f"Falha ao agendar lembrete: {e}", "reminders")


# ==============================================================
# ROTAS (banco_de_dados.json)
# ==============================================================
@api.get("/routes")
async def list_routes(q: Optional[str] = None):
    data = _storage.read_json(ARQUIVO_DB_ROTAS, {"rotas_km": {}})
    rotas = data.get("rotas_km", {})
    items = []
    for chave, km in rotas.items():
        if "_" in chave:
            origem, destino = chave.split("_", 1)
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
    data = _storage.read_json(ARQUIVO_DB_ROTAS, {"rotas_km": {}})
    data.setdefault("rotas_km", {})
    chave = f"{route.origem.strip().upper()}_{route.destino.strip().upper()}"
    km = int(route.km) if float(route.km).is_integer() else route.km
    data["rotas_km"][chave] = km
    _storage.write_json(ARQUIVO_DB_ROTAS, data)
    return {"ok": True, "key": chave, "km": km}


@api.put("/routes/{key}")
async def update_route(key: str, body: RouteUpdate):
    data = _storage.read_json(ARQUIVO_DB_ROTAS, {"rotas_km": {}})
    if key not in data.get("rotas_km", {}):
        raise HTTPException(404, "Rota não encontrada")
    km = int(body.km) if float(body.km).is_integer() else body.km
    data["rotas_km"][key] = km
    _storage.write_json(ARQUIVO_DB_ROTAS, data)
    return {"ok": True}


@api.delete("/routes/{key}")
async def delete_route(key: str):
    data = _storage.read_json(ARQUIVO_DB_ROTAS, {"rotas_km": {}})
    if key not in data.get("rotas_km", {}):
        raise HTTPException(404, "Rota não encontrada")
    del data["rotas_km"][key]
    _storage.write_json(ARQUIVO_DB_ROTAS, data)
    return {"ok": True}


# ==============================================================
# RELATÓRIOS
# ==============================================================
@api.get("/reports")
async def list_reports():
    data = _storage.read_json(ARQUIVO_RELATORIOS, [])
    out = []
    for i, r in enumerate(data):
        out.append({
            "id": r.get("id", str(i)),
            "periodo": r.get("periodo", ""),
            "gerado_em": r.get("gerado_em", ""),
            "preview": (r.get("conteudo_relatorio", "")[:280]).strip(),
        })
    out.reverse()
    return out


@api.get("/reports/{report_id}")
async def get_report(report_id: str):
    data = _storage.read_json(ARQUIVO_RELATORIOS, [])
    for i, r in enumerate(data):
        rid = r.get("id", str(i))
        if rid == report_id:
            return {**r, "id": rid}
    raise HTTPException(404, "Não encontrado")


@api.post("/reports")
async def add_report(report: Report):
    data = _storage.read_json(ARQUIVO_RELATORIOS, [])
    new = {
        "id": report.id or str(uuid.uuid4()),
        "gerado_em": report.gerado_em or datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "periodo": report.periodo,
        "conteudo_relatorio": report.conteudo_relatorio,
    }
    data.append(new)
    _storage.write_json(ARQUIVO_RELATORIOS, data)
    return new


@api.delete("/reports/{report_id}")
async def delete_report(report_id: str):
    data = _storage.read_json(ARQUIVO_RELATORIOS, [])
    novos = []
    removido = False
    for i, r in enumerate(data):
        rid = r.get("id", str(i))
        if rid == report_id:
            removido = True
            continue
        novos.append(r)
    if not removido:
        raise HTTPException(404, "Não encontrado")
    _storage.write_json(ARQUIVO_RELATORIOS, novos)
    return {"ok": True}


# ==============================================================
# GOOGLE
# ==============================================================
@api.get("/google/status")
async def google_status():
    try:
        from mavis.skills.google_auth import status as g_status
        return g_status()
    except Exception as e:
        return {"error": str(e)}


@api.get("/google/calendar/today")
async def gcal_today():
    try:
        from mavis.skills.google_calendar import list_today
        return list_today()
    except Exception as e:
        raise HTTPException(400, str(e))


@api.get("/google/calendar/week")
async def gcal_week():
    try:
        from mavis.skills.google_calendar import list_week
        return list_week()
    except Exception as e:
        raise HTTPException(400, str(e))


@api.get("/google/gmail/unread")
async def gmail_unread(max_results: int = 10):
    try:
        from mavis.skills.google_gmail import list_unread
        return list_unread(max_results)
    except Exception as e:
        raise HTTPException(400, str(e))


@api.get("/google/gmail/message/{message_id}")
async def gmail_get(message_id: str):
    try:
        from mavis.skills.google_gmail import get_message
        return get_message(message_id)
    except Exception as e:
        raise HTTPException(400, str(e))


class GmailSend(BaseModel):
    to: str
    subject: str
    body: str


@api.post("/google/gmail/send")
async def gmail_send_api(payload: GmailSend):
    try:
        from mavis.skills.google_gmail import send
        return send(payload.to, payload.subject, payload.body)
    except Exception as e:
        raise HTTPException(400, str(e))


@api.get("/google/drive/recent")
async def drive_recent(limit: int = 10):
    try:
        from mavis.skills.google_drive import recent
        return recent(limit)
    except Exception as e:
        raise HTTPException(400, str(e))


@api.get("/google/drive/search")
async def drive_search(q: str, limit: int = 10):
    try:
        from mavis.skills.google_drive import search
        return search(q, limit)
    except Exception as e:
        raise HTTPException(400, str(e))


# ==============================================================
# SISTEMA / SKILLS
# ==============================================================
@api.get("/skills")
async def list_skills():
    return {
        "categorias": [
            {"nome": "Sistema",      "skills": ["system.battery","system.cpu","system.ram","system.shutdown","system.lock"]},
            {"nome": "Computador",   "skills": ["computer.open_app","computer.close_app","computer.type_text","computer.screenshot"]},
            {"nome": "Visão",        "skills": ["vision.read_screen","vision.analyze_image"]},
            {"nome": "WhatsApp",     "skills": ["whatsapp.read_unread","whatsapp.send"]},
            {"nome": "Google",       "skills": ["calendar.today","calendar.week","calendar.create","gmail.unread","gmail.summary","drive.search"]},
            {"nome": "Mídia",        "skills": ["media.play","media.pause","media.next"]},
            {"nome": "Informação",   "skills": ["news.headlines","weather.today"]},
            {"nome": "Memória",      "skills": ["memory.save_fact","reminder.create","reminder.list"]},
            {"nome": "Relatórios",   "skills": ["route.legacy"]},
        ]
    }


@api.get("/system/info")
async def system_info():
    return sys_skill.summary()


@api.get("/news")
async def news(source: str = "g1", limit: int = 5):
    return nw_skill.headlines(source, limit)


@api.get("/weather")
async def weather(lat: float = -23.5505, lon: float = -46.6333):
    return nw_skill.weather(lat, lon)


# ==============================================================
# COMANDOS
# ==============================================================
@api.post("/commands/execute")
async def execute_command(req: CommandRequest):
    cmd = req.command.lower().strip()
    push_log("info", f"CMD > {cmd}", "commands")
    if any(x in cmd for x in ["aprender rotas", "estudar rotas", "atualizar planilha",
                              "preencher quilometragem", "preencher planilha",
                              "gerar relatório", "gerar relatorio", "resumo da semana"]):
        return {"status": "desktop_only",
                "message": "Operação RPA pesada — rode no app desktop (precisa de navegador visual + credenciais.json local)."}
    # Trata como chat
    resposta = await chat(ChatRequest(message=req.command))
    return {"status": "chat", "reply": resposta.reply, "intent": resposta.intent}


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
class ConfigPatch(BaseModel):
    personality: Optional[str] = None


@api.get("/config")
async def get_config():
    return {
        "nome_ia": NOME_IA,
        "modelo_gemini": GEMINI_MODEL,
        "voz": VOZ_SINTETIZADOR,
        "personality": os.environ.get("MAVIS_PERSONALITY", "corporativa"),
        "pause_threshold": float(os.environ.get("PAUSE_THRESHOLD", "1.0")),
        "tem_chave_gemini": bool(CHAVE_GEMINI),
        "chave_gemini_mask": (CHAVE_GEMINI[:6] + "..." + CHAVE_GEMINI[-4:]) if CHAVE_GEMINI else "",
        "whatsapp_grupo": os.environ.get("WHATSAPP_GRUPO", ""),
        "fieldcontrol_email": os.environ.get("FIELDCONTROL_EMAIL", ""),
        "google_credenciais_path": ARQUIVO_CREDENCIAIS_GOOGLE,
        "google_token_path": ARQUIVO_TOKEN_GOOGLE,
    }


@api.patch("/config")
async def patch_config(body: ConfigPatch):
    if body.personality and body.personality in ("corporativa", "casual", "sarcastica"):
        os.environ["MAVIS_PERSONALITY"] = body.personality
        # Atualiza no módulo do brain também
        brain_core.PERSONALITY = body.personality
        push_log("info", f"Personalidade alterada para: {body.personality}", "config")
    return {"ok": True, "personality": os.environ.get("MAVIS_PERSONALITY")}


# ==============================================================
# Inclui o router e startup
# ==============================================================
app.include_router(api)


@app.on_event("startup")
async def startup():
    global MAIN_LOOP
    MAIN_LOOP = asyncio.get_event_loop()
    push_log("info", f"{NOME_IA} v3.0 online. Núcleo Gemini {GEMINI_MODEL}.", "system")
    push_log("info", f"Voz neural: {VOZ_SINTETIZADOR}", "system")
    # Re-agenda lembretes pendentes
    for r in rem_core.list_reminders(only_active=True):
        try:
            _schedule_reminder_job(r)
        except Exception:
            pass
    push_log("info", f"Scheduler online ({len(sched_skill.list_jobs())} jobs ativos)", "system")


@app.on_event("shutdown")
async def shutdown():
    mongo_client.close()
