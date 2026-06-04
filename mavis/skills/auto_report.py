"""
mavis.skills.auto_report — Gerador automático de resumo semanal.
Toda sexta-feira às 18h (configurável), agrega a semana e salva como relatório.
"""
import os
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List
from mavis.core.storage import read_json, write_json
from mavis.core.paths import ARQUIVO_RELATORIOS, APP_ROOT
from mavis.skills import analytics
from mavis.skills import analytics_export as ex


def _gemini_summary(stats: Dict[str, Any]) -> str:
    """Pede ao Gemini um texto narrativo do resumo semanal."""
    chave = os.environ.get("CHAVE_GEMINI", "")
    if not chave:
        return _fallback_summary(stats)
    try:
        from google import genai
        client = genai.Client(api_key=chave)
        model = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
        prompt = (
            "Você é o assistente Sexta-feira. Gere um RESUMO SEMANAL corporativo "
            "em português, conciso, sem emojis ou markdown extravagante, com base "
            "nestes dados:\n\n"
            f"Semana: {stats['semana']}\n"
            f"KM rodados: {stats['km']}\n"
            f"Visitas em unidades: {stats['visitas']}\n"
            f"Dias úteis: {stats['dias_uteis']}\n"
            f"Manutenções preventivas: {stats['preventivas']}\n"
            f"Atendimentos técnicos: {stats['atendimentos']}\n\n"
            "Estrutura: 1) Resumo de 2 linhas. 2) Destaques operacionais (3 bullets). "
            "3) Observação se há padrões/insights. Sóbrio, direto, tom corporativo."
        )
        resp = client.models.generate_content(model=model, contents=prompt)
        return (resp.text or "").strip() or _fallback_summary(stats)
    except Exception:
        return _fallback_summary(stats)


def _fallback_summary(s: Dict[str, Any]) -> str:
    return (
        f"Resumo semana {s['semana']}\n\n"
        f"KM rodados: {s['km']}\n"
        f"Visitas em unidades: {s['visitas']}\n"
        f"Dias úteis: {s['dias_uteis']}\n"
        f"Manutenções preventivas: {s['preventivas']}\n"
        f"Atendimentos técnicos: {s['atendimentos']}\n"
    )


def generate_weekly() -> Dict[str, Any]:
    """Pega a última semana (ou atual) das estatísticas e salva como relatório."""
    weekly = analytics.weekly_series(2)
    if not weekly:
        return {"skipped": True, "reason": "sem dados de semana"}
    stats = weekly[-1]
    texto = _gemini_summary(stats)
    rel = {
        "id": str(uuid.uuid4()),
        "gerado_em": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "periodo": f"AUTO {stats['semana']}",
        "conteudo_relatorio": f"📅 RESUMO AUTOMÁTICO — {stats['semana']}\n\n{texto}\n\n"
                              f"[Métricas: {stats['km']} km · {stats['visitas']} visitas · "
                              f"{stats['preventivas']} prev. · {stats['atendimentos']} atend.]",
        "auto_generated": True,
    }
    data = read_json(ARQUIVO_RELATORIOS, [])
    # Não duplica se já existe um auto-report da mesma semana
    for r in data:
        if r.get("periodo") == rel["periodo"]:
            return {"skipped": True, "reason": "já existe", "existing_id": r.get("id")}
    data.append(rel)
    write_json(ARQUIVO_RELATORIOS, data)
    return {"created": True, "report": rel}


# ==============================================================
# Configuração + agendamento + PDF (relatório automático)
# ==============================================================
REPORTS_DIR = Path(APP_ROOT) / "relatorios_gerados"
CONFIG_FILE = str(Path(APP_ROOT) / "auto_report_config.json")

DEFAULT_CONFIG: Dict[str, Any] = {
    "enabled": False,
    "day_of_week": "fri",     # mon,tue,wed,thu,fri,sat,sun
    "hour": 18,
    "minute": 0,
    "period_days": 7,
    "send_whatsapp": False,
    "last_run": None,
    "history": [],            # [{filename, gerado_em, total_km, periodo, titulo}]
}

