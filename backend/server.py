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
APP_ROOT = ROOT_DIR.parent

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
        if intent == "whatsapp.send":
            extracted = brain_core.smart_extract(
                raw_text, 
                'Schema: {"contato": str, "mensagem": str}. Extraia o nome do destinatário e o texto a ser enviado.'
            )
            if not extracted.get("contato") or not extracted.get("mensagem"):
                return {"error": "Falta contato ou mensagem."}
            from mavis.skills import whatsapp as wa
            return {"data": wa.send_message(extracted["contato"], extracted["mensagem"])}

        if intent == "whatsapp.read_unread":
            from mavis.skills import whatsapp as wa
            return {"data": wa.list_unread()}

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

        # Comandos operacionais legacy (planilha / relatório / aprender rotas)
        if intent == "route.legacy":
            return await _execute_legacy(raw_text)

        return {"unhandled": True}
    except Exception as e:
        return {"error": str(e)}


async def _execute_legacy(raw_text: str) -> Dict[str, Any]:
    """Executa comandos operacionais legados (Sheets/Playwright).

    Decide a sub-rotina pelo texto:
      - "atualizar planilha" / "preencher quilometragem" -> planilhas.preencher_km_faltantes()
      - "aprender rotas" / "estudar rotas"               -> aprender_rotas.treinar_mavis()
      - "gerar relatório" / "resumo da semana"           -> relatorios.gerar_resumo()
      - "sincronizar planilha" / "sync sheets"           -> google_sheets.sync_all()

    Tarefas pesadas (Playwright/FieldControl) só rodam local. Se estiver hospedado
    sem credenciais.json, retorna {desktop_only: True} para o cérebro avisar.
    """
    txt = raw_text.lower().strip()
    loop = asyncio.get_event_loop()

    # 1) Atualizar planilha (preencher KM faltantes a partir do banco de rotas)
    if any(k in txt for k in ["atualizar planilha", "preencher quilometragem",
                              "preencher planilha", "atualizar plan", "fazer planilha"]):
        # Tenta caminho moderno: gspread + auth Mavis
        try:
            import sys as _sys
            _sys.path.insert(0, str(APP_ROOT))
            import planilhas as _planilhas
            res = await loop.run_in_executor(None, _planilhas.preencher_km_faltantes)
            push_log("info", f"LEGACY > atualizar planilha: {str(res)[:120]}", "router")
            return {"data": res, "action": "planilha.preencher"}
        except FileNotFoundError:
            return {"desktop_only": True, "action": "planilha.preencher",
                    "msg": "credenciais.json não encontrado neste host"}
        except Exception as e:
            return {"error": str(e), "action": "planilha.preencher"}

    # 2) Aprender / estudar rotas (lê planilha e atualiza banco_de_dados.json)
    if any(k in txt for k in ["aprender rotas", "estudar rotas"]):
        try:
            import sys as _sys
            _sys.path.insert(0, str(APP_ROOT))
            import aprender_rotas as _ar
            res = await loop.run_in_executor(None, _ar.treinar_mavis)
            push_log("info", f"LEGACY > aprender rotas: {str(res)[:120]}", "router")
            return {"data": res, "action": "rotas.aprender"}
        except FileNotFoundError:
            return {"desktop_only": True, "action": "rotas.aprender",
                    "msg": "credenciais.json não encontrado neste host"}
        except Exception as e:
            return {"error": str(e), "action": "rotas.aprender"}

    # 3) Gerar relatório (Playwright + FieldControl - DESKTOP_ONLY)
    if any(k in txt for k in ["gerar relatório", "gerar relatorio",
                              "resumo da semana", "relatório da semana",
                              "relatorio da semana", "relatório mensal",
                              "relatório de"]):
        # Só roda local: depende de Playwright + chromium + credenciais.json
        if not os.path.exists(ARQUIVO_CREDENCIAIS_GOOGLE):
            return {"desktop_only": True, "action": "relatorio.gerar",
                    "msg": "Geração de relatório precisa do PC (FieldControl + credenciais)"}
        try:
            import sys as _sys
            _sys.path.insert(0, str(APP_ROOT))
            import relatorios as _rel
            res = await loop.run_in_executor(None, lambda: _rel.gerar_resumo(raw_text))
            push_log("info", f"LEGACY > gerar relatório: {str(res)[:120]}", "router")
            return {"data": res, "action": "relatorio.gerar"}
        except Exception as e:
            return {"error": str(e), "action": "relatorio.gerar"}

    # 4) Sincronizar planilha (puxa do Sheets para o cache local do Analytics)
    if any(k in txt for k in ["sincroniz", "sync planilha", "sync sheets",
                              "atualizar analytics", "atualiza analytics",
                              "puxar planilha", "puxa planilha",
                              "buscar planilha", "busca planilha"]):
        try:
            from mavis.skills import google_sheets as gs
            res = await loop.run_in_executor(None, gs.sync_all)
            push_log("info" if res.get("ok") else "error",
                     f"LEGACY > sync sheets: {res.get('total_rows', 0)} linhas",
                     "router")
            return {"data": res, "action": "sheets.sync"}
        except Exception as e:
            return {"error": str(e), "action": "sheets.sync"}

    return {"unhandled_legacy": True, "raw_text": raw_text}


