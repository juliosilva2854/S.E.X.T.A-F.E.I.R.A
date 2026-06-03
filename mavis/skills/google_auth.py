"""
mavis.skills.google_auth — Setup OAuth2 do Google compartilhado por Calendar/Gmail/Drive.

CREDENCIAIS:
- O usuário precisa criar um projeto no Google Cloud Console e baixar
  credenciais OAuth do tipo 'Aplicativo para computador' como `credenciais.json`.
- Esses scopes cobrem Calendar (RW), Gmail (read/send), Drive (read), Sheets (RW).
- Na primeira execução, o navegador abrirá pedindo consentimento e salvará
  o token em `google_token.json`.
"""
import os
from typing import Optional

SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/spreadsheets",
]

_SERVICES = {}  # cache


def get_credentials():
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request

    from mavis.core.paths import ARQUIVO_TOKEN_GOOGLE, ARQUIVO_CREDENCIAIS_GOOGLE

    creds = None
    if os.path.exists(ARQUIVO_TOKEN_GOOGLE):
        try:
            creds = Credentials.from_authorized_user_file(ARQUIVO_TOKEN_GOOGLE, SCOPES)
        except Exception:
            creds = None

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(ARQUIVO_CREDENCIAIS_GOOGLE):
                raise FileNotFoundError(
                    f"credenciais.json não encontrado em {ARQUIVO_CREDENCIAIS_GOOGLE}. "
                    "Crie no Google Cloud Console (veja README_MAVIS.md)."
                )
            flow = InstalledAppFlow.from_client_secrets_file(ARQUIVO_CREDENCIAIS_GOOGLE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(ARQUIVO_TOKEN_GOOGLE, "w") as token:
            token.write(creds.to_json())
    return creds


def service(api: str, version: str):
    """Cache de clientes (calendar v3, gmail v1, drive v3, sheets v4)."""
    key = f"{api}:{version}"
    if key in _SERVICES:
        return _SERVICES[key]
    from googleapiclient.discovery import build
    creds = get_credentials()
    s = build(api, version, credentials=creds, cache_discovery=False)
    _SERVICES[key] = s
    return s


def status() -> dict:
    """Retorna status atual da auth: configurado/conectado/precisa-login."""
    from mavis.core.paths import ARQUIVO_TOKEN_GOOGLE, ARQUIVO_CREDENCIAIS_GOOGLE
    has_creds = os.path.exists(ARQUIVO_CREDENCIAIS_GOOGLE)
    has_token = os.path.exists(ARQUIVO_TOKEN_GOOGLE)
    return {
        "has_credenciais_json": has_creds,
        "has_token": has_token,
        "ready": has_creds and has_token,
        "credenciais_path": ARQUIVO_CREDENCIAIS_GOOGLE,
        "token_path": ARQUIVO_TOKEN_GOOGLE,
    }