WEEKDAYS_PT = {
    "mon": "Segunda", "tue": "Terça", "wed": "Quarta", "thu": "Quinta",
    "fri": "Sexta", "sat": "Sábado", "sun": "Domingo",
}


def get_config() -> Dict[str, Any]:
    cfg = read_json(CONFIG_FILE, {}) or {}
    return {**DEFAULT_CONFIG, **cfg}


def set_config(patch: Dict[str, Any]) -> Dict[str, Any]:
    cfg = get_config()
    for k in ("enabled", "day_of_week", "hour", "minute", "period_days", "send_whatsapp"):
        if k in patch and patch[k] is not None:
            cfg[k] = patch[k]
    write_json(CONFIG_FILE, cfg)
    return cfg


def cron_expr() -> Dict[str, Any]:
    cfg = get_config()
    return {"day_of_week": cfg["day_of_week"], "hour": int(cfg["hour"]), "minute": int(cfg["minute"])}


def list_reports() -> List[Dict[str, Any]]:
    return list(reversed(get_config().get("history", [])))[:50]


def report_path(filename: str) -> Path:
    return REPORTS_DIR / os.path.basename(filename)  # evita path traversal


def generate_and_store(period_days: int | None = None, titulo: str = "",
                       fuel_cost_per_liter: float = 5.89, km_per_liter: float = 10.0) -> Dict[str, Any]:
    """Gera resumo (texto) + PDF do período e salva em disco. Também roda a narrativa Gemini."""
    cfg = get_config()
    days = int(period_days or cfg.get("period_days", 7))
    end_dt = datetime.now()
    start_dt = end_dt - timedelta(days=days)
    start = start_dt.strftime("%Y-%m-%d")
    end = end_dt.strftime("%Y-%m-%d")
    if not titulo:
        titulo = f"Semana {start_dt.strftime('%d/%m')} a {end_dt.strftime('%d/%m')}"

    resumo = analytics.resumo_texto(start=start, end=end, fuel_cost_per_liter=fuel_cost_per_liter,
                                    km_per_liter=km_per_liter, titulo=titulo)
    rows = analytics.export_rows(start=start, end=end)
    kpis = analytics.kpis_filtered(start=start, end=end, fuel_cost_per_liter=fuel_cost_per_liter,
                                   km_per_liter=km_per_liter)
    pdf = ex.to_pdf(rows, kpis, filtro={"start": start, "end": end})

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    stamp = end_dt.strftime("%Y%m%d_%H%M%S")
    filename = f"relatorio_{stamp}.pdf"
    with open(REPORTS_DIR / filename, "wb") as f:
        f.write(pdf)
    with open(REPORTS_DIR / f"resumo_{stamp}.txt", "w", encoding="utf-8") as f:
        f.write(resumo)

    entry = {
        "filename": filename,
        "gerado_em": end_dt.isoformat(),
        "total_km": kpis.get("total_km", 0),
        "periodo": f"{start} a {end}",
        "titulo": titulo,
    }
    cfg["last_run"] = entry["gerado_em"]
    cfg.setdefault("history", []).append(entry)
    cfg["history"] = cfg["history"][-50:]
    write_json(CONFIG_FILE, cfg)

    whatsapp_status = "skip"
    if cfg.get("send_whatsapp") and os.environ.get("DESKTOP_MODE") == "1":
        whatsapp_status = _try_send_whatsapp(resumo)

    return {**entry, "resumo": resumo, "kpis": kpis, "whatsapp": whatsapp_status}


def _try_send_whatsapp(resumo: str) -> str:
    """Envio via skill desktop (Playwright). Só roda com DESKTOP_MODE=1 (PC do usuário)."""
    try:
        from mavis.skills import whatsapp as wa
        grupo = os.environ.get("WHATSAPP_GRUPO", "")
        if not grupo:
            return "sem_grupo"
        res = wa.send_message(grupo, resumo)
        return "ok" if res.get("ok") else f"erro: {res.get('error')}"
    except Exception as e:  # pragma: no cover
        return f"erro: {e}"
