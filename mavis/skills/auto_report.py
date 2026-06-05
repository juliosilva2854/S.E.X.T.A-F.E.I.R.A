"""
mavis.skills.auto_report — Geradores automáticos:
  - SEMANAL (legado, sexta às 18h): resumo da semana, com foco em KM/operação.
  - MENSAL MACRO (novo, dia 1º às 8h): visão executiva do mês fechado.
    Narrativa Gemini focada em ATENDIMENTOS, padrões e tendências — NÃO em KM/combustível.

Os PDFs ficam em /app/relatorios_gerados/, e os metadados em /app/auto_report_config.json.
"""
import os
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional

from mavis.core.storage import read_json, write_json
from mavis.core.paths import ARQUIVO_RELATORIOS, APP_ROOT
from mavis.skills import analytics
from mavis.skills import analytics_export as ex


# ==============================================================
# SEMANAL (legado — mantém compatibilidade total)
# ==============================================================
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
    """Pega a última semana das estatísticas e salva como relatório no banco."""
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
    for r in data:
        if r.get("periodo") == rel["periodo"]:
            return {"skipped": True, "reason": "já existe", "existing_id": r.get("id")}
    data.append(rel)
    write_json(ARQUIVO_RELATORIOS, data)
    return {"created": True, "report": rel}


# ==============================================================
# CONFIG (semanal + mensal)
# ==============================================================
REPORTS_DIR = Path(APP_ROOT) / "relatorios_gerados"
CONFIG_FILE = str(Path(APP_ROOT) / "auto_report_config.json")

