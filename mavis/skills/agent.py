"""
mavis.skills.agent — Agent Mode autônomo.

Recebe uma meta complexa do usuário, planeja com Gemini quais ferramentas chamar,
executa em loop, e retorna o resultado final sintetizado.

Modelo: planning single-shot + execução sequencial + síntese final.
"""
import os
import json
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Callable

# Catálogo de ferramentas — schema simplificado JSON
TOOLS = [
    {"name": "calendar_today",   "desc": "Lista eventos do Google Calendar de hoje.", "args": {}},
    {"name": "calendar_week",    "desc": "Lista eventos da semana.", "args": {}},
    {"name": "gmail_summary",    "desc": "Resumo dos emails não lidos.", "args": {}},
    {"name": "gmail_unread",     "desc": "Lista emails não lidos com remetente e assunto.", "args": {"max": "int 1-20"}},
    {"name": "weather",          "desc": "Clima atual em São Paulo.", "args": {}},
    {"name": "news_headlines",   "desc": "Manchetes do dia (G1).", "args": {"limit": "int 1-10"}},
    {"name": "web_search",       "desc": "Busca DuckDuckGo (web ao vivo).", "args": {"query": "str"}},
    {"name": "analytics_kpis",   "desc": "KPIs gerais: KM totais, médias, custo combustível.", "args": {}},
    {"name": "analytics_weekly", "desc": "Série semanal de KM/visitas (últimas N semanas).", "args": {"weeks": "int 1-52"}},
    {"name": "analytics_monthly","desc": "Série mensal de KM/visitas.", "args": {"months": "int 1-24"}},
    {"name": "list_reports",     "desc": "Lista relatórios arquivados (preview).", "args": {}},
    {"name": "search_routes",    "desc": "Busca rotas KM por origem/destino.", "args": {"q": "str"}},
    {"name": "system_info",      "desc": "CPU/RAM/Disco/Bateria do servidor.", "args": {}},
    {"name": "list_facts",       "desc": "Lista fatos da memória de longo prazo sobre o operador.", "args": {}},
    {"name": "list_reminders",   "desc": "Lista lembretes ativos.", "args": {}},
    {"name": "knowledge_ask",    "desc": "Pergunta para a Knowledge Base (PDFs/docs).", "args": {"query": "str"}},
    {"name": "summarize_text",   "desc": "Resume um texto longo.", "args": {"text": "str", "mode": "executivo|detalhado|tldr"}},
    {"name": "forex",            "desc": "Cotação USD/EUR/BTC contra BRL.", "args": {"base": "USD|EUR|BTC|GBP", "quote": "BRL"}},
    {"name": "add_reminder",     "desc": "Cria lembrete.", "args": {"text": "str", "when_iso": "YYYY-MM-DDTHH:MM:SS-03:00"}},
    {"name": "add_note",         "desc": "Salva quick note.", "args": {"text": "str", "tag": "str"}},
    {"name": "no_op",            "desc": "Termina o plano (não chama mais ferramentas).", "args": {}},
]

MAX_STEPS = 6


def _gemini_call(prompt: str) -> str:
    chave = os.environ.get("CHAVE_GEMINI", "")
    if not chave:
        return ""
    from google import genai
    client = genai.Client(api_key=chave)
    resp = client.models.generate_content(
        model=os.environ.get("GEMINI_MODEL", "gemini-2.5-flash"),
        contents=prompt,
    )
    return (resp.text or "").strip()


def _plan(goal: str) -> List[Dict[str, Any]]:
    """Pede ao Gemini para planejar quais ferramentas chamar."""
    tools_desc = "\n".join(f"- {t['name']}: {t['desc']} args={t['args']}" for t in TOOLS)
    prompt = (
        f"Você é a Sexta-feira em modo AGENTE AUTÔNOMO. O operador pediu:\n"
        f"=== META ===\n{goal}\n=== /META ===\n\n"
        f"Ferramentas disponíveis (use só essas):\n{tools_desc}\n\n"
        f"Planeje uma sequência de até {MAX_STEPS} chamadas para CUMPRIR a meta. "
        f"Retorne JSON puro, sem markdown, no formato:\n"
        f'{{"plan": [{{"tool": "<nome>", "args": {{...}}, "why": "razão curta"}}, ...]}}\n'
        f"Se não precisar de ferramentas (basta responder do conhecimento), retorne plan=[]."
    )
    raw = _gemini_call(prompt)
    if raw.startswith("```"):
        raw = raw.strip("`").lstrip("json").strip()
    try:
        data = json.loads(raw)
        return data.get("plan", [])[:MAX_STEPS]
    except Exception:
        return []