@api.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    inicio = datetime.now()
    if not CHAVE_GEMINI:
        raise HTTPException(500, "CHAVE_GEMINI não configurada")

    comando = req.message.strip()
    if not comando:
        raise HTTPException(400, "Mensagem vazia")
    push_log("info", f"USR > {comando}", "chat")

    # 0) Custom commands do usuário (verificados primeiro)
    try:
        from mavis.skills import custom_commands as cc
        custom = cc.match(comando)
        if custom and custom.get("reply"):
            push_log("info", f"CUSTOM > {custom['id'][:8]}", "router")
            return ChatResponse(reply=custom["reply"], espera_resposta=False,
                                intent="custom", skill_result={"custom_id": custom["id"]},
                                duration_ms=0)
    except Exception:
        pass

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
# CODE LAB
# ==============================================================
class CodeReq(BaseModel):
    prompt: Optional[str] = None
    code: Optional[str] = None
    language: Optional[str] = "python"
    instruction: Optional[str] = None
    error: Optional[str] = None
    to_lang: Optional[str] = None
    stdin: Optional[str] = ""


@api.post("/code/generate")
async def code_generate(req: CodeReq):
    from mavis.skills import code_assistant as ca
    loop = asyncio.get_event_loop()
    return {"output": await loop.run_in_executor(None, lambda: ca.generate(req.prompt or "", req.language or "python"))}


@api.post("/code/explain")
async def code_explain(req: CodeReq):
    from mavis.skills import code_assistant as ca
    loop = asyncio.get_event_loop()
    return {"output": await loop.run_in_executor(None, lambda: ca.explain(req.code or "", req.language or "auto"))}


@api.post("/code/review")
async def code_review(req: CodeReq):
    from mavis.skills import code_assistant as ca
    loop = asyncio.get_event_loop()
    return {"output": await loop.run_in_executor(None, lambda: ca.review(req.code or "", req.language or "auto"))}


@api.post("/code/refactor")
async def code_refactor(req: CodeReq):
    from mavis.skills import code_assistant as ca
    loop = asyncio.get_event_loop()
    return {"output": await loop.run_in_executor(
        None, lambda: ca.refactor(req.code or "", req.instruction or "melhorar legibilidade", req.language or "auto"))}


@api.post("/code/convert")
async def code_convert(req: CodeReq):
    from mavis.skills import code_assistant as ca
    loop = asyncio.get_event_loop()
    return {"output": await loop.run_in_executor(
        None, lambda: ca.convert(req.code or "", req.language or "python", req.to_lang or "javascript"))}


@api.post("/code/debug")
async def code_debug(req: CodeReq):
    from mavis.skills import code_assistant as ca
    loop = asyncio.get_event_loop()
    return {"output": await loop.run_in_executor(
        None, lambda: ca.debug(req.code or "", req.error or "", req.language or "auto"))}


@api.post("/code/execute")
async def code_execute(req: CodeReq):
    if not req.code:
        raise HTTPException(400, "código vazio")
    from mavis.skills import python_sandbox
    loop = asyncio.get_event_loop()
    out = await loop.run_in_executor(None, lambda: python_sandbox.run(req.code, req.stdin or ""))
    push_log("info", f"PYEXEC > exit={out.get('returncode')} timeout={out.get('timeout_hit')}", "code")
    return out


# ==============================================================
# DOCUMENT TOOLS
# ==============================================================
class DocReq(BaseModel):
    text: str
    mode: Optional[str] = "executivo"
    to_lang: Optional[str] = "inglês"
    tone: Optional[str] = "formal"


@api.post("/doc/summarize")
async def doc_summarize(req: DocReq):
    from mavis.skills import document_tools as dt
    loop = asyncio.get_event_loop()
    return {"output": await loop.run_in_executor(None, lambda: dt.summarize(req.text, req.mode or "executivo"))}


@api.post("/doc/translate")
async def doc_translate(req: DocReq):
    from mavis.skills import document_tools as dt
    loop = asyncio.get_event_loop()
    return {"output": await loop.run_in_executor(None, lambda: dt.translate(req.text, req.to_lang or "inglês"))}


@api.post("/doc/rewrite")
async def doc_rewrite(req: DocReq):
    from mavis.skills import document_tools as dt
    loop = asyncio.get_event_loop()
    return {"output": await loop.run_in_executor(None, lambda: dt.rewrite(req.text, req.tone or "formal"))}


@api.post("/doc/key-points")
async def doc_key(req: DocReq):
    from mavis.skills import document_tools as dt
    loop = asyncio.get_event_loop()
    return {"output": await loop.run_in_executor(None, lambda: dt.key_points(req.text))}


@api.post("/doc/sentiment")
async def doc_sentiment(req: DocReq):
    from mavis.skills import document_tools as dt
    loop = asyncio.get_event_loop()
    return {"output": await loop.run_in_executor(None, lambda: dt.sentiment(req.text))}


class EmailReq(BaseModel):
    intent: str
    tone: Optional[str] = "formal"
    language: Optional[str] = "português"


@api.post("/doc/compose-email")
async def doc_email(req: EmailReq):
    from mavis.skills import document_tools as dt
    loop = asyncio.get_event_loop()
    return {"output": await loop.run_in_executor(
        None, lambda: dt.compose_email(req.intent, req.tone or "formal", req.language or "português"))}


# ==============================================================
# RESEARCH (Dossier)
# ==============================================================
class ResearchReq(BaseModel):
    topic: str


