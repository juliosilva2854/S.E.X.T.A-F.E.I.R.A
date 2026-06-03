"""
S.E.X.T.A - F.E.I.R.A (MAVIS) v3.0 — Aplicativo Desktop
Loop principal de voz: wake word -> escuta -> roteia skills -> cérebro Gemini -> voz neural.

Rode com:
    python sexta-feira.py
"""
import os
import sys
import time
import json
import queue
import asyncio
import threading
from datetime import datetime
from pathlib import Path

# Carrega .env (do backend/.env por padrão)
from dotenv import load_dotenv
ROOT = Path(__file__).parent
for env_file in [ROOT / "backend" / ".env", ROOT / ".env"]:
    if env_file.exists():
        load_dotenv(env_file)
        break

# Garante import do pacote mavis
sys.path.insert(0, str(ROOT))

from mavis.core import brain
from mavis.core import router as router_core
from mavis.core import long_memory as lm_core
from mavis.core import reminders as rem_core
from mavis.skills import system_info, news_weather
from mavis.skills import vision as vision_skill
from mavis.skills import computer as computer_skill
from mavis.skills import scheduler as sched_skill
from mavis.skills import proactive

import pygame
import edge_tts

NOME_IA = os.environ.get("NOME_IA", "Sexta-feira")
VOZ = os.environ.get("VOZ_SINTETIZADOR", "pt-BR-ThalitaNeural")
PAUSE_THRESHOLD = float(os.environ.get("PAUSE_THRESHOLD", "1.0"))
WAKE_WORD = os.environ.get("WAKE_WORD_MODEL", "hey_jarvis_v0.1")
ATIVA_PROATIVO = os.environ.get("MAVIS_PROATIVO", "1") == "1"

pygame.mixer.init()


# ==========================================
# TTS - VOZ NEURAL
# ==========================================
async def _tts_save(texto: str, arquivo: str = "resposta.mp3"):
    communicate = edge_tts.Communicate(texto, VOZ)
    await communicate.save(arquivo)


def falar(texto: str):
    if not texto.strip():
        return
    print(f"\n[{NOME_IA}] {texto}\n")
    try:
        asyncio.run(_tts_save(texto))
        pygame.mixer.music.load("resposta.mp3")
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.05)
        pygame.mixer.music.unload()
    except Exception as e:
        print(f"[TTS falhou: {e}]")


# ==========================================
# STT - VOSK (português)
# ==========================================
class Listener:
    def __init__(self):
        import vosk
        import speech_recognition as sr
        self.recognizer = sr.Recognizer()
        self.recognizer.pause_threshold = PAUSE_THRESHOLD
        self.mic = sr.Microphone()

    def listen_once(self, timeout: float = 6.0, phrase_time_limit: float = 12.0):
        import speech_recognition as sr
        try:
            with self.mic as src:
                self.recognizer.adjust_for_ambient_noise(src, duration=0.4)
                print("(escutando...)")
                audio = self.recognizer.listen(src, timeout=timeout, phrase_time_limit=phrase_time_limit)
            try:
                txt = self.recognizer.recognize_google(audio, language="pt-BR")
                return txt
            except sr.UnknownValueError:
                return None
        except sr.WaitTimeoutError:
            return None