def _execute(tool_name: str, args: Dict[str, Any]) -> Any:
    """Despacha chamada para a skill correspondente."""
    try:
        if tool_name == "calendar_today":
            from mavis.skills.google_calendar import list_today
            return list_today()
        if tool_name == "calendar_week":
            from mavis.skills.google_calendar import list_week
            return list_week()
        if tool_name == "gmail_summary":
            from mavis.skills.google_gmail import summarize_unread
            return summarize_unread(int(args.get("max", 5)))
        if tool_name == "gmail_unread":
            from mavis.skills.google_gmail import list_unread
            return list_unread(int(args.get("max", 10)))
        if tool_name == "weather":
            from mavis.skills.news_weather import weather
            return weather()
        if tool_name == "news_headlines":
            from mavis.skills.news_weather import headlines
            return headlines("g1", int(args.get("limit", 5)))
        if tool_name == "web_search":
            from duckduckgo_search import DDGS
            return DDGS().text(args.get("query", ""), region="br-pt", max_results=4)
        if tool_name == "analytics_kpis":
            from mavis.skills.analytics import kpis
            return kpis()
        if tool_name == "analytics_weekly":
            from mavis.skills.analytics import weekly_series
            return weekly_series(int(args.get("weeks", 12)))
        if tool_name == "analytics_monthly":
            from mavis.skills.analytics import monthly_series
            return monthly_series(int(args.get("months", 12)))
        if tool_name == "list_reports":
            from mavis.core.storage import read_json
            from mavis.core.paths import ARQUIVO_RELATORIOS
            data = read_json(ARQUIVO_RELATORIOS, [])
            return [{"periodo": r.get("periodo"), "preview": (r.get("conteudo_relatorio") or "")[:240]} for r in data[-10:]]
        if tool_name == "search_routes":
            from mavis.core.storage import read_json
            from mavis.core.paths import ARQUIVO_DB_ROTAS
            db = read_json(ARQUIVO_DB_ROTAS, {"rotas_km": {}})
            q = (args.get("q") or "").upper()
            return [{"key": k, "km": v} for k, v in db.get("rotas_km", {}).items() if q in k][:10]
        if tool_name == "system_info":
            from mavis.skills.system_info import summary
            return summary()
        if tool_name == "list_facts":
            from mavis.core.long_memory import list_facts
            return list_facts()
        if tool_name == "list_reminders":
            from mavis.core.reminders import list_reminders
            return list_reminders(only_active=True)
        if tool_name == "knowledge_ask":
            from mavis.skills.knowledge import ask
            return ask(args.get("query", ""))
        if tool_name == "summarize_text":
            from mavis.skills.document_tools import summarize
            return summarize(args.get("text", ""), args.get("mode", "executivo"))
        if tool_name == "forex":
            from mavis.skills.finance import forex
            return forex(args.get("base", "USD"), args.get("quote", "BRL"))
        if tool_name == "add_reminder":
            from mavis.core.reminders import add_reminder
            return add_reminder(args.get("text", ""), args.get("when_iso", ""), None)
        if tool_name == "add_note":
            from mavis.skills.productivity import add_note
            return add_note(args.get("text", ""), args.get("tag", "agent"))
        if tool_name == "no_op":
            return "terminou"
        return {"error": f"ferramenta desconhecida: {tool_name}"}
    except Exception as e:
        return {"error": str(e)}


def _synthesize(goal: str, steps: List[Dict[str, Any]]) -> str:
    """Pede ao Gemini para sintetizar resultado final a partir dos outputs."""
    if not steps:
        # Sem plano → resposta direta
        return _gemini_call(
            "Você é a Sexta-feira, IA pessoal. Responda à meta abaixo de forma "
            "concisa e direta, em português, tom corporativo, tratando o usuário "
            f"como 'senhor'.\n\nMETA: {goal}"
        )
    contexto = ""
    for i, s in enumerate(steps):
        out = json.dumps(s.get("output"), ensure_ascii=False, default=str)[:1500]
        contexto += f"\n[step {i}: {s['tool']}({s.get('args')})]\n{out}\n"
    prompt = (
        f"Você é a Sexta-feira em modo agente. O operador pediu: '{goal}'\n\n"
        f"Você executou as ferramentas abaixo e obteve:\n{contexto}\n\n"
        f"Agora SINTETIZE a resposta final em português, tom corporativo direto, "
        f"sem markdown extravagante, sem emojis, tratando o usuário como 'senhor'. "
        f"Use os dados das ferramentas. Seja útil e específico. "
        f"Termine com 1 recomendação acionável quando fizer sentido."
    )
    return _gemini_call(prompt)


def run(goal: str, emit: Callable[[str, dict], None] = None) -> Dict[str, Any]:
    """Executa o agente. Se emit fornecido, dispara eventos pra streaming/log."""
    started = datetime.now(timezone.utc).isoformat()
    plan = _plan(goal)
    if emit:
        emit("plan", {"plan": plan})
    steps: List[Dict[str, Any]] = []
    for step in plan:
        tool = step.get("tool")
        args = step.get("args") or {}
        if emit:
            emit("step_start", {"tool": tool, "args": args, "why": step.get("why", "")})
        out = _execute(tool, args)
        record = {"tool": tool, "args": args, "why": step.get("why", ""), "output": out}
        steps.append(record)
        if emit:
            emit("step_done", record)
        if tool == "no_op":
            break
    answer = _synthesize(goal, steps)
    if emit:
        emit("final", {"answer": answer})
    return {
        "id": str(uuid.uuid4()),
        "goal": goal,
        "plan": plan,
        "steps": steps,
        "answer": answer,
        "started": started,
        "finished": datetime.now(timezone.utc).isoformat(),
    }
