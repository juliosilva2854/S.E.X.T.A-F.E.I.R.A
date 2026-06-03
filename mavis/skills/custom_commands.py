"""
mavis.skills.custom_commands — Comandos personalizados pelo usuário.
Cada comando: {id, pattern (regex case-insensitive), reply, run_action?, args?}
Avaliados ANTES dos intents nativos no router.
"""
import re
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from mavis.core.storage import read_json, write_json
from mavis.core.paths import DATA_DIR

ARQ = str(DATA_DIR / "custom_commands.json")


def list_all() -> List[Dict[str, Any]]:
    items = read_json(ARQ, [])
    items.sort(key=lambda x: x.get("created_at", ""))
    return items


def add(pattern: str, reply: str = "", action: Optional[str] = None,
        args: Optional[Dict[str, Any]] = None, description: str = "") -> Dict[str, Any]:
    # valida regex
    re.compile(pattern, re.I)
    items = read_json(ARQ, [])
    novo = {
        "id": str(uuid.uuid4()),
        "pattern": pattern,
        "reply": reply,
        "action": action,
        "args": args or {},
        "description": description,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    items.append(novo)
    write_json(ARQ, items)
    return novo


def remove(cmd_id: str) -> bool:
    items = read_json(ARQ, [])
    novos = [x for x in items if x["id"] != cmd_id]
    if len(novos) == len(items):
        return False
    write_json(ARQ, novos)
    return True


def match(text: str) -> Optional[Dict[str, Any]]:
    for cmd in list_all():
        try:
            if re.search(cmd["pattern"], text, re.I):
                return cmd
        except re.error:
            continue
    return None
