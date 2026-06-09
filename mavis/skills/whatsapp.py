"""
mavis.skills.whatsapp — WhatsApp API via WAHA (invisível e instantâneo).
LEITURA de mensagens não-lidas e ENVIO por contato/grupo (busca inteligente por nome).
Totalmente em background, sem necessidade de janelas ou Playwright.
"""
import requests
import logging
from typing import List, Dict, Any
import base64

# ==========================================
# Configurações WAHA
# ==========================================
WAHA_URL = "http://localhost:3001"
SESSION_NAME = "default"
API_KEY = "mavis123"

HEADERS = {
    "accept": "application/json",
    "Content-Type": "application/json",
    "X-Api-Key": API_KEY
}

def _get_chat_id_by_name(name_or_number: str) -> str:
    """Helper: Traduz um nome (ex: 'João') ou número para o ChatID oficial do WhatsApp."""
    # 1. Se for apenas números, formata como telefone
    digits_only = ''.join(filter(str.isdigit, name_or_number))
    if len(digits_only) >= 10 and len(digits_only) <= 15:
        if len(digits_only) <= 11:
            digits_only = "55" + digits_only
        return f"{digits_only}@c.us"

    # 2. Se for texto (nome de contato ou grupo), busca na lista de chats recentes
    try:
        url = f"{WAHA_URL}/api/{SESSION_NAME}/chats"
        resp = requests.get(url, headers=HEADERS, timeout=10)
        if resp.status_code == 200:
            chats = resp.json()
            for chat in chats:
                chat_name = chat.get("name", "") or ""
                # Faz a busca igual a barra de pesquisa do Whats (ignorando maiúsculas)
                if name_or_number.lower() in chat_name.lower():
                    # Retorna o ID bruto (ex: 5511999999999@c.us ou 120363000@g.us para grupos)
                    return chat.get("id", {}).get("_serialized") or chat.get("id")
    except Exception as e:
        logging.error(f"[WAHA] Erro ao buscar contatos na API: {e}")

    return None # Não encontrou


def list_unread(limit: int = 10) -> List[Dict[str, Any]]:
    """Lista chats com mensagens não-lidas mantendo o formato original da MAVIS."""
    try:
        url = f"{WAHA_URL}/api/{SESSION_NAME}/chats"
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        chats = resp.json()

        out = []
        for chat in chats:
            unread = chat.get("unreadCount", 0)
            if unread > 0:
                name = chat.get("name") or chat.get("id", {}).get("user") or "Desconhecido"
                out.append({
                    "chat": name,
                    "unread_label": f"{unread} mensagens não lidas"
                })

        # Ordena para priorizar quem tem mais mensagens e aplica o limite
        out.sort(key=lambda x: int(x["unread_label"].split()[0]), reverse=True)
        return out[:limit]

    except Exception as e:
        logging.error(f"[WAHA] Erro ao listar não lidas: {e}")
        return [{"error": str(e)}]


def send_message(contact: str, message: str) -> Dict[str, Any]:
    """Envia mensagem para contato/grupo por nome exato (substituto perfeito do Playwright)."""
    try:
        # Pega o ID pesquisando o nome do contato invisivelmente
        chat_id = _get_chat_id_by_name(contact)
        
        if not chat_id:
            return {"ok": False, "error": f"Contato ou grupo '{contact}' não encontrado."}

        url = f"{WAHA_URL}/api/sendText"
        payload = {
            "chatId": chat_id,
            "text": message,
            "session": SESSION_NAME
        }
        
        resp = requests.post(url, headers=HEADERS, json=payload, timeout=15)
        resp.raise_for_status()
        
        return {"ok": True, "to": contact, "message": message}
        
    except Exception as e:
        logging.error(f"[WAHA] Erro ao enviar mensagem: {e}")
        return {"ok": False, "error": str(e)}

def send_file(numero: str, file_bytes: bytes, filename: str):
    """Envia um arquivo (PDF) via WAHA."""
    url = f"{WAHA_URL}/api/sendMedia"
    
    # Converte os bytes do PDF para Base64
    base64_file = base64.b64encode(file_bytes).decode('utf-8')
    
    payload = {
        "chatId": formatar_numero(numero),
        "file": f"data:application/pdf;base64,{base64_file}",
        "filename": filename,
        "session": SESSION_NAME
    }
    
    try:
        resp = requests.post(url, headers=HEADERS, json=payload, timeout=30)
        resp.raise_for_status()
        return {"ok": True}
    except Exception as e:
        logging.error(f"[WAHA] Erro ao enviar arquivo: {e}")
        return {"ok": False, "error": str(e)}