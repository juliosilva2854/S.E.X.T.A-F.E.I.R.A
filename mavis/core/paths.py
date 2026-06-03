"""
mavis.core.paths — caminhos centrais (lê do .env, fallback para defaults).
"""
import os
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = APP_ROOT

ARQUIVO_MEMORIA = os.environ.get("ARQUIVO_MEMORIA", str(DATA_DIR / "memoria_mavis.json"))
ARQUIVO_DB_ROTAS = os.environ.get("ARQUIVO_DB", str(DATA_DIR / "banco_de_dados.json"))
ARQUIVO_RELATORIOS = os.environ.get("ARQUIVO_RELATORIOS", str(DATA_DIR / "banco_relatorios.json"))
ARQUIVO_LONG_MEMORY = os.environ.get("ARQUIVO_LONG_MEMORY", str(DATA_DIR / "long_memory.json"))
ARQUIVO_REMINDERS = os.environ.get("ARQUIVO_REMINDERS", str(DATA_DIR / "reminders.json"))
ARQUIVO_TOKEN_GOOGLE = os.environ.get("ARQUIVO_TOKEN_GOOGLE", str(DATA_DIR / "google_token.json"))
ARQUIVO_CREDENCIAIS_GOOGLE = os.environ.get(
    "ARQUIVO_CREDENCIAIS_GOOGLE", str(DATA_DIR / "credenciais.json")
)
