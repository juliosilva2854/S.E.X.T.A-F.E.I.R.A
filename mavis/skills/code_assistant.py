"""
mavis.skills.code_assistant — Assistente de código via Gemini.
Gera, explica, revisa, refatora, e converte código.
"""
import os
from typing import Optional

CHAVE_GEMINI = os.environ.get("CHAVE_GEMINI", "")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")


def _gemini(prompt: str) -> str:
    if not CHAVE_GEMINI:
        return "Sem chave Gemini configurada."
    from google import genai
    client = genai.Client(api_key=CHAVE_GEMINI)
    resp = client.models.generate_content(model=GEMINI_MODEL, contents=prompt)
    return (resp.text or "").strip()


def generate(prompt: str, language: str = "python") -> str:
    p = (
        f"Você é um engenheiro de software sênior. Gere código {language} "
        f"limpo, idiomático e bem comentado para resolver o seguinte. "
        f"Retorne APENAS o código dentro de um bloco ```{language} ... ``` "
        f"e, abaixo do bloco, uma explicação curta em português.\n\n"
        f"PEDIDO: {prompt}"
    )
    return _gemini(p)


def explain(code: str, language: str = "auto") -> str:
    p = (
        "Explique o código abaixo em português, parte por parte, de forma didática "
        "mas concisa. Inclua complexidade Big-O quando relevante e aponte qualquer "
        "bug/má prática.\n\n"
        f"```{language}\n{code}\n```"
    )
    return _gemini(p)


def review(code: str, language: str = "auto") -> str:
    p = (
        "Faça uma code review do código abaixo em português. Liste problemas separados em "
        "BUGS (críticos), MELHORIAS (refatoração), SEGURANÇA, e DESEMPENHO. Seja específico "
        "(cite linhas/blocos). Ao final, sugira uma versão melhorada em bloco de código.\n\n"
        f"```{language}\n{code}\n```"
    )
    return _gemini(p)


def refactor(code: str, instruction: str, language: str = "auto") -> str:
    p = (
        f"Refatore o código abaixo seguindo a instrução: '{instruction}'. "
        f"Mantenha a funcionalidade. Retorne APENAS o novo código em ```{language} ... ``` "
        f"e uma explicação curta abaixo sobre as mudanças.\n\n"
        f"```{language}\n{code}\n```"
    )
    return _gemini(p)


def convert(code: str, from_lang: str, to_lang: str) -> str:
    p = (
        f"Converta o código abaixo de {from_lang} para {to_lang}. "
        f"Preserve a lógica e a clareza. Retorne só o bloco ```{to_lang} ... ``` e uma "
        f"nota breve sobre diferenças idiomáticas.\n\n"
        f"```{from_lang}\n{code}\n```"
    )
    return _gemini(p)


def debug(code: str, error_message: str, language: str = "auto") -> str:
    p = (
        f"Debugue o código abaixo. O erro reportado é:\n{error_message}\n\n"
        f"Identifique a causa raiz, explique em português e mostre a correção em "
        f"```{language} ... ```.\n\n"
        f"```{language}\n{code}\n```"
    )
    return _gemini(p)