@api.post("/research")
async def do_research(req: ResearchReq):
    from mavis.skills import research as rs
    loop = asyncio.get_event_loop()
    out = await loop.run_in_executor(None, lambda: rs.dossier(req.topic))
    push_log("info", f"RESEARCH > {req.topic}", "research")
    return out


# ==============================================================
# FINANCE
# ==============================================================
@api.get("/finance/forex")
async def fin_forex(base: str = "USD", quote: str = "BRL"):
    from mavis.skills import finance as fi
    return fi.forex(base, quote)


@api.get("/finance/multi")
async def fin_multi():
    from mavis.skills import finance as fi
    return fi.multi_forex()


@api.get("/finance/crypto")
async def fin_crypto(coin: str = "bitcoin", vs: str = "brl"):
    from mavis.skills import finance as fi
    return fi.crypto(coin, vs)


class LoanReq(BaseModel):
    principal: float
    annual_rate_pct: float
    months: int


@api.post("/finance/loan")
async def fin_loan(req: LoanReq):
    from mavis.skills import finance as fi
    return fi.loan_payment(req.principal, req.annual_rate_pct, req.months)


class CompoundReq(BaseModel):
    principal: float
    annual_rate_pct: float
    years: float
    monthly_contribution: float = 0


@api.post("/finance/compound")
async def fin_compound(req: CompoundReq):
    from mavis.skills import finance as fi
    return fi.compound_interest(req.principal, req.annual_rate_pct, req.years, req.monthly_contribution)


# ==============================================================
# PRODUCTIVITY (Notes / Todos / Pomodoro)
# ==============================================================
class NoteIn(BaseModel):
    text: str
    tag: Optional[str] = ""


@api.get("/notes")
async def notes_list():
    from mavis.skills import productivity as p
    return p.list_notes()


@api.post("/notes")
async def notes_add(n: NoteIn):
    from mavis.skills import productivity as p
    return p.add_note(n.text, n.tag or "")


@api.delete("/notes/{nid}")
async def notes_del(nid: str):
    from mavis.skills import productivity as p
    if not p.delete_note(nid):
        raise HTTPException(404, "não encontrado")
    return {"ok": True}


class TodoIn(BaseModel):
    text: str
    priority: int = 1
    due: Optional[str] = None


@api.get("/todos")
async def todos_list(only_pending: bool = False):
    from mavis.skills import productivity as p
    return p.list_todos(only_pending)


@api.post("/todos")
async def todos_add(t: TodoIn):
    from mavis.skills import productivity as p
    return p.add_todo(t.text, t.priority, t.due)


@api.post("/todos/{tid}/toggle")
async def todos_toggle(tid: str):
    from mavis.skills import productivity as p
    if not p.toggle_todo(tid):
        raise HTTPException(404, "não encontrado")
    return {"ok": True}


@api.delete("/todos/{tid}")
async def todos_del(tid: str):
    from mavis.skills import productivity as p
    if not p.delete_todo(tid):
        raise HTTPException(404, "não encontrado")
    return {"ok": True}


class PomodoroIn(BaseModel):
    minutes: int = 25
    label: str = ""


@api.post("/pomodoro/log")
async def pomo_log(p: PomodoroIn):
    from mavis.skills import productivity as ps
    return ps.log_pomodoro(p.minutes, p.label)


@api.get("/pomodoro/stats")
async def pomo_stats(days: int = 7):
    from mavis.skills import productivity as ps
    return ps.pomodoro_stats(days)


# ==============================================================
# WORKFLOWS
# ==============================================================
class WorkflowIn(BaseModel):
    id: Optional[str] = None
    name: str
    description: Optional[str] = ""
    steps: List[Dict[str, Any]] = []


@api.get("/workflows")
async def wf_list():
    from mavis.skills import workflows as wf
    return wf.list_workflows()


@api.post("/workflows")
async def wf_save(w: WorkflowIn):
    from mavis.skills import workflows as wf
    return wf.save_workflow(w.model_dump())


@api.delete("/workflows/{wid}")
async def wf_del(wid: str):
    from mavis.skills import workflows as wf
    if not wf.delete_workflow(wid):
        raise HTTPException(404, "não encontrado")
    return {"ok": True}


@api.post("/workflows/{wid}/run")
async def wf_run(wid: str):
    from mavis.skills import workflows as wf
    items = wf.list_workflows()
    w = next((x for x in items if x["id"] == wid), None)
    if not w:
        raise HTTPException(404, "não encontrado")
    loop = asyncio.get_event_loop()
    record = await loop.run_in_executor(None, lambda: wf.execute_workflow(w))
    push_log("info", f"WORKFLOW > {w['name']} executed", "workflow")
    return record


@api.get("/workflows/runs")
async def wf_runs(limit: int = 20):
    from mavis.skills import workflows as wf
    return wf.list_runs(limit)


# ==============================================================
# KNOWLEDGE BASE
# ==============================================================
@api.get("/knowledge/documents")
async def kb_list():
    from mavis.skills import knowledge as kb
    return kb.list_documents()


@api.post("/knowledge/documents")
async def kb_add(file: UploadFile = File(...)):
    from mavis.skills import knowledge as kb
    data = await file.read()
    if not data:
        raise HTTPException(400, "arquivo vazio")
    out = kb.add_document(file.filename or "doc", data)
    if "error" in out:
        raise HTTPException(400, out["error"])
    push_log("info", f"KB > +{file.filename} ({out['chunks']} chunks)", "knowledge")
    return out


