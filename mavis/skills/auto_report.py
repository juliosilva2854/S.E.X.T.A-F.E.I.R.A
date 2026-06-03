"""
mavis.skills.auto_report — Gerador automático de resumo semanal.
Toda sexta-feira às 18h (configurável), agrega a semana e salva como relatório.
"""
import os
import uuid
from datetime import datetime
from typing import Dict, Any
from mavis.core.storage import read_json, write_json
from mavis.core.paths import ARQUIVO_RELATORIOS
from mavis.skills import analytics


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
