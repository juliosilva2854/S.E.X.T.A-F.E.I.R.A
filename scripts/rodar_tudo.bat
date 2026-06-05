@echo off
REM ============================================================
REM  Sexta-feira (Mavis) - RODAR TUDO (1 clique)
REM  - Detecta se ja preparou o ambiente (se nao, roda preparar.bat)
REM  - Sobe MongoDB (se for servico)
REM  - Lanca backend (uvicorn :8001) e frontend (serve :3000) ocultos
REM  - Abre o navegador em http://localhost:3000
REM ============================================================
setlocal
cd /d "%~dp0.."
set BASE=%CD%

echo === Sexta-feira (Mavis) === iniciando ===

REM 1) Verifica preparacao previa
if not exist "backend\venv\Scripts\python.exe" goto :preparar
if not exist "frontend\build\index.html" goto :preparar
goto :iniciar

:preparar
echo.
echo *** Primeira execucao detectada. Preparando ambiente (venv + deps + build)...
echo *** Isso pode demorar alguns minutos.
echo.
call "%~dp0preparar.bat"
if not exist "backend\venv\Scripts\python.exe" (
  echo FALHA na preparacao. Verifique os logs acima.
  pause
  exit /b 1
)

:iniciar
REM 2) Verifica backend\.env
if not exist "backend\.env" (
  echo.
  echo *** ERRO: backend\.env nao existe. Crie o arquivo antes de continuar.
  pause
  exit /b 1
)

REM 3) Para qualquer instancia anterior (evita "porta ocupada")
echo.
echo === Parando instancias anteriores (se houver)...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8001 ^| findstr LISTENING 2^>nul') do taskkill /f /pid %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :3000 ^| findstr LISTENING 2^>nul') do taskkill /f /pid %%a >nul 2>&1

REM 4) Sobe MongoDB (silencia erro se ja estiver rodando)
echo === Iniciando MongoDB...
net start MongoDB >nul 2>&1

REM 5) Lanca backend + frontend ocultos via o VBS
echo === Iniciando backend (porta 8001) e frontend (porta 3000)...
wscript "%~dp0iniciar_oculto.vbs"

REM 6) Aguarda e abre o navegador
echo === Aguardando backend responder...
set /a TRIES=0
:wait_backend
set /a TRIES+=1
powershell -NoProfile -Command "try { $r = Invoke-WebRequest -Uri http://localhost:8001/api/health -UseBasicParsing -TimeoutSec 1; if ($r.StatusCode -eq 200) { exit 0 } } catch {}; exit 1" >nul 2>&1
if %errorlevel% equ 0 goto :ready
if %TRIES% geq 30 goto :timeout
timeout /t 1 /nobreak >nul
goto :wait_backend

:timeout
echo.
echo AVISO: backend nao respondeu em 30s. Pode ser que esteja iniciando lento.
echo Vou abrir o navegador mesmo assim — se nao carregar, espere mais alguns segundos e atualize a pagina.

:ready
echo === Tudo no ar. Abrindo http://localhost:3000 ...
start "" "http://localhost:3000"
echo.
echo Pronto, senhor. Para parar tudo, rode:  scripts\parar_tudo.bat
endlocal
exit /b 0