@api.delete("/knowledge/documents/{doc_id}")
async def kb_del(doc_id: str):
    from mavis.skills import knowledge as kb
    if not kb.delete_document(doc_id):
        raise HTTPException(404, "não encontrado")
    return {"ok": True}


class KbAsk(BaseModel):
    query: str


@api.post("/knowledge/ask")
async def kb_ask(body: KbAsk):
    from mavis.skills import knowledge as kb
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, lambda: kb.ask(body.query))


# ==============================================================
# CONFIG (.env editor + custom commands + credenciais Google + auto-report)
# ==============================================================
@api.get("/env/items")
async def env_items():
    from mavis.skills import env_manager as em
    return em.get_all()


class EnvPatch(BaseModel):
    updates: Dict[str, str]


@api.post("/env/update")
async def env_update(body: EnvPatch):
    from mavis.skills import env_manager as em
    try:
        out = em.update(body.updates)
    except ValueError as e:
        raise HTTPException(400, str(e))
    push_log("warn", f"ENV > atualizado: {list(body.updates.keys())}", "config")
    return out


@api.post("/google/credentials")
async def upload_google_creds(file: UploadFile = File(...)):
    """Salva o credenciais.json do OAuth Google."""
    data = await file.read()
    if not data:
        raise HTTPException(400, "vazio")
    try:
        parsed = json.loads(data)
        if "installed" not in parsed and "web" not in parsed:
            raise ValueError("Formato inválido (esperado installed/web)")
    except Exception as e:
        raise HTTPException(400, f"JSON inválido: {e}")
    with open(ARQUIVO_CREDENCIAIS_GOOGLE, "wb") as f:
        f.write(data)
    push_log("info", "credenciais.json carregado", "google")
    return {"ok": True, "path": ARQUIVO_CREDENCIAIS_GOOGLE}


# ---------- Custom Commands ----------
class CustomCmdIn(BaseModel):
    pattern: str
    reply: str = ""
    action: Optional[str] = None
    args: Optional[Dict[str, Any]] = None
    description: Optional[str] = ""


@api.get("/custom-commands")
async def cc_list():
    from mavis.skills import custom_commands as cc
    return cc.list_all()


@api.post("/custom-commands")
async def cc_add(body: CustomCmdIn):
    from mavis.skills import custom_commands as cc
    try:
        return cc.add(body.pattern, body.reply, body.action, body.args, body.description or "")
    except Exception as e:
        raise HTTPException(400, f"regex inválido: {e}")


@api.delete("/custom-commands/{cid}")
async def cc_del(cid: str):
    from mavis.skills import custom_commands as cc
    if not cc.remove(cid):
        raise HTTPException(404, "não encontrado")
    return {"ok": True}


# ---------- Bulk import reports ----------
class ReportImport(BaseModel):
    items: List[Dict[str, Any]]


@api.post("/reports/import")
async def reports_import(body: ReportImport):
    data = _storage.read_json(ARQUIVO_RELATORIOS, [])
    added = 0
    for r in body.items:
        if not r.get("conteudo_relatorio") and not r.get("conteudo"):
            continue
        novo = {
            "id": r.get("id") or str(uuid.uuid4()),
            "gerado_em": r.get("gerado_em") or datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "periodo": r.get("periodo", "Importado"),
            "conteudo_relatorio": r.get("conteudo_relatorio") or r.get("conteudo"),
        }
        data.append(novo)
        added += 1
    _storage.write_json(ARQUIVO_RELATORIOS, data)
    push_log("info", f"REPORTS > {added} relatórios importados", "reports")
    return {"added": added, "total": len(data)}


# ---------- Auto Report (gerar manualmente ou via cron) ----------
@api.post("/reports/auto-weekly")
async def auto_weekly():
    from mavis.skills import auto_report as ar
    loop = asyncio.get_event_loop()
    out = await loop.run_in_executor(None, ar.generate_weekly)
    return out


class AutoReportConfig(BaseModel):
    enabled: Optional[bool] = None
    day_of_week: Optional[str] = None
    hour: Optional[int] = None
    minute: Optional[int] = None
    period_days: Optional[int] = None
    send_whatsapp: Optional[bool] = None


def _run_auto_report():
    """Callback do scheduler: gera o relatório semanal (resumo + PDF)."""
    from mavis.skills import auto_report as ar
    try:
        res = ar.generate_and_store()
        push_log("info", f"📄 Relatório automático gerado: {res['filename']} ({res['total_km']} km · WhatsApp: {res['whatsapp']})", "analytics")
        return res
    except Exception as e:
        push_log("error", f"Falha no relatório automático: {e}", "analytics")
        return {"error": str(e)}


def _schedule_auto_report():
    """(Re)agenda o job semanal conforme a config. Remove se desativado."""
    from mavis.skills import auto_report as ar
    cfg = ar.get_config()
    sched_skill.remove_job("auto-report-weekly")
    if cfg.get("enabled"):
        sched_skill.schedule_recurring(ar.cron_expr(), _run_auto_report, job_id="auto-report-weekly")
        push_log("info", f"Relatório automático ativo: {ar.WEEKDAYS_PT.get(cfg['day_of_week'], cfg['day_of_week'])} {cfg['hour']:02d}:{cfg['minute']:02d}", "analytics")


