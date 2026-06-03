# ==========================================
# MAVIS / S.E.X.T.A - F.E.I.R.A
# Arquivo de configuração (lê do backend/.env automaticamente)
# ==========================================
import os
from pathlib import Path

# Tenta carregar do backend/.env (fonte única de verdade)
try:
    from dotenv import load_dotenv
    raiz = Path(__file__).parent
    candidatos = [
        raiz / "backend" / ".env",
        raiz / ".env",
    ]
    for c in candidatos:
        if c.exists():
            load_dotenv(c)
            break
except ImportError:
    pass

# ---------- Credenciais (NUNCA committar valores reais) ----------
CHAVE_GEMINI = os.environ.get("CHAVE_GEMINI", "")

# ---------- Voz ----------
VOZ_SINTETIZADOR = os.environ.get("VOZ_SINTETIZADOR", "pt-BR-ThalitaNeural")

# ---------- Sistema ----------
NOME_IA = os.environ.get("NOME_IA", "Sexta-feira")
ARQUIVO_MEMORIA = os.environ.get("ARQUIVO_MEMORIA", "memoria_mavis.json")
ARQUIVO_DB = os.environ.get("ARQUIVO_DB", "banco_de_dados.json")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

# ---------- Microfone ----------
PAUSE_THRESHOLD = float(os.environ.get("PAUSE_THRESHOLD", "1.0"))

# ---------- FieldControl ----------
FIELDCONTROL_EMAIL = os.environ.get("FIELDCONTROL_EMAIL", "")
FIELDCONTROL_SENHA = os.environ.get("FIELDCONTROL_SENHA", "")

# ---------- WhatsApp ----------
WHATSAPP_NUMERO = os.environ.get("WHATSAPP_NUMERO", "")
WHATSAPP_GRUPO = os.environ.get("WHATSAPP_GRUPO", "")

# ---------- Planilha ----------
PLANILHA_NOME = os.environ.get("PLANILHA_NOME", "Planilha KM - Julio Cesar MTFL")
