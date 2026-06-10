"""
mavis.skills.whatsapp — WhatsApp API via WAHA (invisível e instantâneo).
LEITURA de mensagens não-lidas e ENVIO por contato/grupo (busca inteligente por nome).
Totalmente em background, sem necessidade de janelas ou Playwright.

Configuração via backend/.env:
    WAHA_URL=http://localhost:3001
    WAHA_API_KEY=mavis123
    WAHA_SESSION=default
"""
import os
import base64
import logging
import requests
from typing import List, Dict, Any, Optional


# ==========================================
# Configurações WAHA (lidas do .env, com defaults seguros)
# ==========================================
def _waha_url() -> str:
    return os.environ.get("WAHA_URL", "http://localhost:3001").rstrip("/")


def _waha_session() -> str:
    return os.environ.get("WAHA_SESSION", "default")


def _waha_headers() -> Dict[str, str]:
    return {
        "accept": "application/json",
        "Content-Type": "application/json",
        "X-Api-Key": os.environ.get("WAHA_API_KEY", ""),
    }


def _formatar_numero(numero: str) -> str:
    """Converte um número solto (com ou sem 55) para o formato chatId do WhatsApp."""
    digits = "".join(filter(str.isdigit, numero or ""))
    if not digits:
        return ""
    if len(digits) <= 11:  # falta o DDI
        digits = "55" + digits
    return f"{digits}@c.us"


# ==========================================
# STATUS — saber se a sessão WAHA está conectada
# ==========================================
def status() -> Dict[str, Any]:
    """Consulta o estado da sessão WAHA.

    Retorna algo como:
        {"connected": True, "status": "WORKING", "session": "default", "url": "..."}
    """
    base = _waha_url()
    sess = _waha_session()
    try:
        resp = requests.get(
            f"{base}/api/sessions/{sess}",
            headers=_waha_headers(),
            timeout=8,
        )
        if resp.status_code == 200:
            data = resp.json() or {}
            estado = (data.get("status") or "").upper()
            return {
                "connected": estado == "WORKING",
                "status": estado or "UNKNOWN",
                "session": sess,
                "url": base,
                "engine": (data.get("engine") or {}).get("engine"),
                "ok": True,
            }
        return {
            "connected": False,
            "status": f"HTTP_{resp.status_code}",
            "session": sess,
            "url": base,
            "ok": False,
        }
    except Exception as e:
        return {
            "connected": False,
            "status": "OFFLINE",
            "session": sess,
            "url": base,
            "error": str(e),
            "ok": False,
        }


# ==========================================
# RESOLUÇÃO DE CHATID
# ==========================================
def _get_chat_id_by_name(name_or_number: str) -> Optional[str]:
    """Traduz nome ('João') ou número para o chatId oficial do WhatsApp."""
    # 1) Se for número puro, formata direto
    digits_only = "".join(filter(str.isdigit, name_or_number))
    if len(digits_only) >= 10 and len(digits_only) <= 15:
        return _formatar_numero(digits_only)

    # 2) Texto livre: busca nos chats recentes
    try:
        url = f"{_waha_url()}/api/{_waha_session()}/chats"
        resp = requests.get(url, headers=_waha_headers(), timeout=10)
        if resp.status_code == 200:
            chats = resp.json() or []
            alvo = (name_or_number or "").lower().strip()
            for chat in chats:
                nome = (chat.get("name") or "").lower()
                if alvo and alvo in nome:
                    chat_id = chat.get("id")
                    if isinstance(chat_id, dict):
                        return chat_id.get("_serialized")
                    return chat_id
    except Exception as e:
        logging.error(f"[WAHA] Erro ao buscar contatos: {e}")
    return None


# ==========================================
# LEITURA — não-lidas
# ==========================================
def list_unread(limit: int = 10) -> List[Dict[str, Any]]:
    """Lista chats com mensagens não-lidas."""
    try:
        url = f"{_waha_url()}/api/{_waha_session()}/chats"
        resp = requests.get(url, headers=_waha_headers(), timeout=10)
        resp.raise_for_status()
        chats = resp.json() or []

        out: List[Dict[str, Any]] = []
        for chat in chats:
            unread = chat.get("unreadCount", 0)
            if unread and unread > 0:
                name = (
                    chat.get("name")
                    or (chat.get("id", {}) or {}).get("user")
                    or "Desconhecido"
                )
                out.append({
                    "chat": name,
                    "unread_label": f"{unread} mensagens não lidas",
                    "_count": int(unread),
                })

        out.sort(key=lambda x: x["_count"], reverse=True)
        for o in out:
            o.pop("_count", None)
        return out[:limit]

    except Exception as e:
        logging.error(f"[WAHA] Erro ao listar não lidas: {e}")
        return [{"error": str(e)}]


# ==========================================
# ENVIO — texto
# ==========================================
def send_message(contact: str, message: str) -> Dict[str, Any]:
    """Envia mensagem para contato/grupo por nome ou número via WAHA."""
    try:
        chat_id = _get_chat_id_by_name(contact)
        if not chat_id:
            return {"ok": False, "error": f"Contato ou grupo '{contact}' não encontrado."}

        url = f"{_waha_url()}/api/sendText"
        payload = {
            "chatId": chat_id,
            "text": message,
            "session": _waha_session(),
        }
        resp = requests.post(url, headers=_waha_headers(), json=payload, timeout=15)
        resp.raise_for_status()
        return {"ok": True, "to": contact, "chatId": chat_id, "message": message}

    except Exception as e:
        logging.error(f"[WAHA] Erro ao enviar mensagem: {e}")
        return {"ok": False, "error": str(e)}


# ==========================================
# ENVIO — arquivo (PDF, etc)
# ==========================================
def send_file(numero_ou_nome: str, file_bytes: bytes, filename: str,
              mimetype: str = "application/pdf") -> Dict[str, Any]:
    """Envia um arquivo binário (PDF padrão) via WAHA sendFile.

    Aceita número OU nome (resolve via chat list, igual send_message).
    """
    try:
        chat_id = _get_chat_id_by_name(numero_ou_nome)
        if not chat_id:
            return {"ok": False, "error": f"Destino '{numero_ou_nome}' não encontrado."}

        base64_file = base64.b64encode(file_bytes).decode("utf-8")
        url = f"{_waha_url()}/api/sendFile"
        payload = {
            "chatId": chat_id,
            "session": _waha_session(),
            "file": {
                "mimetype": mimetype,
                "filename": filename,
                "data": base64_file,
            },
        }
        resp = requests.post(url, headers=_waha_headers(), json=payload, timeout=60)
        resp.raise_for_status()
        return {"ok": True, "to": numero_ou_nome, "chatId": chat_id, "filename": filename}

    except Exception as e:
        logging.error(f"[WAHA] Erro ao enviar arquivo: {e}")
        return {"ok": False, "error": str(e)}
