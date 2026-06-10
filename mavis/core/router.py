"""
mavis.core.router — Roteador de intenções.
Combina:
- Match por keywords (rápido, determinístico) -> skill
- Fallback: Gemini classifica intent + extrai parâmetros
"""
import re
from typing import Dict, Any, Optional


INTENTS = {
    # Computador (desktop apenas)
    "computer.open_app": [
        r"\babre\s+(o|a|os|as)?\s*",
        r"\bligar?\s+(o|a)?\s*",
        r"\bexecut\w+\s+(o|a)?\s*",
    ],
    "computer.close_app": [r"\bfecha\s+", r"\bencerr\w+\s+"],
    "computer.screenshot": [r"\btir\w+\s+print", r"\bcaptur\w+\s+a?\s*tela", r"\bscreenshot\b"],
    "computer.type_text": [r"\bdigit\w+\s+", r"\bescrev\w+\s+(no|na|aqui)\s+"],

    # Visão
    "vision.read_screen": [
        r"\bo que\s+(tem|tá|est[áa])\s+na\s+tela\b",
        r"\bl\w+\s+a\s+tela\b",
        r"\bolh\w+\s+a\s+tela\b",
        r"\bv[êe]\s+a\s+tela\b",
        r"\banalis\w+\s+a\s+tela\b",
    ],

    # Sistema
    "system.battery": [r"\bbateria\b"],
    "system.cpu": [r"\bcpu\b", r"\bprocessador\b"],
    "system.ram": [r"\bram\b", r"\bmem[óo]ria\s+(do\s+pc|do\s+computador|f[íi]sica)\b"],
    "system.shutdown": [r"\bdesligar?\s+o\s+(pc|computador)\b"],
    "system.lock": [r"\btrav\w+\s+o\s+pc\b", r"\bbloque\w+\s+a\s+tela\b"],

    # Whatsapp
    "whatsapp.read_unread": [r"\bmensagens?\s+(do\s+)?whats", r"\btenho\s+mensagens?\b"],
    "whatsapp.send": [r"\bmanda\w*\s+mensagem", r"\benvi\w+\s+mensagem"],

    # Google Calendar
    "calendar.today": [
        r"\bagenda\s+(de\s+)?hoje\b",
        r"\bcompromiss\w+\s+hoje\b",
        r"\breuni\w+\s+hoje\b",
        r"\bo que\s+tenho\s+(hoje|na\s+agenda)\b",
    ],
    "calendar.week": [r"\bagenda\s+(da\s+)?semana\b", r"\bcompromiss\w+\s+(da\s+)?semana\b"],
    "calendar.create": [
        r"\bmarc\w+\s+",
        r"\bagend\w+\s+",
        r"\bcria\w+\s+evento\b",
    ],

    # Gmail
    "gmail.unread": [r"\b(emails?|e-?mails?)\s+n[ãa]o\s+lid", r"\bcaixa\s+de\s+entrada\b"],
    "gmail.summary": [r"\bresumo\s+(dos\s+)?(emails?|e-?mails?)\b"],

    # Drive
    "drive.search": [r"\b(busca|procur\w+)\s+.*\s+(no\s+)?drive\b", r"\barquivos?\s+(do|no)\s+drive\b"],

    # Lembretes
    "reminder.create": [
        r"\bme\s+lembr\w+\s+",
        r"\bcri\w+\s+(um\s+)?lembrete",
        r"\bavise?\s+me\s+",
        r"\balarm\w+",
    ],
    "reminder.list": [r"\blembretes?\b", r"\bagenda\s+de\s+lembrete"],

    # Memória longa
    "memory.save_fact": [
        r"\blembr\w+\s+disso\b",
        r"\bguard\w+\s+(isso|essa\s+informa)",
        r"\bsalv\w+\s+na\s+sua\s+mem[óo]ria\b",
        r"\banot\w+\s+que\b",
    ],

    # Música / Mídia
    "media.play": [r"\bpla[yi]\s+m[úu]sica", r"\btocar?\s+m[úu]sica", r"\bcontinu\w+\s+a\s+m[úu]sica"],
    "media.pause": [r"\bpaus\w+\s+(a\s+)?m[úu]sica", r"\bpaus\w+\b"],
    "media.next": [r"\bpr[óo]xima\s+m[úu]sica", r"\bpula\s+(a\s+)?m[úu]sica"],

    # Notícias / Clima
    "news.headlines": [r"\bnot[íi]cias\b", r"\bmanchetes?\b"],
    "weather.today": [r"\bclima\b", r"\btempo\s+hoje\b", r"\btemperatura\b", r"\bvai\s+chover\b"],

    # Rotas existentes (legacy)
    "route.legacy": [r"\baprender\s+rotas\b", r"\bestudar\s+rotas\b", r"\batualizar\s+planilha\b",
                     r"\bpreencher\s+planilha\b", r"\bfazer\s+planilha\b",
                     r"\bpreencher\s+quilometragem\b", r"\bgerar?\s+relat[óo]rio\b",
                     r"\bresumo\s+da\s+semana\b", r"\brelat[óo]rio\s+(da|de|mensal|semanal)\b",
                     r"\bsincroniz\w+\s+planilha\b", r"\bsync\s+(planilha|sheets)\b",
                     r"\batualiz\w+\s+(o\s+)?analytics\b", r"\bpux\w+\s+(a\s+)?planilha\b",
                     r"\bbusc\w+\s+(da\s+|na\s+)?planilha\b"],
}


def match_intent(text: str) -> Optional[Dict[str, Any]]:
    """Retorna {intent, raw_text} se match keyword, senão None."""
    t = text.lower().strip()
    for intent, patterns in INTENTS.items():
        for p in patterns:
            if re.search(p, t):
                return {"intent": intent, "raw_text": text}
    return None
