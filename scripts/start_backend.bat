@echo off
REM ============================================================
REM  Sexta-feira (Mavis) - Backend FastAPI em background
REM  Ajuste os caminhos abaixo conforme sua instalacao.
REM ============================================================
cd /d "%~dp0\..\backend"

REM Ative o venv se existir
if exist "venv\Scripts\activate.bat" call "venv\Scripts\activate.bat"

REM DESKTOP_MODE=1 habilita RPA/WhatsApp via navegador visivel
set DESKTOP_MODE=1

python -m uvicorn server:app --host 0.0.0.0 --port 8001
