@echo off
REM ============================================================
REM  Sexta-feira (Mavis) - Frontend (build estatico) em background
REM ============================================================
cd /d "%~dp0\..\frontend"

REM Gera o build de producao (so precisa rodar quando o codigo muda)
if not exist "build\index.html" call yarn build

REM Serve o build na porta 3000 (precisa do pacote 'serve': npm i -g serve)
npx serve -s build -l 3000
