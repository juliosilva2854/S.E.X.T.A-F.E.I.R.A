"""
mavis.core.long_memory — Memória de longo prazo (fatos sobre o usuário).
Estrutura: lista de {id, category, fact, created_at}.
Categorias sugeridas: pessoal, preferencia, trabalho, contato, lugar, agenda, outro.
"""
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any

from .paths import ARQUIVO_LONG_MEMORY
from .storage import read_json, write_json


def list_facts() -> List[Dict[str, Any]]:
    return read_json(ARQUIVO_LONG_MEMORY, [])


def add_fact(category: str, fact: str) -> Dict[str, Any]:
    items = list_facts()
    novo = {
        "id": str(uuid.uuid4()),
        "category": category.lower().strip(),
        "fact": fact.strip(),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    items.append(novo)
    write_json(ARQUIVO_LONG_MEMORY, items)
    return novo


def remove_fact(fact_id: str) -> bool:
    items = list_facts()
    novos = [x for x in items if x.get("id") != fact_id]
    if len(novos) == len(items):
        return False
    write_json(ARQUIVO_LONG_MEMORY, novos)
    return True


def update_fact(fact_id: str, category: str = None, fact: str = None) -> bool:
    items = list_facts()
    for it in items:
        if it.get("id") == fact_id:
            if category is not None:
                it["category"] = category.lower().strip()
            if fact is not None:
                it["fact"] = fact.strip()
            write_json(ARQUIVO_LONG_MEMORY, items)
            return True
    return False


def as_context_block() -> str:
    """Retorna fatos formatados pra injetar no prompt da IA."""
    items = list_facts()
    if not items:
        return ""
    grupos: Dict[str, List[str]] = {}
    for it in items:
        grupos.setdefault(it["category"], []).append(it["fact"])
    out = "FATOS QUE EU SEI SOBRE O OPERADOR (use sempre que pertinente):\n"
    for cat, facts in grupos.items():
        out += f"- [{cat}]: " + " | ".join(facts) + "\n"
    return out
