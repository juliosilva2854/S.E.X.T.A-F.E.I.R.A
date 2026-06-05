@echo off
REM ============================================================
REM  Sexta-feira (Mavis) - PARAR TUDO
REM  - Mata o backend (uvicorn na porta 8001)
REM  - Mata o frontend (serve na porta 3000)
REM  - MongoDB NAO eh parado (pode ser usado por outros apps)
REM ============================================================
setlocal

echo === Parando Sexta-feira (Mavis) ===

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

REM Tambem mata qualquer "node serve" e python uvicorn solto que tenha ficado orfao
echo === Limpando processos orfaos (node serve / uvicorn)...
for /f "tokens=2" %%a in ('tasklist /v /fo csv ^| findstr /i "uvicorn" 2^>nul') do (
  taskkill /f /pid %%~a >nul 2>&1
)

if %ENCONTROU% equ 0 (
  echo.
  echo Nenhum processo encontrado nas portas 8001/3000. Ja estava parado.
) else (
  echo.
  echo Tudo parado, senhor.
)

echo.
echo OBS: o MongoDB continua rodando (eh um servico separado).
echo      Para parar o MongoDB tambem:  net stop MongoDB
echo.
endlocal
exit /b 0