DEFAULT_CONFIG: Dict[str, Any] = {
    # Semanal (legado)
    "enabled": False,
    "day_of_week": "fri",
    "hour": 18,
    "minute": 0,
    "period_days": 7,
    "send_whatsapp": False,
    "whatsapp_destination_id": None,   # NOVO: id do favorito (preferido sobre WHATSAPP_GRUPO)
    "last_run": None,
    "history": [],
    # Mensal MACRO (novo)
    "monthly_enabled": False,
    "monthly_day": 1,                  # dia do mês (1-28)
    "monthly_hour": 8,
    "monthly_minute": 0,
    "monthly_send_whatsapp": False,
    "monthly_whatsapp_destination_id": None,
    "monthly_last_run": None,
    "monthly_history": [],
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
    allowed = (
        "enabled", "day_of_week", "hour", "minute", "period_days",
        "send_whatsapp", "whatsapp_destination_id",
        "monthly_enabled", "monthly_day", "monthly_hour", "monthly_minute",
        "monthly_send_whatsapp", "monthly_whatsapp_destination_id",
    )
    for k in allowed:
        if k in patch and patch[k] is not None:
            cfg[k] = patch[k]
    # Validações leves
    if not (1 <= int(cfg.get("monthly_day", 1)) <= 28):
        cfg["monthly_day"] = 1
    write_json(CONFIG_FILE, cfg)
    return cfg


def cron_expr() -> Dict[str, Any]:
    cfg = get_config()
    return {"day_of_week": cfg["day_of_week"], "hour": int(cfg["hour"]), "minute": int(cfg["minute"])}


def cron_expr_monthly() -> Dict[str, Any]:
    cfg = get_config()
    return {"day": int(cfg["monthly_day"]), "hour": int(cfg["monthly_hour"]),
            "minute": int(cfg["monthly_minute"])}


def list_reports() -> List[Dict[str, Any]]:
    return list(reversed(get_config().get("history", [])))[:50]


def list_monthly_reports() -> List[Dict[str, Any]]:
    return list(reversed(get_config().get("monthly_history", [])))[:50]


def report_path(filename: str) -> Path:
    return REPORTS_DIR / os.path.basename(filename)


# ==============================================================
# GERAÇÃO SEMANAL (PDF + texto resumo)
# ==============================================================
def _resolve_whatsapp_destination(destination_id: Optional[str], fallback_grupo: str) -> Optional[str]:
    """Resolve o nome do destino a partir do favorito (preferido) ou do WHATSAPP_GRUPO."""
    if destination_id:
        try:
            from mavis.skills import whatsapp_favorites as wf
            fav = wf.get(destination_id)
            if fav:
                return fav["nome"]
        except Exception:
            pass
    return fallback_grupo or None


def generate_and_store(period_days: Optional[int] = None, titulo: str = "",
                       fuel_cost_per_liter: float = 5.89, km_per_liter: float = 10.0) -> Dict[str, Any]:
    """Gera resumo (texto) + PDF semanal e salva em disco."""
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
    kpis = analytics.kpis_filtered(start=start, end=end,
                                   fuel_cost_per_liter=fuel_cost_per_liter,
                                   km_per_liter=km_per_liter)
    pdf = ex.to_pdf(rows, kpis, filtro={"start": start, "end": end})

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    stamp = end_dt.strftime("%Y%m%d_%H%M%S")
    filename = f"relatorio_{stamp}.pdf"
    (REPORTS_DIR / filename).write_bytes(pdf)
    (REPORTS_DIR / f"resumo_{stamp}.txt").write_text(resumo, encoding="utf-8")

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
        dest = _resolve_whatsapp_destination(
            cfg.get("whatsapp_destination_id"),
            os.environ.get("WHATSAPP_GRUPO", ""),
        )
        whatsapp_status = _try_send_whatsapp(resumo, dest)

    return {**entry, "resumo": resumo, "kpis": kpis, "whatsapp": whatsapp_status}


def _try_send_whatsapp(texto: str, destino: Optional[str]) -> str:
    """Envio via skill desktop. Só funciona com DESKTOP_MODE=1 + destino válido."""
    if not destino:
        return "sem_destino"
    try:
        from mavis.skills import whatsapp as wa
        res = wa.send_message(destino, texto)
        return "ok" if res.get("ok") else f"erro: {res.get('error')}"
    except Exception as e:  # pragma: no cover
        return f"erro: {e}"


# ==============================================================
# GERAÇÃO MENSAL MACRO (novo)
# ==============================================================
def _gemini_monthly_narrative(macro: Dict[str, Any]) -> str:
    """Narrativa macro do mês com foco em OPERAÇÕES (não KM/combustível)."""
    chave = os.environ.get("CHAVE_GEMINI", "")
    if not chave:
        return _fallback_monthly(macro)
    try:
        from google import genai
        client = genai.Client(api_key=chave)
        model = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

        cur = macro.get("current") or {}
        prev = macro.get("previous") or {}
        d = macro.get("deltas") or {}
        top_un = cur.get("top_unidades", []) or []
        top_eq = cur.get("top_equipamentos", []) or []

        def fmt_d(v):
            return "—" if v is None else (f"+{v}%" if v > 0 else f"{v}%")

        unidades_block = "\n".join(f"  - {u['unidade']}: {u['visitas']} visitas" for u in top_un) or "  - (sem dados)"
        equip_block = "\n".join(f"  - {e['item']}: {e['qtd']}x" for e in top_eq) or "  - (sem dados)"

        prompt = f"""Você é o assistente Sexta-feira. Gere um RESUMO MENSAL EXECUTIVO em português, com VISÃO MACRO
focada em INSIGHTS OPERACIONAIS sobre atendimentos, padrões de visita e tipos de intervenção.

REGRAS CRÍTICAS:
- NÃO foque em KM rodado, combustível ou logística de transporte. Nem mencione esses temas.
- Foque em: VOLUME de atendimentos, DISTRIBUIÇÃO entre unidades, CONCENTRAÇÃO de visitas,
  TIPOS de intervenção (preventiva vs corretiva vs entrega), padrões emergentes,
  comparativo com o mês anterior em termos de carga operacional.
- Tom corporativo, conciso, sem emojis nem markdown extravagante.
- Identifique TENDÊNCIAS e PADRÕES interpretando os dados — não apenas repita números crus.

DADOS DO MÊS {macro.get('month','')}:
- Preventivas: {cur.get('preventivas',0)} (vs {prev.get('preventivas',0)} no mês anterior · {fmt_d(d.get('preventivas'))})
- Atendimentos técnicos: {cur.get('atendimentos',0)} (vs {prev.get('atendimentos',0)} · {fmt_d(d.get('atendimentos'))})
- Entregas de insumos: {cur.get('entregas',0)} (vs {prev.get('entregas',0)} · {fmt_d(d.get('entregas'))})
- Trocas / substituições: {cur.get('trocas',0)} (vs {prev.get('trocas',0)} · {fmt_d(d.get('trocas'))})
- Configurações: {cur.get('configuracoes',0)} (vs {prev.get('configuracoes',0)} · {fmt_d(d.get('configuracoes'))})
- Visitas totais em unidades: {cur.get('visitas',0)} (vs {prev.get('visitas',0)} · {fmt_d(d.get('visitas'))})
- Dias úteis trabalhados: {cur.get('dias_uteis',0)} (vs {prev.get('dias_uteis',0)} · {fmt_d(d.get('dias_uteis'))})

TOP 5 UNIDADES VISITADAS:
{unidades_block}

TOP 3 EQUIPAMENTOS MANUSEADOS:
{equip_block}

Concentração: {round(macro.get('concentracao_top3', 0) * 100, 1)}% das visitas foram nas top3 unidades.

ESTRUTURA OBRIGATÓRIA (em 4 blocos curtos, separados por linha em branco):
1) Síntese (2-3 frases): panorama executivo do mês em volume e tipo de operação.
2) Insights operacionais (3 bullets, formato "- "): padrões, concentrações, anomalias relevantes em ATENDIMENTOS.
3) Comparativo macro (2-3 frases): como o mês evoluiu vs o anterior em carga e tipo de operação.
4) Atenção (1-2 bullets, se houver padrão a observar — concentração excessiva, alta em trocas, etc.).
"""
        resp = client.models.generate_content(model=model, contents=prompt)
        return (resp.text or "").strip() or _fallback_monthly(macro)
    except Exception:
        return _fallback_monthly(macro)


def _fallback_monthly(macro: Dict[str, Any]) -> str:
    cur = macro.get("current") or {}
    top = ", ".join(u["unidade"] for u in (cur.get("top_unidades") or [])[:3]) or "—"
    return (
        f"Resumo Mensal {macro.get('month','')}\n\n"
        f"Operação: {cur.get('atendimentos',0)} atendimentos técnicos · "
        f"{cur.get('preventivas',0)} preventivas · "
        f"{cur.get('entregas',0)} entregas de insumos · "
        f"{cur.get('trocas',0)} trocas em {cur.get('dias_uteis',0)} dias úteis.\n\n"
        f"Top unidades: {top}."
    )


def _format_monthly_text(macro: Dict[str, Any], narrativa: str) -> str:
    """Texto pronto para WhatsApp/clipboard a partir do macro + narrativa."""
    cur = macro.get("current") or {}
    d = macro.get("deltas") or {}

    def fmt_d(v):
        if v is None:
            return ""
        return f" ({'+' if v > 0 else ''}{v}% vs mês anterior)"

    top3 = (cur.get("top_unidades") or [])[:3]
    top_str = " · ".join(f"{u['unidade']} ({u['visitas']}x)" for u in top3) or "—"

    linhas = [
        f"*RESUMO MENSAL — {macro.get('month','')}*",
        "",
        f"Atendimentos técnicos: *{cur.get('atendimentos',0)}*{fmt_d(d.get('atendimentos'))}",
        f"Preventivas: *{cur.get('preventivas',0)}*{fmt_d(d.get('preventivas'))}",
        f"Entregas de insumos: *{cur.get('entregas',0)}*{fmt_d(d.get('entregas'))}",
        f"Trocas / substituições: *{cur.get('trocas',0)}*{fmt_d(d.get('trocas'))}",
        f"Dias úteis: {cur.get('dias_uteis',0)}",
        "",
        f"Top destinos: {top_str}",
        f"Concentração top3: {round(macro.get('concentracao_top3',0)*100,1)}%",
    ]
    if narrativa:
        linhas.append("")
        linhas.append("— Análise —")
        linhas.append(narrativa.strip())
    return "\n".join(linhas)


def generate_monthly(month_str: Optional[str] = None,
                     destination_id: Optional[str] = None) -> Dict[str, Any]:
    """Gera resumo MACRO mensal (PDF + texto) e salva.
    Se month_str=None, usa o mês anterior fechado.
    destination_id (opcional) sobrescreve o destino padrão do config.
    """
    if not month_str:
        today = datetime.now()
        first_of_this = today.replace(day=1)
        last_day_prev = first_of_this - timedelta(days=1)
        month_str = last_day_prev.strftime("%Y-%m")

    macro = analytics.monthly_macro(month_str)
    narrativa = _gemini_monthly_narrative(macro)
    pdf = ex.to_pdf_macro(macro, narrativa)

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"resumo_mensal_{month_str}_{stamp}.pdf"
    (REPORTS_DIR / filename).write_bytes(pdf)

    texto = _format_monthly_text(macro, narrativa)
    (REPORTS_DIR / f"resumo_mensal_{month_str}_{stamp}.txt").write_text(texto, encoding="utf-8")

    cfg = get_config()
    entry = {
        "filename": filename,
        "month": month_str,
        "gerado_em": datetime.now().isoformat(),
        "total_atendimentos": (macro.get("current") or {}).get("atendimentos", 0),
        "total_preventivas": (macro.get("current") or {}).get("preventivas", 0),
        "titulo": f"Resumo Mensal {month_str}",
    }
    cfg["monthly_last_run"] = entry["gerado_em"]
    cfg.setdefault("monthly_history", []).append(entry)
    cfg["monthly_history"] = cfg["monthly_history"][-50:]
    write_json(CONFIG_FILE, cfg)

    whatsapp_status = "skip"
    if (destination_id or cfg.get("monthly_send_whatsapp")) and os.environ.get("DESKTOP_MODE") == "1":
        dest = _resolve_whatsapp_destination(
            destination_id or cfg.get("monthly_whatsapp_destination_id"),
            os.environ.get("WHATSAPP_GRUPO", ""),
        )
        whatsapp_status = _try_send_whatsapp(texto, dest)

    return {**entry, "texto": texto, "macro": macro, "narrativa": narrativa,
            "whatsapp": whatsapp_status}
