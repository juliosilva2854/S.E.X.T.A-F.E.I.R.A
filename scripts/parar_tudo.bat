@echo off
REM ============================================================
REM  Sexta-feira (MAVIS) - PARAR TUDO
REM  - Mata o backend (uvicorn :8001) e o frontend (serve :3000)
REM  - Mata o sexta-feira.py (loop de voz)
REM  - Para o container WAHA (docker compose stop waha)
REM  - MongoDB NAO eh parado (pode ser usado por outros apps).
REM ============================================================
setlocal
cd /d "%~dp0.."

echo === Parando Sexta-feira (MAVIS) ===

set ENCONTROU=0

REM Backend :8001
echo === Procurando backend na porta 8001...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8001 ^| findstr LISTENING 2^>nul') do (
  echo   - matando PID %%a
  taskkill /f /pid %%a >nul 2>&1
  set ENCONTROU=1
)

REM Frontend :3000
echo === Procurando frontend na porta 3000...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :3000 ^| findstr LISTENING 2^>nul') do (
  echo   - matando PID %%a
  taskkill /f /pid %%a >nul 2>&1
  set ENCONTROU=1
)

REM sexta-feira.py (loop de voz) — procura por processo python que esteja rodando o script
echo === Procurando sexta-feira.py (loop de voz)...
for /f "tokens=2 delims=," %%a in ('wmic process where "name='python.exe' and commandline like '%%sexta-feira.py%%'" get processid /format:csv 2^>nul ^| findstr /r "[0-9]"') do (
  echo   - matando PID %%a
  taskkill /f /pid %%a >nul 2>&1
  set ENCONTROU=1
)

REM Limpa qualquer uvicorn orfao
for /f "tokens=2" %%a in ('tasklist /v /fo csv ^| findstr /i "uvicorn" 2^>nul') do (
  taskkill /f /pid %%~a >nul 2>&1
)

REM WAHA (container Docker)
echo === Parando container WAHA...
docker compose stop waha >nul 2>&1
if errorlevel 1 docker-compose stop waha >nul 2>&1

if %ENCONTROU% equ 0 (
  echo.
  echo Nenhum processo encontrado nas portas 8001/3000. Ja estava parado.
) else (
  echo.
  echo Backend, frontend, sexta-feira.py e WAHA foram parados.
)

echo.
echo OBS: MongoDB continua rodando (servico). Para parar:  net stop MongoDB
echo OBS: Docker Desktop continua rodando. Para parar:    feche pelo tray icon.
echo.
endlocal
exit /b 0
