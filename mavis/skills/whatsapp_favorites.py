"""
mavis.skills.whatsapp_favorites — Contatos/grupos pré-cadastrados para envio rápido.

Os favoritos são persistidos em /app/whatsapp_favoritos.json e usados:
- Na tela /whatsapp (CRUD)
- No "Compartilhar" do Analytics (dropdown de destino)
- No agendamento de resumo automático (semanal/mensal) como destino padrão
"""
from __future__ import annotations

import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from mavis.core.storage import read_json, write_json
from mavis.core.paths import APP_ROOT

ARQUIVO = str(Path(APP_ROOT) / "whatsapp_favoritos.json")

TIPOS = ("grupo", "contato")


def list_all() -> List[Dict[str, Any]]:
    """Retorna todos os favoritos cadastrados."""
    return read_json(ARQUIVO, [])


def get(fav_id: str) -> Optional[Dict[str, Any]]:
    return next((f for f in list_all() if f.get("id") == fav_id), None)


def get_by_nome(nome: str) -> Optional[Dict[str, Any]]:
    """Busca favorito pelo nome exato do contato/grupo no WhatsApp."""
    nome_lower = (nome or "").strip().lower()
    return next((f for f in list_all() if f.get("nome", "").lower() == nome_lower), None)


def add(nome: str, tipo: str = "grupo", display_name: str = "") -> Dict[str, Any]:
    """Adiciona um favorito. nome = string exata usada na busca do WhatsApp Web.
    display_name = rótulo amigável (default = nome)."""
    nome = (nome or "").strip()
    if not nome:
        raise ValueError("nome obrigatório")
    tipo = tipo if tipo in TIPOS else "grupo"
    if get_by_nome(nome):
        raise ValueError("já existe um favorito com este nome")
    fav: Dict[str, Any] = {
        "id": str(uuid.uuid4()),
        "nome": nome,
        "tipo": tipo,
        "display_name": (display_name or nome).strip(),
        "criado_em": datetime.now().isoformat(),
    }
    data = list_all()
    data.append(fav)
    write_json(ARQUIVO, data)
    return fav


def update(fav_id: str, patch: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    data = list_all()
    found = None
    for f in data:
        if f.get("id") == fav_id:
            for k in ("nome", "tipo", "display_name"):
                if k in patch and patch[k] is not None:
                    f[k] = (patch[k] or "").strip() if isinstance(patch[k], str) else patch[k]
            if f.get("tipo") not in TIPOS:
                f["tipo"] = "grupo"
            found = f
            break
    if not found:
        return None
    write_json(ARQUIVO, data)
    return found


def remove(fav_id: str) -> bool:
    data = list_all()
    new_data = [f for f in data if f.get("id") != fav_id]
    if len(new_data) == len(data):
        return False
    write_json(ARQUIVO, new_data)
    return True


def resolve_destination(favorite_id: Optional[str] = None,
                       nome: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Resolve o destino para envio: favorite_id > nome cadastrado > nome livre.
    Retorna dict {nome, tipo, source} ou None se inválido."""
    if favorite_id:
        fav = get(favorite_id)
        if fav:
            return {"nome": fav["nome"], "tipo": fav["tipo"], "source": "favorite"}
    if nome and nome.strip():
        existing = get_by_nome(nome)
        if existing:
            return {"nome": existing["nome"], "tipo": existing["tipo"], "source": "favorite"}
        return {"nome": nome.strip(), "tipo": "grupo", "source": "manual"}
    return None
