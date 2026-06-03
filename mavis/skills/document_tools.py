"""
mavis.skills.document_tools — Resumo, tradução, reescrita, análise de texto.
"""
import os

CHAVE_GEMINI = os.environ.get("CHAVE_GEMINI", "")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")


def _gemini(prompt: str) -> str:
    if not CHAVE_GEMINI:
        return "Sem chave Gemini configurada."
    from google import genai
    client = genai.Client(api_key=CHAVE_GEMINI)
    resp = client.models.generate_content(model=GEMINI_MODEL, contents=prompt)
    return (resp.text or "").strip()


def summarize(text: str, mode: str = "executivo") -> str:
    """mode: 'executivo' (3 bullets) | 'detalhado' (parágrafo) | 'tldr' (1 frase)"""
    instr = {
        "executivo": "Resuma em 3 a 5 bullets curtos (sem markdown, use traços).",
        "detalhado": "Resuma em 2 parágrafos curtos.",
        "tldr": "TL;DR em uma única frase concisa.",
    }.get(mode, "Resuma em bullets.")
    return _gemini(f"{instr}\n\nTexto:\n{text}")


def translate(text: str, to_lang: str = "inglês") -> str:
    return _gemini(
        f"Traduza o texto abaixo para {to_lang}, preservando tom e termos técnicos. "
        f"Retorne só a tradução, sem comentários.\n\nTexto:\n{text}"
    )


def rewrite(text: str, tone: str = "formal") -> str:
    """tone: 'formal' | 'casual' | 'criativo' | 'técnico' | 'persuasivo'"""
    return _gemini(
        f"Reescreva o texto abaixo em tom {tone}, em português. Mantenha o significado. "
        f"Retorne só o texto reescrito.\n\nOriginal:\n{text}"
    )


def key_points(text: str) -> str:
    return _gemini(
        "Extraia os pontos-chave do texto abaixo em formato de lista numerada. "
        "Cada ponto deve ser uma frase curta.\n\n" + text
    )


def sentiment(text: str) -> str:
    return _gemini(
        "Faça análise de sentimento do texto abaixo. Retorne JSON puro "
        '(sem markdown) com chaves {"score": -1.0 a 1.0, "emocao": str, "resumo": str}.'
        f"\n\nTexto:\n{text}"
    )


def compose_email(intent: str, tone: str = "formal", language: str = "português") -> str:
    return _gemini(
        f"Escreva um email em {language}, tom {tone}, baseado neste pedido: '{intent}'. "
        f"Retorne em formato:\nASSUNTO: ...\n\nCORPO:\n...\n\nSeja conciso e claro."
    )
