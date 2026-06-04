' ============================================================
'  Sexta-feira (Mavis) - LANCADOR OCULTO (sem janela)
'  Inicia MongoDB (se for servico), Backend (uvicorn :8001) e
'  Frontend (serve build :3000) totalmente em segundo plano.
'  Usado pelo Agendador de Tarefas (ao fazer logon) - Opcao B.
' ============================================================
Option Explicit
Dim sh, fso, base, backend, frontend, py

Set sh  = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

' base = pasta raiz do app (pai da pasta scripts)
base     = fso.GetParentFolderName(fso.GetParentFolderName(WScript.ScriptFullName))
backend  = base & "\backend"
frontend = base & "\frontend"

' Caminho do python do venv (cai para o python global se nao existir venv)
py = backend & "\venv\Scripts\python.exe"
If Not fso.FileExists(py) Then py = "python"

' 1) MongoDB como servico (ignora erro silenciosamente se nao existir)
sh.Run "cmd /c net start MongoDB", 0, False

' 2) Backend FastAPI (DESKTOP_MODE=1 habilita RPA/WhatsApp via navegador visivel)
sh.CurrentDirectory = backend
sh.Run "cmd /c set DESKTOP_MODE=1 && """ & py & """ -m uvicorn server:app --host 0.0.0.0 --port 8001", 0, False

' 3) Frontend (build estatico). Requer 'serve' (npx baixa se faltar).
sh.CurrentDirectory = frontend
sh.Run "cmd /c npx serve -s build -l 3000", 0, False

' 4) Abre o navegador apos 6s
WScript.Sleep 6000
sh.Run "http://localhost:3000", 1, False
