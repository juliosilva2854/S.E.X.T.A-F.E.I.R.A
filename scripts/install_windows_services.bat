@echo off
REM ============================================================
REM  Instala a Sexta-feira (Mavis) como SERVICOS do Windows (NSSM)
REM  Pre-requisitos: NSSM no PATH (https://nssm.cc), Python e Yarn instalados.
REM  Rode este .bat como ADMINISTRADOR.
REM ============================================================
setlocal
set BASE=%~dp0..
set PY=python
set NPX=npx.cmd

echo === Backend ===
nssm install SextaFeiraBackend "%PY%" "-m uvicorn server:app --host 0.0.0.0 --port 8001"
nssm set SextaFeiraBackend AppDirectory "%BASE%\backend"
nssm set SextaFeiraBackend AppEnvironmentExtra DESKTOP_MODE=1
nssm set SextaFeiraBackend Start SERVICE_AUTO_START
nssm start SextaFeiraBackend

echo === Frontend ===
nssm install SextaFeiraFrontend "%NPX%" "serve -s build -l 3000"
nssm set SextaFeiraFrontend AppDirectory "%BASE%\frontend"
nssm set SextaFeiraFrontend Start SERVICE_AUTO_START
nssm start SextaFeiraFrontend

echo.
echo Servicos instalados. Acesse http://localhost:3000
echo Para remover: nssm remove SextaFeiraBackend confirm ^&^& nssm remove SextaFeiraFrontend confirm
endlocal
pause
