"""
mavis.skills.env_manager — Lê/escreve backend/.env com segurança.
Whitelist de chaves editáveis. Chaves sensíveis: gravam mas só retornam mascaradas.
"""
import os
import re
from pathlib import Path
from typing import Dict, Any

ENV_FILE = Path(__file__).resolve().parent.parent.parent / "backend" / ".env"

EDITABLE = {
    # display key, sensitive?
    "CHAVE_GEMINI":           {"sensitive": True,  "label": "Chave Gemini"},
    "GEMINI_MODEL":           {"sensitive": False, "label": "Modelo Gemini"},
    "NOME_IA":                {"sensitive": False, "label": "Nome da IA"},
    "VOZ_SINTETIZADOR":       {"sensitive": False, "label": "Voz neural"},
    "PAUSE_THRESHOLD":        {"sensitive": False, "label": "Pause threshold (s)"},
    "MAVIS_PERSONALITY":      {"sensitive": False, "label": "Personalidade"},
    "MAVIS_PROATIVO":         {"sensitive": False, "label": "Modo proativo (1/0)"},
    "MAVIS_AUTO_WEEKLY":      {"sensitive": False, "label": "Resumo semanal automático (1/0)"},
    "MAVIS_AUTO_WEEKLY_HOUR": {"sensitive": False, "label": "Hora do resumo semanal (0-23)"},
    "MAVIS_KM_PER_LITER":     {"sensitive": False, "label": "km/L do veículo"},
    "MAVIS_FUEL_COST":        {"sensitive": False, "label": "R$ por litro"},
    "FIELDCONTROL_EMAIL":     {"sensitive": False, "label": "Email FieldControl"},
    "FIELDCONTROL_SENHA":     {"sensitive": True,  "label": "Senha FieldControl"},
    "WHATSAPP_NUMERO":        {"sensitive": False, "label": "WhatsApp número"},
    "WHATSAPP_GRUPO":         {"sensitive": False, "label": "WhatsApp grupo"},
    "PLANILHA_NOME":          {"sensitive": False, "label": "Nome da planilha Google"},
    "WAHA_URL":               {"sensitive": False, "label": "URL do WAHA"},
    "WAHA_API_KEY":           {"sensitive": True,  "label": "API Key do WAHA"},
    "WAHA_SESSION":           {"sensitive": False, "label": "Sessão WAHA"},
    "MAVIS_SHEETS_AUTOSYNC":      {"sensitive": False, "label": "Auto-sync Sheets (1/0)"},
    "MAVIS_SHEETS_AUTOSYNC_HOUR": {"sensitive": False, "label": "Hora auto-sync Sheets (0-23)"},
}


def _read_raw() -> Dict[str, str]:
    if not ENV_FILE.exists():
        return {}
    out = {}
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            k, v = line.split("=", 1)
            out[k.strip()] = v.strip()
    return out


def _mask(v: str) -> str:
    if not v:
        return ""
    if len(v) <= 8:
        return "•" * len(v)
    return v[:4] + "•" * (len(v) - 8) + v[-4:]


def get_all() -> Dict[str, Any]:
    """Retorna configs editáveis (sensíveis mascaradas)."""
    raw = _read_raw()
    items = []
    for key, meta in EDITABLE.items():
        v = raw.get(key, "")
        items.append({
            "key": key,
            "label": meta["label"],
            "sensitive": meta["sensitive"],
            "value": _mask(v) if meta["sensitive"] else v,
            "is_set": bool(v),
        })
    return {"items": items}


def update(patch: Dict[str, str]) -> Dict[str, Any]:
    """Atualiza um conjunto de chaves no .env. Cria backup .env.bak antes."""
    raw = _read_raw()
    invalidos = [k for k in patch if k not in EDITABLE]
    if invalidos:
        raise ValueError(f"Chaves não editáveis: {invalidos}")
    for k, v in patch.items():
        if v is None or v == "":
            continue
        raw[k] = str(v).strip()
        os.environ[k] = str(v).strip()
    # Backup + write
    if ENV_FILE.exists():
        bak = ENV_FILE.parent / ".env.bak"
        bak.write_text(ENV_FILE.read_text(encoding="utf-8"), encoding="utf-8")
    lines = [f"{k}={v}" for k, v in raw.items()]
    ENV_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"ok": True, "updated_keys": list(patch.keys())}


# Alias para chamadas a partir do server.py
update_env = update