@api.get("/analytics/auto-report")
async def get_auto_report():
    from mavis.skills import auto_report as ar
    cfg = ar.get_config()
    jobs = [j for j in sched_skill.list_jobs() if j["id"] == "auto-report-weekly"]
    return {"config": cfg, "next_run": jobs[0]["next_run"] if jobs else None, "reports": ar.list_reports()}


@api.post("/analytics/auto-report")
async def set_auto_report(body: AutoReportConfig):
    from mavis.skills import auto_report as ar
    cfg = ar.set_config(body.dict(exclude_none=True))
    _schedule_auto_report()
    jobs = [j for j in sched_skill.list_jobs() if j["id"] == "auto-report-weekly"]
    return {"config": cfg, "next_run": jobs[0]["next_run"] if jobs else None}


@api.post("/analytics/auto-report/run-now")
async def run_auto_report_now():
    from mavis.skills import auto_report as ar
    loop = asyncio.get_event_loop()
    res = await loop.run_in_executor(None, ar.generate_and_store)
    push_log("info", f"📄 Relatório gerado manualmente: {res['filename']}", "analytics")
    return res


@api.get("/analytics/auto-report/download/{filename}")
async def download_auto_report(filename: str):
    from mavis.skills import auto_report as ar
    p = ar.report_path(filename)
    if not p.exists():
        raise HTTPException(404, "relatório não encontrado")
    return Response(content=p.read_bytes(), media_type="application/pdf",
                    headers={"Content-Disposition": f'attachment; filename="{p.name}"'})


# ==============================================================
# AUTO-REPORT MENSAL (macro, dia 1º 08h por padrão)
# ==============================================================
def _run_auto_monthly():
    """Callback do scheduler: gera o resumo mensal macro (PDF + texto)."""
    from mavis.skills import auto_report as ar
    try:
        res = ar.generate_monthly()
        push_log("info", f"📅 Resumo mensal gerado: {res['filename']} "
                         f"({res['total_atendimentos']} atend. · {res['total_preventivas']} prev. "
                         f"· WhatsApp: {res['whatsapp']})", "analytics")
        return res
    except Exception as e:
        push_log("error", f"Falha no resumo mensal: {e}", "analytics")
        return {"error": str(e)}


def _schedule_auto_monthly():
    """(Re)agenda o job mensal conforme a config. Remove se desativado."""
    from mavis.skills import auto_report as ar
    cfg = ar.get_config()
    sched_skill.remove_job("auto-report-monthly")
    if cfg.get("monthly_enabled"):
        sched_skill.schedule_recurring(ar.cron_expr_monthly(), _run_auto_monthly,
                                       job_id="auto-report-monthly")
        push_log("info", f"Resumo mensal ativo: dia {cfg['monthly_day']} às "
                         f"{cfg['monthly_hour']:02d}:{cfg['monthly_minute']:02d}", "analytics")


@api.get("/analytics/auto-monthly")
async def get_auto_monthly():
    from mavis.skills import auto_report as ar
    cfg = ar.get_config()
    jobs = [j for j in sched_skill.list_jobs() if j["id"] == "auto-report-monthly"]
    return {
        "config": cfg,
        "next_run": jobs[0]["next_run"] if jobs else None,
        "reports": ar.list_monthly_reports(),
    }


@api.post("/analytics/auto-monthly")
async def set_auto_monthly(body: Dict[str, Any]):
    from mavis.skills import auto_report as ar
    cfg = ar.set_config(body or {})
    _schedule_auto_monthly()
    jobs = [j for j in sched_skill.list_jobs() if j["id"] == "auto-report-monthly"]
    return {"config": cfg, "next_run": jobs[0]["next_run"] if jobs else None}


class MonthlyRunRequest(BaseModel):
    month: Optional[str] = None         # "YYYY-MM"; default = mês anterior fechado
    destination_id: Optional[str] = None # favorito (sobrescreve config)


@api.post("/analytics/auto-monthly/run-now")
async def run_auto_monthly_now(body: Optional[MonthlyRunRequest] = None):
    from mavis.skills import auto_report as ar
    body = body or MonthlyRunRequest()
    loop = asyncio.get_event_loop()
    res = await loop.run_in_executor(None,
                                     lambda: ar.generate_monthly(body.month, body.destination_id))
    push_log("info", f"📅 Resumo mensal gerado manualmente: {res['filename']}", "analytics")
    return res


@api.get("/analytics/auto-monthly/download/{filename}")
async def download_auto_monthly(filename: str):
    from mavis.skills import auto_report as ar
    p = ar.report_path(filename)
    if not p.exists():
        raise HTTPException(404, "relatório não encontrado")
    return Response(content=p.read_bytes(), media_type="application/pdf",
                    headers={"Content-Disposition": f'attachment; filename="{p.name}"'})


@api.get("/analytics/monthly-macro")
async def analytics_monthly_macro(month: str = ""):
    """Retorna o macro de um mês (YYYY-MM). Sem `month`, usa o mês anterior fechado."""
    from mavis.skills import analytics as an
    if not month:
        today = datetime.now()
        first_of_this = today.replace(day=1)
        last_day_prev = first_of_this - timedelta(days=1)
        month = last_day_prev.strftime("%Y-%m")
    return an.monthly_macro(month)


