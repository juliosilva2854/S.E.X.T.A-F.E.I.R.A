"""
mavis.skills.productivity — Pomodoro, Quick Notes, To-do list.
"""
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from mavis.core.storage import read_json, write_json
from mavis.core.paths import DATA_DIR

ARQ_NOTES = str(DATA_DIR / "quick_notes.json")
ARQ_TODOS = str(DATA_DIR / "todos.json")
ARQ_POMODORO = str(DATA_DIR / "pomodoro_log.json")


# ========== Quick Notes ==========
def list_notes() -> List[Dict[str, Any]]:
    items = read_json(ARQ_NOTES, [])
    items.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return items


def add_note(text: str, tag: str = "") -> Dict[str, Any]:
    items = read_json(ARQ_NOTES, [])
    novo = {
        "id": str(uuid.uuid4()),
        "text": text.strip(),
        "tag": tag.strip(),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    items.append(novo)
    write_json(ARQ_NOTES, items)
    return novo


def delete_note(note_id: str) -> bool:
    items = read_json(ARQ_NOTES, [])
    novos = [x for x in items if x["id"] != note_id]
    if len(novos) == len(items):
        return False
    write_json(ARQ_NOTES, novos)
    return True


# ========== To-Dos ==========
def list_todos(only_pending: bool = False) -> List[Dict[str, Any]]:
    items = read_json(ARQ_TODOS, [])
    if only_pending:
        items = [t for t in items if not t.get("done")]
    items.sort(key=lambda x: (x.get("done", False), -x.get("priority", 0)))
    return items


def add_todo(text: str, priority: int = 1, due: Optional[str] = None) -> Dict[str, Any]:
    items = read_json(ARQ_TODOS, [])
    novo = {
        "id": str(uuid.uuid4()),
        "text": text.strip(),
        "priority": int(priority),
        "due": due,
        "done": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    items.append(novo)
    write_json(ARQ_TODOS, items)
    return novo


def toggle_todo(todo_id: str) -> bool:
    items = read_json(ARQ_TODOS, [])
    for t in items:
        if t["id"] == todo_id:
            t["done"] = not t.get("done", False)
            t["done_at"] = datetime.now(timezone.utc).isoformat() if t["done"] else None
            write_json(ARQ_TODOS, items)
            return True
    return False


def delete_todo(todo_id: str) -> bool:
    items = read_json(ARQ_TODOS, [])
    novos = [x for x in items if x["id"] != todo_id]
    if len(novos) == len(items):
        return False
    write_json(ARQ_TODOS, novos)
    return True


# ========== Pomodoro (log de sessões concluídas) ==========
def log_pomodoro(focus_minutes: int = 25, label: str = "") -> Dict[str, Any]:
    items = read_json(ARQ_POMODORO, [])
    novo = {
        "id": str(uuid.uuid4()),
        "label": label.strip(),
        "minutes": int(focus_minutes),
        "finished_at": datetime.now(timezone.utc).isoformat(),
    }
    items.append(novo)
    write_json(ARQ_POMODORO, items)
    return novo


def pomodoro_stats(days: int = 7) -> Dict[str, Any]:
    items = read_json(ARQ_POMODORO, [])
    from datetime import timedelta
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    recent = []
    for it in items:
        try:
            t = datetime.fromisoformat(it["finished_at"].replace("Z", "+00:00"))
            if t >= cutoff:
                recent.append(it)
        except Exception:
            continue
    total_min = sum(x.get("minutes", 0) for x in recent)
    by_day = {}
    for it in recent:
        d = it["finished_at"][:10]
        by_day[d] = by_day.get(d, 0) + it.get("minutes", 0)
    return {
        "sessions": len(recent),
        "total_minutes": total_min,
        "total_hours": round(total_min / 60, 1),
        "by_day": by_day,
        "last_7d_items": sorted(recent, key=lambda x: x["finished_at"], reverse=True)[:20],
    }
