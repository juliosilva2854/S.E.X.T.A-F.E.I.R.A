"""
mavis.skills.workflows — Macros / sequências de comandos.
Cada workflow é uma lista de steps. Cada step tem {action, args}.
Actions suportadas (server-side): chat, web_search, calendar.today, gmail.unread,
weather, news, summarize, translate, generate_code, sleep, save_note.
"""
import uuid
import time
import os
from datetime import datetime, timezone
from typing import List, Dict, Any
from mavis.core.storage import read_json, write_json
from mavis.core.paths import DATA_DIR

ARQ_WF = str(DATA_DIR / "workflows.json")
ARQ_WF_RUNS = str(DATA_DIR / "workflow_runs.json")


def list_workflows() -> List[Dict[str, Any]]:
    return read_json(ARQ_WF, [])


def save_workflow(wf: Dict[str, Any]) -> Dict[str, Any]:
    items = read_json(ARQ_WF, [])
    if not wf.get("id"):
        wf["id"] = str(uuid.uuid4())
        wf["created_at"] = datetime.now(timezone.utc).isoformat()
        items.append(wf)
    else:
        for i, it in enumerate(items):
            if it["id"] == wf["id"]:
                items[i] = wf
                break
        else:
            items.append(wf)
    write_json(ARQ_WF, items)
    return wf


def delete_workflow(wf_id: str) -> bool:
    items = read_json(ARQ_WF, [])
    novos = [w for w in items if w["id"] != wf_id]
    if len(novos) == len(items):
        return False
    write_json(ARQ_WF, novos)
    return True


def execute_workflow(wf: Dict[str, Any]) -> Dict[str, Any]:
    """
    Executa um workflow synchronously. Cada step:
      {"action": "<nome>", "args": {...}, "label": "opcional"}
    Compartilha um dicionário `state` entre os steps. Cada step pode salvar
    em state[<label>] o retorno.
    """
    state: Dict[str, Any] = {}
    log: List[Dict[str, Any]] = []
    started = datetime.now(timezone.utc).isoformat()

    for i, step in enumerate(wf.get("steps", [])):
        action = step.get("action")
        args = step.get("args", {}) or {}
        label = step.get("label") or f"step_{i}"
        out: Any = None
        ok = True
        err = None
        try:
            if action == "sleep":
                time.sleep(min(int(args.get("seconds", 1)), 30))
                out = "ok"
            elif action == "chat":
                from mavis.core.brain import chat_text
                msg = _interp(args.get("message", ""), state)
                reply, _ = chat_text(msg)
                out = reply
            elif action == "web_search":
                from duckduckgo_search import DDGS
                q = _interp(args.get("query", ""), state)
                out = DDGS().text(q, region="br-pt", max_results=int(args.get("max", 4)))
            elif action == "calendar.today":
                from mavis.skills.google_calendar import list_today
                out = list_today()
            elif action == "gmail.unread":
                from mavis.skills.google_gmail import list_unread
                out = list_unread(int(args.get("max", 10)))
            elif action == "weather":
                from mavis.skills.news_weather import weather
                out = weather()
            elif action == "news":
                from mavis.skills.news_weather import headlines
                out = headlines(args.get("source", "g1"), int(args.get("limit", 5)))
            elif action == "summarize":
                from mavis.skills.document_tools import summarize
                text = _interp(args.get("text", ""), state)
                out = summarize(text, args.get("mode", "executivo"))
            elif action == "translate":
                from mavis.skills.document_tools import translate
                out = translate(_interp(args.get("text", ""), state), args.get("to_lang", "inglês"))
            elif action == "generate_code":
                from mavis.skills.code_assistant import generate
                out = generate(_interp(args.get("prompt", ""), state), args.get("language", "python"))
            elif action == "save_note":
                from mavis.skills.productivity import add_note
                out = add_note(_interp(args.get("text", ""), state), args.get("tag", "workflow"))
            elif action == "research":
                from mavis.skills.research import dossier
                out = dossier(_interp(args.get("topic", ""), state))
            elif action == "compose_email":
                from mavis.skills.document_tools import compose_email
                out = compose_email(_interp(args.get("intent", ""), state),
                                    args.get("tone", "formal"))
            else:
                ok = False
                err = f"Ação desconhecida: {action}"
        except Exception as e:
            ok = False
            err = str(e)
        state[label] = out
        log.append({
            "step": i, "action": action, "label": label, "ok": ok,
            "error": err, "output_preview": _preview(out),
        })
        if not ok and step.get("stop_on_error", True):
            break

    finished = datetime.now(timezone.utc).isoformat()
    record = {
        "id": str(uuid.uuid4()),
        "workflow_id": wf.get("id"),
        "workflow_name": wf.get("name", ""),
        "started": started, "finished": finished,
        "log": log,
    }
    runs = read_json(ARQ_WF_RUNS, [])
    runs.append(record)
    write_json(ARQ_WF_RUNS, runs[-50:])
    return record


def list_runs(limit: int = 20) -> List[Dict[str, Any]]:
    runs = read_json(ARQ_WF_RUNS, [])
    runs.sort(key=lambda x: x.get("started", ""), reverse=True)
    return runs[:limit]


def _interp(template: str, state: Dict[str, Any]) -> str:
    """Substitui {{label}} pelo texto desse step anterior."""
    if not isinstance(template, str):
        return template
    out = template
    for k, v in state.items():
        out = out.replace("{{" + k + "}}", str(v) if v is not None else "")
    return out


def _preview(v: Any) -> str:
    if v is None:
        return "—"
    s = str(v)
    return s[:400] + ("..." if len(s) > 400 else "")
