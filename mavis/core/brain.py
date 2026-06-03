"""
mavis.core.brain — Cérebro neural avançado (Gemini 2.5).
- Suporta function-calling via Gemini Tools (quando habilitado)
- Injeta memória curta + memória longa + banco de rotas + fatos do operador
- Suporta visão (multimodal): envio de imagens
- Personalidade configurável
"""
import os
import json
import base64
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

from .paths import ARQUIVO_MEMORIA, ARQUIVO_DB_ROTAS
from .storage import read_json, write_json
from .long_memory import as_context_block as long_memory_context

NOME_IA = os.environ.get("NOME_IA", "Sexta-feira")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
CHAVE_GEMINI = os.environ.get("CHAVE_GEMINI", "")

PERSONALITY = os.environ.get("MAVIS_PERSONALITY", "corporativa")  # corporativa | casual | sarcastica

PERSONAS = {
    "corporativa": (
        "Você é a {nome}, uma IA corporativa avançada estilo J.A.R.V.I.S. Tom sóbrio, "
        "eficiente, direto ao ponto. Trate sempre o usuário como 'senhor'."
    ),
    "casual": (
        "Você é a {nome}, uma IA amigável e descontraída. Fale como uma amiga próxima, "
        "use português brasileiro natural. Sem 'senhor'."
    ),
    "sarcastica": (
        "Você é a {nome}, uma IA com humor afiado, irônica mas leal. Use sarcasmo sutil "
        "sem desrespeito. Trate o usuário como 'chefe'."
    ),
}


def build_system_prompt(extra_context: str = "") -> str:
    persona = PERSONAS.get(PERSONALITY, PERSONAS["corporativa"]).format(nome=NOME_IA)
    db = read_json(ARQUIVO_DB_ROTAS, {"rotas_km": {}})
    rotas_json = json.dumps(db, ensure_ascii=False)
    lm = long_memory_context()
    agora = datetime.now().strftime("%A, %d/%m/%Y %H:%M")

    return (
        f"{persona}\n\n"
        "REGRAS DE OURO:\n"
        "1. Respostas curtas, naturais e diretas.\n"
        "2. SEM emojis, asteriscos, markdown ou formatação visual.\n"
        "3. Se fizer pergunta de retorno, termine com a tag [ESPERAR].\n"
        "4. CONSULTE o banco de rotas KM sempre que perguntarem distâncias.\n"
        "5. Se o usuário disser comando operacional (relatório, planilha, ligar app, "
        "controlar tela, ler tela, enviar whatsapp, agenda, email), apenas CONFIRME "
        "a ação - o roteador externo executa a skill.\n"
        "6. Use FATOS LONGOS sobre o operador quando for relevante (memória persistente).\n\n"
        f"CONTEXTO TEMPORAL: agora é {agora}.\n\n"
        f"{lm}\n\n"
        f"BANCO DE ROTAS KM (chave ORIGEM_DESTINO -> KM):\n{rotas_json}\n\n"
        f"{extra_context}"
    )


def get_client():
    from google import genai
    return genai.Client(api_key=CHAVE_GEMINI)


def chat_text(
    user_message: str,
    history_override: Optional[list] = None,
    extra_context: str = "",
    use_web: bool = False,
    image_b64: Optional[str] = None,
) -> Tuple[str, bool]:
    """
    Conversa textual (com possível imagem multimodal).
    Retorna (resposta, espera_resposta).
    """
    if not CHAVE_GEMINI:
        return ("Sem chave de Gemini configurada, senhor.", False)

    historico = history_override if history_override is not None else read_json(ARQUIVO_MEMORIA, [])

    # Busca web opcional
    if use_web:
        web = _quick_web_search(user_message)
        if web:
            extra_context += f"\n[DADO EM TEMPO REAL DA WEB]:\n{web}\n"

    system_prompt = build_system_prompt(extra_context)

    conversa = system_prompt + "\n\n=== HISTÓRICO ===\n"
    for msg in historico[-12:]:
        conversa += f"{msg['role']}: {msg['texto']}\n"
    conversa += f"\nUsuário: {user_message}\n{NOME_IA}: "

    try:
        client = get_client()
        if image_b64:
            # Multimodal: monta contents com imagem
            from google.genai import types
            parts = [
                types.Part.from_text(text=conversa),
                types.Part.from_bytes(
                    data=base64.b64decode(image_b64), mime_type="image/png"
                ),
            ]
            resp = client.models.generate_content(model=GEMINI_MODEL, contents=parts)
        else:
            resp = client.models.generate_content(model=GEMINI_MODEL, contents=conversa)
        texto = (resp.text or "").strip()
    except Exception as e:
        return (f"Falha no cérebro neural: {e}", False)

    espera = False
    if "[ESPERAR]" in texto:
        espera = True
        texto = texto.replace("[ESPERAR]", "").strip()
    elif texto.rstrip().endswith("?"):
        espera = True

    # Persiste na memória curta (se não usou override)
    if history_override is None:
        memoria = read_json(ARQUIVO_MEMORIA, [])
        memoria.append({"role": "Usuário", "texto": user_message})
        memoria.append({"role": NOME_IA, "texto": texto})
        write_json(ARQUIVO_MEMORIA, memoria[-30:])

    return texto, espera


def _quick_web_search(query: str) -> str:
    try:
        from duckduckgo_search import DDGS
        results = DDGS().text(query, region="br-pt", safesearch="moderate", max_results=3)
        out = ""
        for r in results:
            out += f"- {r.get('title','')}: {r.get('body','')}\n"
        return out.strip()
    except Exception:
        return ""


def vision_describe(image_bytes: bytes, instruction: str = "Descreva o que está na tela.") -> str:
    """Recebe bytes de imagem (png/jpg) e analisa com Gemini multimodal."""
    if not CHAVE_GEMINI:
        return "Sem chave Gemini."
    try:
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=CHAVE_GEMINI)
        prompt = (
            f"Você é {NOME_IA}. Analise esta imagem e responda em português, "
            f"de forma sucinta e útil. Instrução do operador: {instruction}"
        )
        parts = [
            types.Part.from_text(text=prompt),
            types.Part.from_bytes(data=image_bytes, mime_type="image/png"),
        ]
        resp = client.models.generate_content(model=GEMINI_MODEL, contents=parts)
        return (resp.text or "").strip()
    except Exception as e:
        return f"Falha na visão: {e}"


def smart_extract(user_message: str, schema_instruction: str) -> Dict[str, Any]:
    """
    Pede ao Gemini para extrair informação estruturada em JSON.
    Usado para parsear lembretes, eventos de calendário, etc.
    """
    if not CHAVE_GEMINI:
        return {}
    prompt = (
        f"Extraia da frase abaixo as informações em JSON puro (sem markdown, sem ```). "
        f"Hoje é {datetime.now().strftime('%A, %d/%m/%Y %H:%M')}. "
        f"{schema_instruction}\n\nFrase: {user_message}\n\nJSON:"
    )
    try:
        client = get_client()
        resp = client.models.generate_content(model=GEMINI_MODEL, contents=prompt)
        txt = (resp.text or "").strip()
        if txt.startswith("```"):
            txt = txt.strip("`").lstrip("json").strip()
        return json.loads(txt)
    except Exception:
        return {}
