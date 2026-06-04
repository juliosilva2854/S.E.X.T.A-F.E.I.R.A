@echo off
REM ============================================================
REM  Sexta-feira (Mavis) - PREPARACAO (rode UMA vez)
REM  Cria o venv do backend, instala dependencias e gera o build do frontend.
REM  Pre-requisitos: Python 3.11+, Node.js + Yarn, MongoDB instalados.
REM ============================================================
setlocal
cd /d "%~dp0.."

echo === Backend: venv + dependencias ===
cd backend
if not exist "venv\Scripts\python.exe" python -m venv venv
call venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
cd ..

echo.
echo === Frontend: dependencias + build ===
cd frontend
call yarn install
call yarn build
cd ..

echo.
echo Preparacao concluida.
echo Agora rode:  scripts\registrar_inicializacao.bat   (como Administrador)
echo Ou teste agora:  wscript scripts\iniciar_oculto.vbs
endlocal
pause
