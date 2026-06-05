@echo off
REM ============================================================
REM  Sexta-feira (Mavis) - PREPARACAO (rode UMA vez)
REM  Cria o venv do backend, instala dependencias e gera o build do frontend.
REM  Pre-requisitos: Python 3.11+, Node.js + Yarn, MongoDB instalados.
REM ============================================================
setlocal
cd /d "%~dp0.."

echo === Verificando backend\.env ===
if not exist "backend\.env" (
  echo.
  echo *** ATENCAO: backend\.env nao existe. Crie-o antes de continuar.
  echo     Exemplo de variaveis esperadas: MONGO_URL, DB_NAME, CHAVE_GEMINI, etc.
  echo.
  pause
  exit /b 1
)

echo === Backend: venv + dependencias ===
cd backend
if not exist "venv\Scripts\python.exe" python -m venv venv
call venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
cd ..

echo.
echo === Frontend: aponta para backend LOCAL no build ===
cd frontend
if not exist ".env.production.local" (
  echo REACT_APP_BACKEND_URL=http://localhost:8001> .env.production.local
  echo Criado frontend\.env.production.local apontando para http://localhost:8001
)

echo === Frontend: dependencias + build ===
call yarn install
call yarn build
cd ..

echo.
echo Preparacao concluida.
echo Agora rode:  scripts\registrar_inicializacao.bat   (como Administrador)
echo Ou teste agora:  wscript scripts\iniciar_oculto.vbs
endlocal
pause
