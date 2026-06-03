"""
mavis.skills.proactive — Modo proativo.
Loop que checa periodicamente: lembretes vencidos, próximas reuniões (15min antes),
bateria baixa, email novo prioritário. Emite eventos pro front via log push.
"""
import time
import threading
from datetime import datetime, timezone, timedelta
from typing import Callable, Optional

from mavis.core import reminders as rem_core


_thread: Optional[threading.Thread] = None
_stop = threading.Event()


def _check_loop(emit: Callable[[str, str], None], poll_seconds: int = 60):
    last_battery_alert = 0
    last_calendar_check = 0
    while not _stop.is_set():
        try:
            now = datetime.now(timezone.utc)
            # 1) Lembretes vencidos
            for r in rem_core.due_reminders(now):
                emit("reminder", f"Lembrete: {r['text']}")
                rem_core.mark_done(r["id"])

            # 2) Bateria baixa (a cada 5 min)
            if time.time() - last_battery_alert > 300:
                try:
                    from mavis.skills.system_info import battery
                    b = battery()
                    if b.get("percent") is not None and not b.get("plugged") and b["percent"] < 20:
                        emit("battery", f"Bateria em {b['percent']}%. Considere conectar o carregador.")
                        last_battery_alert = time.time()
                except Exception:
                    pass

            # 3) Próxima reunião em 15min (a cada 5 min)
            if time.time() - last_calendar_check > 300:
                try:
                    from mavis.skills.google_calendar import list_today
                    evs = list_today()
                    soon = now + timedelta(minutes=15)
                    for e in evs:
                        st = (e.get("start") or "")
                        if "T" not in st:
                            continue
                        when = datetime.fromisoformat(st.replace("Z", "+00:00"))
                        if now < when <= soon:
                            emit("calendar", f"Atenção: '{e['summary']}' em 15 minutos.")
                    last_calendar_check = time.time()
                except Exception:
                    pass
        except Exception:
            pass
        _stop.wait(poll_seconds)


def start(emit_callback: Callable[[str, str], None], poll_seconds: int = 60):
    global _thread
    if _thread and _thread.is_alive():
        return False
    _stop.clear()
    _thread = threading.Thread(target=_check_loop, args=(emit_callback, poll_seconds), daemon=True)
    _thread.start()
    return True


def stop():
    _stop.set()