# ==========================================
# EXECUTOR DE SKILLS (desktop)
# ==========================================
def execute_skill_local(intent: str, raw: str) -> str:
    """Retorna string com resultado falável."""
    try:
        if intent == "vision.read_screen":
            return vision_skill.analyze_screen(raw)

        if intent == "system.battery":
            b = system_info.battery()
            if b.get("percent") is None: return "Sem bateria detectada, senhor."
            return f"Bateria em {b['percent']}%, {'ligado na tomada' if b['plugged'] else 'em modo bateria'}."
        if intent == "system.cpu":
            c = system_info.cpu()
            return f"CPU em {c['percent']}%, {c['cores_logical']} threads."
        if intent == "system.ram":
            r = system_info.ram()
            return f"RAM em {r['percent']}%, usando {r['used_gb']} de {r['total_gb']} gigas."
        if intent == "system.lock":
            return computer_skill.lock_screen()
        if intent == "system.shutdown":
            return computer_skill.shutdown(1)

        if intent == "computer.screenshot":
            img = vision_skill.capture_screen()
            if img:
                out = ROOT / "screenshots" / f"shot_{int(time.time())}.png"
                out.parent.mkdir(exist_ok=True)
                out.write_bytes(img)
                return f"Print salvo em {out.name}, senhor."
            return "Não consegui capturar a tela."
        if intent == "computer.open_app":
            # extrai nome após "abre "
            nome = raw.lower()
            for prefix in ["abre ", "ligar ", "executar ", "executa ", "abrir "]:
                if prefix in nome:
                    nome = nome.split(prefix, 1)[1].strip()
                    break
            nome = nome.replace("o ", "").replace("a ", "").strip()
            return computer_skill.open_app(nome)
        if intent == "computer.close_app":
            nome = raw.lower().replace("fecha", "").replace("encerrar", "").strip()
            return computer_skill.close_app(nome)

        if intent == "media.play":   return computer_skill.media_key("play_pause")
        if intent == "media.pause":  return computer_skill.media_key("play_pause")
        if intent == "media.next":   return computer_skill.media_key("next")

        if intent == "news.headlines":
            return news_weather.speakable_headlines("g1")
        if intent == "weather.today":
            return news_weather.speakable_weather()

        if intent == "calendar.today":
            from mavis.skills import google_calendar as gc
            return gc.speakable_today()
        if intent == "calendar.create":
            extracted = brain.smart_extract(
                raw,
                'Schema: {"summary": str, "start_iso": "YYYY-MM-DDTHH:MM:SS-03:00", '
                '"end_iso": str|null, "location": str|null, "description": str|null}.'
            )
            if not extracted.get("summary") or not extracted.get("start_iso"):
                return "Não consegui entender o título ou horário do evento."
            from mavis.skills import google_calendar as gc
            ev = gc.create_event(extracted["summary"], extracted["start_iso"],
                                 extracted.get("end_iso"),
                                 extracted.get("description") or "",
                                 extracted.get("location") or "")
            return f"Evento criado: {extracted['summary']}."

        if intent == "gmail.unread" or intent == "gmail.summary":
            from mavis.skills import google_gmail as gm
            return gm.summarize_unread(5)

        if intent == "drive.search":
            from mavis.skills import google_drive as gd
            term = raw.lower().split("drive", 1)[-1].strip().replace("?", "")
            files = gd.search(term or raw, 5)
            if not files: return "Nenhum arquivo encontrado, senhor."
            return "Encontrei: " + "; ".join(f["name"] for f in files[:5])

        if intent == "reminder.create":
            extracted = brain.smart_extract(
                raw,
                'Schema: {"text": str, "when_iso": "YYYY-MM-DDTHH:MM:SS-03:00", '
                '"recurrence": "daily"|"weekly"|"monthly"|null}.'
            )
            if not extracted.get("text") or not extracted.get("when_iso"):
                return "Não entendi o lembrete."
            r = rem_core.add_reminder(extracted["text"], extracted["when_iso"], extracted.get("recurrence"))
            try:
                sched_skill.schedule_one_shot(
                    r["when"], lambda: falar(f"Lembrete, senhor: {r['text']}"),
                    job_id=f"rem-{r['id']}"
                )
            except Exception:
                pass
            return f"Lembrete agendado para {extracted['when_iso'][:16].replace('T',' ')}."
        if intent == "reminder.list":
            items = rem_core.list_reminders(only_active=True)
            if not items: return "Sem lembretes ativos, senhor."
            return "Ativos: " + "; ".join(f"{i['text']} ({i['when'][:16].replace('T',' ')})" for i in items[:5])

        if intent == "memory.save_fact":
            extracted = brain.smart_extract(
                raw,
                'Schema: {"category":"pessoal|preferencia|trabalho|contato|lugar|agenda|outro","fact": str}.'
            )
            if not extracted.get("fact"):
                return "Não captei o que devo lembrar."
            lm_core.add_fact(extracted.get("category", "outro"), extracted["fact"])
            return "Gravado na memória de longo prazo, senhor."

        if intent == "route.legacy":
            # Mantém compatibilidade com rotinas.py existente
            try:
                import rotinas
                return rotinas.executar_rotina_local(raw, falar) or "Rotina executada."
            except Exception as e:
                return f"Falha na rotina legacy: {e}"

        if intent == "whatsapp.read_unread":
            from mavis.skills import whatsapp as wa
            res = wa.list_unread(10)
            if not res or res[0].get("error"):
                return "Não consegui ler o WhatsApp."
            return f"Você tem {len(res)} chats não lidos: " + ", ".join(r["chat"] for r in res[:3])
        if intent == "whatsapp.send":
            extracted = brain.smart_extract(
                raw, 'Schema: {"contact": str, "message": str}.'
            )
            if not extracted.get("contact") or not extracted.get("message"):
                return "Não entendi o destinatário ou mensagem."
            from mavis.skills import whatsapp as wa
            r = wa.send_message(extracted["contact"], extracted["message"])
            return "Mensagem enviada." if r.get("ok") else f"Falhou: {r.get('error')}"

    except Exception as e:
        return f"Falha na skill: {e}"

    return None  # cai pro brain


# ==========================================
# LOOP PRINCIPAL
# ==========================================
def processar_comando(texto: str, esperando_resposta: bool = False):
    print(f"[USR] {texto}")
    matched = router_core.match_intent(texto)
    if matched and not esperando_resposta:
        intent = matched["intent"]
        print(f"[INTENT] {intent}")
        result = execute_skill_local(intent, texto)
        if result is not None:
            falar(result)
            return False
    # Cai pro cérebro
    reply, espera = brain.chat_text(texto)
    falar(reply)
    return espera


def loop_principal():
    listener = Listener()
    falar(f"{NOME_IA} online, senhor. Sistemas operacionais.")

    # Modo proativo (background)
    if ATIVA_PROATIVO:
        proactive.start(lambda kind, msg: falar(msg), poll_seconds=60)
        print("[MAVIS] Modo proativo ativo.")

    # Re-agenda lembretes pendentes
    for r in rem_core.list_reminders(only_active=True):
        try:
            sched_skill.schedule_one_shot(
                r["when"], lambda txt=r["text"]: falar(f"Lembrete, senhor: {txt}"),
                job_id=f"rem-{r['id']}"
            )
        except Exception:
            pass

    esperando = False
    while True:
        try:
            txt = listener.listen_once(timeout=8 if esperando else 30)
            if not txt:
                continue
            esperando = processar_comando(txt, esperando)
        except KeyboardInterrupt:
            falar("Até logo, senhor.")
            break
        except Exception as e:
            print(f"[ERR] {e}")
            time.sleep(1)


if __name__ == "__main__":
    loop_principal()
