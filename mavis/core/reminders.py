"""
mavis.core.reminders — Lembretes e alarmes com APScheduler.
"""
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from .paths import ARQUIVO_REMINDERS
from .storage import read_json, write_json


def list_reminders(only_active: bool = False) -> List[Dict[str, Any]]:
    items = read_json(ARQUIVO_REMINDERS, [])
    if only_active:
        items = [r for r in items if not r.get("done")]
    items.sort(key=lambda x: x.get("when", ""))
    return items


def add_reminder(text: str, when_iso: str, recurrence: Optional[str] = None) -> Dict[str, Any]:
    items = read_json(ARQUIVO_REMINDERS, [])
    novo = {
        "id": str(uuid.uuid4()),
        "text": text.strip(),
        "when": when_iso,
        "recurrence": recurrence,  # None | "daily" | "weekly" | "monthly"
        "done": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    items.append(novo)
    write_json(ARQUIVO_REMINDERS, items)
    return novo


def mark_done(reminder_id: str) -> bool:
    items = read_json(ARQUIVO_REMINDERS, [])
    for r in items:
        if r["id"] == reminder_id:
            r["done"] = True
            write_json(ARQUIVO_REMINDERS, items)
            return True
    return False


def remove_reminder(reminder_id: str) -> bool:
    items = read_json(ARQUIVO_REMINDERS, [])
    novos = [r for r in items if r["id"] != reminder_id]
    if len(novos) == len(items):
        return False
    write_json(ARQUIVO_REMINDERS, novos)
    return True


def due_reminders(now: Optional[datetime] = None) -> List[Dict[str, Any]]:
    """Retorna lembretes que já passaram do horário e ainda não foram marcados."""
    if now is None:
        now = datetime.now(timezone.utc)
    out = []
    for r in list_reminders(only_active=True):
        try:
            when = datetime.fromisoformat(r["when"].replace("Z", "+00:00"))
            if when.tzinfo is None:
                when = when.replace(tzinfo=timezone.utc)
            if when <= now:
                out.append(r)
        except Exception:
            continue
    return out