# ==============================================================
# WHATSAPP FAVORITOS (CRUD + envio com favorite_id)
# ==============================================================
class FavoriteIn(BaseModel):
    nome: str
    tipo: Optional[str] = "grupo"      # "grupo" | "contato"
    display_name: Optional[str] = ""


class FavoritePatch(BaseModel):
    nome: Optional[str] = None
    tipo: Optional[str] = None
    display_name: Optional[str] = None


class WhatsappSend(BaseModel):
    message: str
    favorite_id: Optional[str] = None
    nome: Optional[str] = None         # alternativa: nome do contato/grupo


@api.get("/whatsapp/favorites")
async def whatsapp_list_favorites():
    from mavis.skills import whatsapp_favorites as wf
    return wf.list_all()


@api.post("/whatsapp/favorites")
async def whatsapp_add_favorite(body: FavoriteIn):
    from mavis.skills import whatsapp_favorites as wf
    try:
        fav = wf.add(body.nome, body.tipo or "grupo", body.display_name or "")
        push_log("info", f"WhatsApp favorito adicionado: {fav['display_name']} ({fav['tipo']})", "whatsapp")
        return fav
    except ValueError as e:
        raise HTTPException(400, str(e))


@api.patch("/whatsapp/favorites/{fav_id}")
async def whatsapp_update_favorite(fav_id: str, body: FavoritePatch):
    from mavis.skills import whatsapp_favorites as wf
    out = wf.update(fav_id, body.dict(exclude_none=True))
    if not out:
        raise HTTPException(404, "favorito não encontrado")
    return out


@api.delete("/whatsapp/favorites/{fav_id}")
async def whatsapp_remove_favorite(fav_id: str):
    from mavis.skills import whatsapp_favorites as wf
    if not wf.remove(fav_id):
        raise HTTPException(404, "favorito não encontrado")
    return {"removed": True}


@api.post("/whatsapp/send")
async def whatsapp_send(body: WhatsappSend):
    """Envia mensagem via WAHA (invisível e instantâneo)."""
    from mavis.skills import whatsapp_favorites as wf
    from mavis.skills import whatsapp as wa
    
    dest = wf.resolve_destination(body.favorite_id, body.nome)
    if not dest:
        raise HTTPException(400, "destino inválido (informe favorite_id ou nome)")
    if not body.message.strip():
        raise HTTPException(400, "mensagem vazia")

    # Envia direto para o nosso novo código, sem checar DESKTOP_MODE
    loop = asyncio.get_event_loop()
    res = await loop.run_in_executor(None, lambda: wa.send_message(dest["nome"], body.message))
    
    push_log("info" if res.get("ok") else "error",
             f"WhatsApp → {dest['nome']}: {'ok' if res.get('ok') else res.get('error')}",
             "whatsapp")
             
    return {"sent": bool(res.get("ok")), "destino": dest, **res}


@api.get("/whatsapp/status")
async def whatsapp_status():
    """Status atual da sessão WAHA (conectado/desconectado, engine, URL)."""
    from mavis.skills import whatsapp as wa
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, wa.status)


@api.get("/whatsapp/unread")
async def whatsapp_unread(limit: int = 10):
    """Lista chats com mensagens não-lidas via WAHA."""
    from mavis.skills import whatsapp as wa
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, lambda: wa.list_unread(limit))


# ==============================================================
# GOOGLE SHEETS — alimentação do Analytics
# ==============================================================
@api.get("/sheets/status")
async def sheets_status():
    """Estado do cache local do Google Sheets (última sync, total linhas, abas)."""
    from mavis.skills import google_sheets as gs
    return gs.status()


@api.post("/sheets/sync")
async def sheets_sync():
    """Força sincronização da planilha KM (varre TODAS as abas mensais)."""
    from mavis.skills import google_sheets as gs
    loop = asyncio.get_event_loop()
    res = await loop.run_in_executor(None, gs.sync_all)
    push_log("info" if res.get("ok") else "error",
             f"SHEETS > sync: {res.get('total_rows', 0)} linhas, ok={res.get('ok')}",
             "sheets")
    return res


@api.get("/sheets/rows")
async def sheets_rows(start: str = "", end: str = "", unidade: str = "", limit: int = 500):
    """Devolve linhas estruturadas (Data, Origem, Destino, KM, Tipo, Ticket) do cache."""
    from mavis.skills import google_sheets as gs
    rows = gs.get_rows(start=start, end=end, unidade=unidade)
    return {"total": len(rows), "rows": rows[-limit:]}


def _run_auto_sheets_sync():
    """Job APScheduler: roda sync_all e loga resultado."""
    try:
        from mavis.skills import google_sheets as gs
        res = gs.sync_all()
        if res.get("ok"):
            push_log("info",
                     f"AUTO-SHEETS > sync: {res.get('total_rows', 0)} linhas em "
                     f"{len(res.get('abas', []))} abas",
                     "sheets")
        else:
            push_log("error", f"AUTO-SHEETS > falha: {res.get('error')}", "sheets")
    except Exception as e:  # pragma: no cover
        push_log("error", f"AUTO-SHEETS > exceção: {e}", "sheets")


