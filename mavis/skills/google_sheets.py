"""
mavis.skills.google_sheets — Sincroniza a planilha KM do Julio Cesar (Google Sheets)
e mantém um cache local estruturado (sheets_cache.json) que alimenta o Analytics.

Planilha: "Planilha KM - Julio Cesar MTFL"
ID:        1BkAHzN9aoWOyb0iZXAlcTvkaj0mFd7AyPohDa0Sbhn4
Abas:      Jan-26, Fev-26, ..., Maio-26, Jun-26 (mensais)
Colunas:   A=Data  B=Origem  C=??  D=Destino  E=??  F=Tipo Visita  G=Ticket  H=KM

Estratégia de auth (em ordem):
1) OAuth do usuário via mavis.skills.google_auth (usa google_token.json)
2) Service Account legada via credenciais.json + oauth2client (compat com relatorios.py)
"""
import os
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

from mavis.core.storage import read_json, write_json
from mavis.core.paths import ARQUIVO_SHEETS_CACHE, ARQUIVO_CREDENCIAIS_GOOGLE


PLANILHA_NOME = os.environ.get("PLANILHA_NOME", "Planilha KM - Julio Cesar MTFL")
PLANILHA_ID = os.environ.get(
    "PLANILHA_ID", "1BkAHzN9aoWOyb0iZXAlcTvkaj0mFd7AyPohDa0Sbhn4"
)

# Linha (1-based) onde realmente começam os dados (header até linha 5 conforme planilhas.py)
DATA_ROW_START = 6


# ==========================================
# AUTH — tenta OAuth do usuário, cai pra Service Account
# ==========================================
def _gspread_client():
    """Retorna um cliente gspread autenticado. Lança RuntimeError se falhar."""
    import gspread

    # 1) OAuth do usuário (modo Mavis padrão)
    try:
        from mavis.skills import google_auth
        creds = google_auth.get_credentials()
        return gspread.authorize(creds)
    except Exception as e:
        logging.info(f"[sheets] OAuth do usuário indisponível: {e}")

    # 2) Service Account (formato legacy de relatorios.py / planilhas.py)
    if os.path.exists(ARQUIVO_CREDENCIAIS_GOOGLE):
        try:
            from oauth2client.service_account import ServiceAccountCredentials
            escopos = [
                "https://spreadsheets.google.com/feeds",
                "https://www.googleapis.com/auth/drive",
            ]
            sa = ServiceAccountCredentials.from_json_keyfile_name(
                ARQUIVO_CREDENCIAIS_GOOGLE, escopos
            )
            return gspread.authorize(sa)
        except Exception as e:
            logging.info(f"[sheets] Service Account falhou: {e}")

    raise RuntimeError(
        "Sem credenciais Google. Faça login OAuth pelo painel (/google) "
        "ou coloque credenciais.json (Service Account) na raiz do projeto."
    )


# ==========================================
# PARSING — converte linha bruta da planilha em registro estruturado
# ==========================================
def _parse_date(raw: str) -> Optional[str]:
    """'10/06/2026' -> '2026-06-10'  (ISO date)."""
    if not raw:
        return None
    raw = raw.strip()
    for fmt in ("%d/%m/%Y", "%d/%m/%y", "%Y-%m-%d"):
        try:
            return datetime.strptime(raw, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def _to_float(raw: str) -> float:
    if not raw:
        return 0.0
    s = (raw or "").strip().replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return 0.0


def _row_to_record(row: List[str], aba: str) -> Optional[Dict[str, Any]]:
    """Converte uma linha bruta (lista de strings) em dict estruturado."""
    if not row or len(row) < 4:
        return None

    data_iso = _parse_date(row[0] if len(row) > 0 else "")
    if not data_iso:
        return None

    origem = (row[1] if len(row) > 1 else "").strip().upper()
    destino = (row[3] if len(row) > 3 else "").strip().upper()
    if not origem and not destino:
        return None

    tipo = (row[5] if len(row) > 5 else "").strip()
    ticket = (row[6] if len(row) > 6 else "").strip()
    km = _to_float(row[7] if len(row) > 7 else "")

    return {
        "data": data_iso,
        "origem": origem,
        "destino": destino,
        "tipo": tipo,           # "Preventiva", "Atendimento", etc
        "ticket": ticket,
        "km": km,
        "aba": aba,
    }


# ==========================================
# SYNC — varre todas as abas mensais e salva cache
# ==========================================
def sync_all() -> Dict[str, Any]:
    """Lê TODAS as abas da planilha e salva em sheets_cache.json.

    Retorna {ok, total_rows, abas, last_sync, planilha}.
    """
    try:
        client = _gspread_client()
    except Exception as e:
        return {"ok": False, "error": str(e)}

    try:
        try:
            planilha = client.open_by_key(PLANILHA_ID)
        except Exception:
            planilha = client.open(PLANILHA_NOME)
    except Exception as e:
        return {"ok": False, "error": f"Planilha não acessível: {e}"}

    todas: List[Dict[str, Any]] = []
    abas_info: List[Dict[str, Any]] = []

    for ws in planilha.worksheets():
        nome_aba = ws.title
        try:
            rows = ws.get_all_values()
        except Exception as e:
            abas_info.append({"aba": nome_aba, "erro": str(e), "linhas": 0})
            continue

        registros_aba = 0
        for i, row in enumerate(rows, start=1):
            if i < DATA_ROW_START:
                continue
            rec = _row_to_record(row, nome_aba)
            if rec:
                todas.append(rec)
                registros_aba += 1

        abas_info.append({"aba": nome_aba, "linhas": registros_aba})

    # Ordena por data ascendente
    todas.sort(key=lambda r: r["data"])

    cache = {
        "last_sync": datetime.now().isoformat(),
        "planilha": planilha.title,
        "planilha_id": PLANILHA_ID,
        "abas": abas_info,
        "total_rows": len(todas),
        "rows": todas,
    }
    write_json(ARQUIVO_SHEETS_CACHE, cache)

    return {
        "ok": True,
        "total_rows": len(todas),
        "abas": abas_info,
        "last_sync": cache["last_sync"],
        "planilha": planilha.title,
    }


# ==========================================
# READERS — usados pelo Analytics
# ==========================================
def read_cache() -> Dict[str, Any]:
    """Retorna o cache atual (ou vazio se nunca sincronizado)."""
    return read_json(ARQUIVO_SHEETS_CACHE, {
        "last_sync": None,
        "planilha": None,
        "abas": [],
        "total_rows": 0,
        "rows": [],
    })


def get_rows(start: str = "", end: str = "", unidade: str = "") -> List[Dict[str, Any]]:
    """Retorna linhas filtradas por data (ISO YYYY-MM-DD) e/ou unidade (origem ou destino)."""
    cache = read_cache()
    rows = cache.get("rows", [])

    if start:
        rows = [r for r in rows if r["data"] >= start]
    if end:
        rows = [r for r in rows if r["data"] <= end]
    if unidade:
        u = unidade.upper().strip()
        rows = [r for r in rows if u in r["origem"] or u in r["destino"]]

    return rows


def status() -> Dict[str, Any]:
    """Status resumido do cache para a UI."""
    cache = read_cache()
    return {
        "configured": bool(cache.get("last_sync")),
        "last_sync": cache.get("last_sync"),
        "planilha": cache.get("planilha"),
        "total_rows": cache.get("total_rows", 0),
        "abas": cache.get("abas", []),
    }
