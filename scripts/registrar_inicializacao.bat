@echo off
REM ============================================================
REM  Sexta-feira (Mavis) - REGISTRA inicializacao automatica (Opcao B)
REM  Cria uma tarefa que roda o lancador OCULTO ao fazer logon.
REM  >>> Execute este arquivo como ADMINISTRADOR <<<
REM ============================================================
setlocal
set TAREFA=SextaFeira
set VBS=%~dp0iniciar_oculto.vbs

echo Registrando a tarefa "%TAREFA%" para iniciar ao fazer logon...
schtasks /create /tn "%TAREFA%" /tr "wscript.exe \"%VBS%\"" /sc onlogon /rl highest /f
if %errorlevel% neq 0 (
  echo.
  echo FALHA ao registrar. Rode este .bat como Administrador.
  pause
  exit /b 1
)

echo.
echo Pronto! A Sexta-feira vai iniciar sozinha (oculta) toda vez que voce logar.
echo - Iniciar agora sem reiniciar:   schtasks /run /tn "%TAREFA%"
echo - Ver status:                    schtasks /query /tn "%TAREFA%"
echo - Remover a inicializacao:       schtasks /delete /tn "%TAREFA%" /f
echo.
echo Acesse o painel em: http://localhost:3000
endlocal
pause