def _schedule_auto_sheets_sync():
    """Agenda sync diário do Sheets (default: 7h). Controle via env:
       MAVIS_SHEETS_AUTOSYNC=1       (liga)
       MAVIS_SHEETS_AUTOSYNC_HOUR=7  (hora)
    """
    if os.environ.get("MAVIS_SHEETS_AUTOSYNC", "0") != "1":
        return
    try:
        hour = int(os.environ.get("MAVIS_SHEETS_AUTOSYNC_HOUR", "7"))
    except ValueError:
        hour = 7
    sched_skill.schedule_recurring(
        {"hour": hour, "minute": 0},
        _run_auto_sheets_sync,
        job_id="sheets-autosync-daily",
    )


@api.post("/sheets/autosync/toggle")
async def sheets_autosync_toggle(enabled: bool, hour: Optional[int] = None):
    """Liga/desliga o sync automático diário do Sheets em runtime.

    Persiste no .env via env_manager (para sobreviver ao restart).
    """
    from mavis.skills import env_manager as em
    patch = {"MAVIS_SHEETS_AUTOSYNC": "1" if enabled else "0"}
    if hour is not None:
        patch["MAVIS_SHEETS_AUTOSYNC_HOUR"] = str(int(hour))
    em.update_env(patch)
    # Aplica em memória
    os.environ["MAVIS_SHEETS_AUTOSYNC"] = patch["MAVIS_SHEETS_AUTOSYNC"]
    if hour is not None:
        os.environ["MAVIS_SHEETS_AUTOSYNC_HOUR"] = patch["MAVIS_SHEETS_AUTOSYNC_HOUR"]
    # Remove job antigo e re-agenda
    sched_skill.remove_job("sheets-autosync-daily")
    _schedule_auto_sheets_sync()
    jobs = [j for j in sched_skill.list_jobs() if j["id"] == "sheets-autosync-daily"]
    return {"enabled": enabled, "hour": int(os.environ.get("MAVIS_SHEETS_AUTOSYNC_HOUR", "7")),
            "next_run": jobs[0]["next_run"] if jobs else None}


@api.get("/sheets/autosync")
async def sheets_autosync_status():
    enabled = os.environ.get("MAVIS_SHEETS_AUTOSYNC", "0") == "1"
    try:
        hour = int(os.environ.get("MAVIS_SHEETS_AUTOSYNC_HOUR", "7"))
    except ValueError:
        hour = 7
    jobs = [j for j in sched_skill.list_jobs() if j["id"] == "sheets-autosync-daily"]
    return {"enabled": enabled, "hour": hour,
            "next_run": jobs[0]["next_run"] if jobs else None}

# ==============================================================
# PDF Fields catalog (para o modal de seleção)
# ==============================================================
@api.get("/analytics/pdf-fields")
async def analytics_pdf_fields():
    from mavis.skills import analytics_export as ex
    return ex.pdf_fields_catalog()


class PdfExportRequest(BaseModel):
    start: Optional[str] = ""
    end: Optional[str] = ""
    unidade: Optional[str] = ""
    fuel_cost: Optional[float] = 5.89
    km_per_liter: Optional[float] = 10.0
    fields: Optional[Dict[str, Any]] = None  # {kpis: [...], columns: [...], sections: [...]}


@api.post("/analytics/export-pdf")
async def analytics_export_pdf(body: PdfExportRequest, send_to_id: Optional[str] = None):
    from mavis.skills import analytics as an
    from mavis.skills import analytics_export as ex
    from mavis.skills import whatsapp_favorites as wf
    from mavis.skills import whatsapp as wa
    
    # Gera o PDF
    rows = an.export_rows(start=body.start or "", end=body.end or "", unidade=body.unidade or "")
    kpis = an.kpis_filtered(start=body.start or "", end=body.end or "", unidade=body.unidade or "",
                            fuel_cost_per_liter=body.fuel_cost or 5.89,
                            km_per_liter=body.km_per_liter or 10.0)
    pdf_bytes = ex.to_pdf(rows, kpis,
                          filtro={"start": body.start, "end": body.end, "unidade": body.unidade},
                          fields=body.fields)
    ts = datetime.now().strftime("%Y%m%d_%H%M")
    filename = f"mavis_analytics_{ts}.pdf"

    # Se um destino (favorite_id) foi enviado, enviamos via WAHA
    if send_to_id:
        dest = wf.resolve_destination(send_to_id, None)
        if not dest:
            raise HTTPException(400, "Destino não encontrado")
        
        wa_res = wa.send_file(dest["nome"], pdf_bytes, filename)
        if not wa_res.get("ok"):
            raise HTTPException(500, f"Erro ao enviar via WAHA: {wa_res.get('error')}")
        return {"ok": True, "message": f"Enviado para {dest['display_name']}"}

    # Caso contrário, comportamento padrão (download)
    return Response(content=pdf_bytes, media_type="application/pdf",
                    headers={"Content-Disposition": f'attachment; filename="{filename}"'})


# ==============================================================
# AGENT MODE (autônomo)
# ==============================================================
class AgentReq(BaseModel):
    goal: str


@api.post("/agent/run")
async def agent_run(req: AgentReq):
    from mavis.skills import agent as ag
    if not req.goal.strip():
        raise HTTPException(400, "meta vazia")
    push_log("info", f"AGENT > {req.goal[:120]}", "agent")
    loop = asyncio.get_event_loop()
    out = await loop.run_in_executor(None, lambda: ag.run(req.goal))
    push_log("info", f"AGENT > done ({len(out['steps'])} steps)", "agent")
    return out


