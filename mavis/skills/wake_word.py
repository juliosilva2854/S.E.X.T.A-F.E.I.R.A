"""
mavis.skills.wake_word — Wake word detection (DESKTOP-ONLY).
Usa openwakeword (gratuito, on-device). Aciona callback ao ouvir 'sexta-feira' ou 'mavis'.
"""
import threading
from typing import Callable


def start_listener(callback: Callable[[], None], model: str = "hey_jarvis_v0.1"):
    """
    Roda em thread background. Quando detecta a palavra, chama callback().
    Modelos default do openwakeword incluem 'hey_jarvis_v0.1', 'alexa_v0.1', etc.
    Para wake word custom 'sexta-feira', o usuário pode treinar um modelo próprio:
    https://github.com/dscripka/openWakeWord
    """
    try:
        import pyaudio
        import numpy as np
        from openwakeword.model import Model
    except Exception as e:
        return None, f"Dependências indisponíveis: {e}"

    def loop():
        wake = Model(wakeword_models=[model])
        audio = pyaudio.PyAudio()
        stream = audio.open(rate=16000, channels=1, format=pyaudio.paInt16,
                            input=True, frames_per_buffer=1280)
        try:
            while True:
                data = stream.read(1280, exception_on_overflow=False)
                samples = np.frombuffer(data, dtype=np.int16)
                preds = wake.predict(samples)
                for kw, score in preds.items():
                    if score > 0.6:
                        try:
                            callback()
                        except Exception:
                            pass
                        # Cooldown 2s
                        for _ in range(25):
                            stream.read(1280, exception_on_overflow=False)
        except Exception:
            pass
        finally:
            try:
                stream.stop_stream()
                stream.close()
                audio.terminate()
            except Exception:
                pass

    t = threading.Thread(target=loop, daemon=True)
    t.start()
    return t, "ok"
