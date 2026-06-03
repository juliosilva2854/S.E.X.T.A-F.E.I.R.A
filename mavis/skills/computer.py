"""
mavis.skills.computer — Controle do computador (mouse, teclado, apps).
Funcionalidade DESKTOP-ONLY (requer PyAutoGUI + tela física).
"""
import subprocess
import sys
import platform
import time
from typing import Optional


def _available() -> bool:
    try:
        import pyautogui  # noqa
        return True
    except Exception:
        return False


def type_text(text: str, interval: float = 0.02) -> str:
    if not _available():
        return "PyAutoGUI não disponível neste ambiente."
    import pyautogui
    pyautogui.typewrite(text, interval=interval)
    return f"Digitei: {text}"


def press_keys(*keys) -> str:
    if not _available():
        return "PyAutoGUI não disponível."
    import pyautogui
    pyautogui.hotkey(*keys)
    return f"Atalho: {'+'.join(keys)}"


def click(x: Optional[int] = None, y: Optional[int] = None, button: str = "left") -> str:
    if not _available():
        return "PyAutoGUI não disponível."
    import pyautogui
    if x is None or y is None:
        pyautogui.click(button=button)
    else:
        pyautogui.click(x=x, y=y, button=button)
    return f"Clique {button} {'em ('+str(x)+','+str(y)+')' if x else ''}"


def move(x: int, y: int, duration: float = 0.3) -> str:
    if not _available():
        return "PyAutoGUI não disponível."
    import pyautogui
    pyautogui.moveTo(x, y, duration=duration)
    return f"Mouse em ({x},{y})"


def screen_size() -> dict:
    if not _available():
        return {"error": "PyAutoGUI não disponível"}
    import pyautogui
    w, h = pyautogui.size()
    return {"width": w, "height": h}


def open_app(app_name: str) -> str:
    """Tenta abrir aplicativo pelo nome (Windows/Mac/Linux)."""
    so = platform.system()
    try:
        if so == "Windows":
            subprocess.Popen(["start", "", app_name], shell=True)
        elif so == "Darwin":
            subprocess.Popen(["open", "-a", app_name])
        else:
            subprocess.Popen([app_name])
        return f"Iniciando {app_name}"
    except Exception as e:
        return f"Não consegui abrir {app_name}: {e}"


def close_app(app_name: str) -> str:
    """Fecha aplicativo por nome de processo."""
    so = platform.system()
    try:
        if so == "Windows":
            subprocess.run(["taskkill", "/IM", f"{app_name}.exe", "/F"], capture_output=True)
        else:
            subprocess.run(["pkill", "-f", app_name], capture_output=True)
        return f"Fechei {app_name}"
    except Exception as e:
        return f"Falha ao fechar: {e}"


def lock_screen() -> str:
    so = platform.system()
    try:
        if so == "Windows":
            subprocess.run(["rundll32.exe", "user32.dll,LockWorkStation"])
        elif so == "Darwin":
            subprocess.run(["pmset", "displaysleepnow"])
        else:
            subprocess.run(["xdg-screensaver", "lock"])
        return "Tela bloqueada"
    except Exception as e:
        return f"Falha ao bloquear: {e}"


def shutdown(when_minutes: int = 1) -> str:
    so = platform.system()
    try:
        if so == "Windows":
            subprocess.run(["shutdown", "/s", "/t", str(when_minutes * 60)])
        else:
            subprocess.run(["shutdown", "-h", f"+{when_minutes}"])
        return f"Desligando em {when_minutes} minuto(s). Use 'cancelar desligamento' para abortar."
    except Exception as e:
        return f"Falha ao desligar: {e}"


def media_key(key: str) -> str:
    """key: 'play_pause' | 'next' | 'previous' | 'volume_up' | 'volume_down' | 'mute'"""
    if not _available():
        return "PyAutoGUI não disponível."
    import pyautogui
    mapping = {
        "play_pause": "playpause",
        "next": "nexttrack",
        "previous": "prevtrack",
        "volume_up": "volumeup",
        "volume_down": "volumedown",
        "mute": "volumemute",
    }
    key_name = mapping.get(key)
    if not key_name:
        return f"Tecla desconhecida: {key}"
    pyautogui.press(key_name)
    return f"Mídia: {key}"


def clipboard_get() -> str:
    try:
        import pyperclip
        return pyperclip.paste()
    except Exception as e:
        return f"clipboard indisponível: {e}"


def clipboard_set(text: str) -> str:
    try:
        import pyperclip
        pyperclip.copy(text)
        return "Copiado para a área de transferência"
    except Exception as e:
        return f"falha: {e}"