@api.get("/agent/tools")
async def agent_tools():
    from mavis.skills.agent import TOOLS
    return TOOLS


# ==============================================================
# ANALYTICS
@api.get("/analytics/kpis")
async def analytics_kpis(fuel_cost: float = 5.89, km_per_liter: float = 10.0,
                         start: str = "", end: str = "", unidade: str = ""):
    from mavis.skills import analytics as an
    return an.kpis_filtered(start=start, end=end, unidade=unidade,
                            fuel_cost_per_liter=fuel_cost, km_per_liter=km_per_liter)


@api.get("/analytics/weekly")
async def analytics_weekly(weeks: int = 12, start: str = "", end: str = "", unidade: str = ""):
    from mavis.skills import analytics as an
    return an.weekly_filtered(start=start, end=end, unidade=unidade, weeks=weeks)


@api.get("/analytics/unidades")
async def analytics_unidades():
    from mavis.skills import analytics as an
    return an.unidades_list()


@api.get("/analytics/map-data")
async def analytics_map_data(start: str = "", end: str = "", unidade: str = "",
                             allow_remote: bool = True):
    from mavis.skills import analytics as an
    return an.map_data(start=start, end=end, unidade=unidade, allow_remote=allow_remote)


@api.get("/analytics/resumo")
async def analytics_resumo(start: str = "", end: str = "", unidade: str = "",
                          fuel_cost: float = 5.89, km_per_liter: float = 10.0, titulo: str = ""):
    """Resumo executivo em texto (pronto para compartilhar no WhatsApp)."""
    from mavis.skills import analytics as an
    texto = an.resumo_texto(start=start, end=end, unidade=unidade,
                            fuel_cost_per_liter=fuel_cost, km_per_liter=km_per_liter, titulo=titulo)
    return {"texto": texto, "grupo": os.environ.get("WHATSAPP_GRUPO", "")}


@api.get("/analytics/export")
async def analytics_export(format: str = "csv", start: str = "", end: str = "", unidade: str = "",
                           fuel_cost: float = 5.89, km_per_liter: float = 10.0):
    from mavis.skills import analytics as an
    from mavis.skills import analytics_export as ex
    rows = an.export_rows(start=start, end=end, unidade=unidade)
    kpis = an.kpis_filtered(start=start, end=end, unidade=unidade,
                            fuel_cost_per_liter=fuel_cost, km_per_liter=km_per_liter)
    fmt = (format or "csv").lower()
    ts = datetime.now().strftime("%Y%m%d_%H%M")
    if fmt == "csv":
        return Response(content=ex.to_csv(rows), media_type="text/csv; charset=utf-8",
                        headers={"Content-Disposition": f'attachment; filename="mavis_analytics_{ts}.csv"'})
    if fmt in ("xlsx", "excel"):
        return Response(content=ex.to_xlsx(rows, kpis),
                        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        headers={"Content-Disposition": f'attachment; filename="mavis_analytics_{ts}.xlsx"'})
    if fmt == "pdf":
        return Response(content=ex.to_pdf(rows, kpis, filtro={"start": start, "end": end, "unidade": unidade}),
                        media_type="application/pdf",
                        headers={"Content-Disposition": f'attachment; filename="mavis_analytics_{ts}.pdf"'})
    raise HTTPException(400, "format inválido (use csv|xlsx|pdf)")


@api.get("/analytics/monthly")
async def analytics_monthly(months: int = 12):
    from mavis.skills import analytics as an
    return an.monthly_series(months)


@api.get("/analytics/daily")
async def analytics_daily(days: int = 60):
    from mavis.skills import analytics as an
    return an.daily_series(days)


@api.get("/analytics/heatmap")
async def analytics_heatmap():
    from mavis.skills import analytics as an
    return an.heatmap_weekday()


@api.get("/analytics/activities")
async def analytics_activities(start: str = "", end: str = "", unidade: str = ""):
    from mavis.skills import analytics as an
    return an.activity_filtered(start=start, end=end, unidade=unidade)


@api.get("/analytics/month/{month}")
async def analytics_month_detail(month: str):
    """month no formato YYYY-MM"""
    from mavis.skills import analytics as an
    out = an.month_detail(month)
    if "error" in out:
        raise HTTPException(404, out["error"])
    return out


@api.get("/analytics/parse-all")
async def analytics_parse_all():
    """Retorna todos os relatórios parseados (útil para debug)."""
    from mavis.skills import analytics as an
    return an.parse_all()


# ==============================================================
# COMANDOS (legacy + chat)
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
    # Agenda o relatório automático semanal, se ativado
    try:
        _schedule_auto_report()
    except Exception as e:
        push_log("error", f"Falha ao agendar relatório automático: {e}", "system")
    # Agenda o resumo mensal macro, se ativado
    try:
        _schedule_auto_monthly()
    except Exception as e:
        push_log("error", f"Falha ao agendar resumo mensal: {e}", "system")
    # Agenda o auto-sync diário do Google Sheets, se ativado
    try:
        _schedule_auto_sheets_sync()
    except Exception as e:
        push_log("error", f"Falha ao agendar auto-sync do Sheets: {e}", "system")


@app.on_event("shutdown")
async def shutdown():
    mongo_client.close()
