"""
mavis.skills.vision — Captura de tela + análise via Gemini Vision.
"""
import io
from typing import Optional


def capture_screen() -> Optional[bytes]:
    """Captura screenshot da tela primária (desktop)."""
    try:
        import mss
        from PIL import Image
        with mss.mss() as sct:
            monitor = sct.monitors[1]  # 1 = primary
            raw = sct.grab(monitor)
            img = Image.frombytes("RGB", raw.size, raw.bgra, "raw", "BGRX")
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            return buf.getvalue()
    except Exception:
        # Fallback pyautogui
        try:
            import pyautogui
            img = pyautogui.screenshot()
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            return buf.getvalue()
        except Exception:
            return None


def analyze_screen(instruction: str = "Descreva o que está na tela.") -> str:
    """Captura tela e envia para Gemini Vision."""
    img = capture_screen()
    if img is None:
        return "Não consegui capturar a tela neste ambiente."
    from mavis.core.brain import vision_describe
    return vision_describe(img, instruction)
