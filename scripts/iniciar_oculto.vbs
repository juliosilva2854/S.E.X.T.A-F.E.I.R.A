' ============================================================
'  Sexta-feira (MAVIS) - LANCADOR OCULTO COMPLETO
'  Sobe em background, sem janela visivel:
'    - Backend FastAPI (uvicorn :8001)
'    - Frontend (serve build :3000)
'    - sexta-feira.py (loop de voz / wake-word)
'  WAHA, Docker e MongoDB sao tratados pelo iniciar_tudo.bat.
' ============================================================
Option Explicit
Dim sh, fso, base, backend, frontend, py

Set sh  = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

' base = pasta raiz do app (pai da pasta scripts)
base     = fso.GetParentFolderName(fso.GetParentFolderName(WScript.ScriptFullName))
backend  = base & "\backend"
frontend = base & "\frontend"

' Caminho do Python do venv (cai para o python global se nao existir venv)
py = backend & "\venv\Scripts\python.exe"
If Not fso.FileExists(py) Then py = "python"

' 1) Backend FastAPI (sem DESKTOP_MODE — WhatsApp agora roda 100% via WAHA)
sh.CurrentDirectory = backend
sh.Run "cmd /c """ & py & """ -m uvicorn server:app --host 0.0.0.0 --port 8001", 0, False

' 2) Frontend (build estatico)
sh.CurrentDirectory = frontend
sh.Run "cmd /c npx serve -s build -l 3000", 0, False

' 3) sexta-feira.py — loop de voz com wake-word, oculto
sh.CurrentDirectory = base
sh.Run "cmd /c """ & py & """ """ & base & "\sexta-feira.py""", 0, False

' 4) Abre o navegador apos 8s (da tempo do backend subir)
WScript.Sleep 8000
sh.Run "http://localhost:3000", 1, False
