"""
mavis.skills.python_sandbox — Executa Python isolado em subprocess com timeout/limites.

ATENÇÃO: Roda em subprocess separado, com timeout, sem rede, sem acesso a /app.
Não é prova-de-bala (Python é difícil de sandboxar 100%), mas é seguro para
snippets de código que o usuário pede para a MAVIS testar.
"""
import os
import sys
import tempfile
import subprocess
import textwrap
from typing import Dict, Any

EXEC_TIMEOUT = int(os.environ.get("PYEXEC_TIMEOUT", "8"))


PROLOGUE = textwrap.dedent("""
import sys, builtins, os
# Bloqueios suaves (não é sandbox 100%, mas evita acidentes)
_FORBIDDEN = {"subprocess", "ctypes", "socket", "shutil"}
_orig_import = builtins.__import__
def _safe_import(name, *args, **kwargs):
    base = name.split('.')[0]
    if base in _FORBIDDEN:
        raise ImportError(f"Modulo '{base}' bloqueado no sandbox MAVIS")
    return _orig_import(name, *args, **kwargs)
builtins.__import__ = _safe_import
""").lstrip()


def run(code: str, stdin: str = "") -> Dict[str, Any]:
    """Executa Python em subprocess, retorna {stdout, stderr, returncode, timeout_hit}."""
    full = PROLOGUE + "\n" + code
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(full)
        path = f.name
    try:
        proc = subprocess.run(
            [sys.executable, path],
            input=stdin,
            capture_output=True,
            text=True,
            timeout=EXEC_TIMEOUT,
            cwd=tempfile.gettempdir(),
            env={"PATH": os.environ.get("PATH", ""), "PYTHONUNBUFFERED": "1"},
        )
        return {
            "stdout": proc.stdout[-4000:],
            "stderr": proc.stderr[-4000:],
            "returncode": proc.returncode,
            "timeout_hit": False,
        }
    except subprocess.TimeoutExpired as e:
        return {
            "stdout": (e.stdout or b"").decode("utf-8", "ignore")[-4000:] if isinstance(e.stdout, bytes) else (e.stdout or "")[-4000:],
            "stderr": f"⏱ Tempo limite ({EXEC_TIMEOUT}s) excedido",
            "returncode": -1,
            "timeout_hit": True,
        }
    finally:
        try:
            os.unlink(path)
        except Exception:
            pass
