@echo off
REM ============================================================
REM  Sexta-feira (MAVIS) - INICIAR TUDO (1 clique, oculto)
REM  Sobe na ordem:
REM    1) Docker Desktop (se nao estiver rodando)
REM    2) Container WAHA (devlikeapro/waha :3001)
REM    3) MongoDB (servico Windows nativo)
REM    4) Backend FastAPI (uvicorn :8001) - oculto
REM    5) Frontend (serve build :3000) - oculto
REM    6) sexta-feira.py (loop de voz / wake-word) - oculto
REM  Abre o navegador em http://localhost:3000 ao final.
REM ============================================================
setlocal EnableDelayedExpansion
cd /d "%~dp0.."
set BASE=%CD%

echo === Sexta-feira (MAVIS) === iniciando tudo ===

REM ---------- 1) Verifica preparacao ----------
if not exist "backend\venv\Scripts\python.exe" goto :preparar
if not exist "frontend\build\index.html"      goto :preparar
if not exist "model\final.mdl"                goto :preparar
goto :env_check

:preparar
echo.
echo *** Ambiente nao preparado. Rodando scripts\preparar.bat ...
call "%~dp0preparar.bat"
if not exist "backend\venv\Scripts\python.exe" (
  echo FALHA na preparacao. Verifique os logs acima.
  pause
  exit /b 1
)

:env_check
if not exist "backend\.env" (
  echo.
  echo *** ERRO: backend\.env nao existe. Crie o arquivo antes de continuar.
  pause
  exit /b 1
)

REM ---------- 2) Docker Desktop ----------
echo.
echo === Verificando Docker Desktop ===
docker info >nul 2>&1
if errorlevel 1 (
  echo Docker Desktop NAO esta rodando. Iniciando agora...
  start "" "%ProgramFiles%\Docker\Docker\Docker Desktop.exe" >nul 2>&1
  if errorlevel 1 (
    start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe" >nul 2>&1
  )
  echo Aguardando o Docker subir (pode demorar 30-60s)...
  set /a TRIES=0
  :wait_docker
  set /a TRIES+=1
  docker info >nul 2>&1
  if not errorlevel 1 goto :docker_ok
  if !TRIES! geq 60 (
    echo.
    echo AVISO: Docker nao subiu em 60s. WAHA pode nao iniciar.
    echo Abra o Docker Desktop manualmente e rode este script de novo.
    goto :mongo
  )
  timeout /t 1 /nobreak >nul
  goto :wait_docker
)
:docker_ok
echo Docker Desktop OK.

REM ---------- 3) Container WAHA ----------
echo.
echo === Subindo container WAHA ===
docker compose -f "%BASE%\docker-compose.yml" up -d waha
if errorlevel 1 (
  echo.
  echo AVISO: Falha ao subir o WAHA via docker compose.
  echo Tentando comando legado 'docker-compose'...
  docker-compose -f "%BASE%\docker-compose.yml" up -d waha
)

echo Aguardando WAHA responder em http://localhost:3001 ...
set /a TRIES=0
:wait_waha
set /a TRIES+=1
powershell -NoProfile -Command "try { $r = Invoke-WebRequest -Uri http://localhost:3001/api/sessions -Headers @{'X-Api-Key'='mavis123'} -UseBasicParsing -TimeoutSec 1; if ($r.StatusCode -lt 500) { exit 0 } } catch {}; exit 1" >nul 2>&1
if not errorlevel 1 goto :waha_ok
if %TRIES% geq 30 (
  echo AVISO: WAHA nao respondeu em 30s. Verifique 'docker logs mavis_waha'.
  goto :mongo
)
timeout /t 1 /nobreak >nul
goto :wait_waha
:waha_ok
echo WAHA OK em http://localhost:3001 (dashboard: admin / ver docker-compose.yml).

REM ---------- 4) MongoDB ----------
:mongo
echo.
echo === Iniciando MongoDB (servico Windows)...
net start MongoDB >nul 2>&1

REM ---------- 5) Mata instancias antigas do backend/frontend ----------
echo.
echo === Parando instancias antigas (porta 8001/3000)...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8001 ^| findstr LISTENING 2^>nul') do taskkill /f /pid %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :3000 ^| findstr LISTENING 2^>nul') do taskkill /f /pid %%a >nul 2>&1

REM ---------- 6) Backend + Frontend + sexta-feira.py via VBS (oculto) ----------
echo === Iniciando backend, frontend e sexta-feira.py (oculto)...
wscript "%~dp0iniciar_oculto.vbs"

REM ---------- 7) Aguarda backend pronto ----------
echo === Aguardando backend responder em http://localhost:8001 ...
set /a TRIES=0
:wait_backend
set /a TRIES+=1
powershell -NoProfile -Command "try { $r = Invoke-WebRequest -Uri http://localhost:8001/api/health -UseBasicParsing -TimeoutSec 1; if ($r.StatusCode -eq 200) { exit 0 } } catch {}; exit 1" >nul 2>&1
if not errorlevel 1 goto :ready
if %TRIES% geq 30 (
  echo AVISO: backend nao respondeu em 30s. Abrindo o navegador mesmo assim.
  goto :ready
)
timeout /t 1 /nobreak >nul
goto :wait_backend

:ready
echo.
echo === Tudo no ar. Abrindo http://localhost:3000 ===
start "" "http://localhost:3000"
echo.
echo Pronto, senhor. WAHA, backend, frontend e sexta-feira.py estao em background.
echo Para parar tudo:  scripts\parar_tudo.bat
endlocal
exit /b 0
