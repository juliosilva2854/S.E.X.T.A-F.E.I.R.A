"""
mavis.skills.research — Dossier profundo (multi-step web search + síntese).
"""
import os

CHAVE_GEMINI = os.environ.get("CHAVE_GEMINI", "")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")


def _gemini(prompt: str) -> str:
    if not CHAVE_GEMINI:
        return ""
    from google import genai
    client = genai.Client(api_key=CHAVE_GEMINI)
    resp = client.models.generate_content(model=GEMINI_MODEL, contents=prompt)
    return (resp.text or "").strip()


def _search(query: str, max_results: int = 5):
    try:
        from duckduckgo_search import DDGS
        return DDGS().text(query, region="br-pt", safesearch="moderate", max_results=max_results)
    except Exception:
        return []


def dossier(topic: str, depth: int = 2) -> dict:
    """
    Gera dossier multi-step:
    1) Gera 3-4 subqueries a partir do tópico
    2) Busca cada subquery
    3) Sintetiza tudo em um relatório
    """
    # 1) subqueries
    qs_raw = _gemini(
        f"Liste 4 subperguntas de pesquisa úteis para investigar o tópico abaixo. "
        f"Retorne uma por linha, SEM numeração nem markdown.\n\nTópico: {topic}"
    )
    subqueries = [q.strip(" -•").strip() for q in qs_raw.splitlines() if q.strip()][:4]
    if not subqueries:
        subqueries = [topic]

    # 2) busca cada
    findings = []
    for q in subqueries:
        results = _search(q, max_results=4)
        block = "\n".join(f"- {r.get('title','')}: {r.get('body','')}" for r in results)
        findings.append({"query": q, "results_text": block, "raw": results})

    # 3) sintetiza
    all_text = "\n\n".join(f"### {f['query']}\n{f['results_text']}" for f in findings)
    synthesis = _gemini(
        f"Você é uma analista de inteligência. Com base nas pesquisas abaixo, escreva um "
        f"DOSSIER em português sobre: '{topic}'. Estrutura:\n"
        f"## Resumo Executivo\n## Pontos-Chave\n## Detalhes por Subtópico\n## Recomendações\n"
        f"## Lacunas / O que ainda precisa investigar\n\n"
        f"Use linguagem objetiva, sem emojis ou markdown extravagante.\n\n"
        f"DADOS BRUTOS DA PESQUISA:\n{all_text}"
    )

    return {
        "topic": topic,
        "subqueries": subqueries,
        "findings": findings,
        "dossier": synthesis,
    }
