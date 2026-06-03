"""
mavis.skills.scheduler — APScheduler para lembretes/proativo.
Backend roda um scheduler em background; ao disparar um lembrete,
ele anexa um evento de log que o painel mostra em tempo real.
"""
from datetime import datetime, timezone
from typing import Callable, Optional

_scheduler = None


def get_scheduler():
    global _scheduler
    if _scheduler is not None:
        return _scheduler
    from apscheduler.schedulers.background import BackgroundScheduler
    _scheduler = BackgroundScheduler(timezone="America/Sao_Paulo")
    _scheduler.start()
    return _scheduler


def schedule_one_shot(run_date_iso: str, callback: Callable, args=None, job_id: Optional[str] = None):
    sch = get_scheduler()
    when = datetime.fromisoformat(run_date_iso.replace("Z", "+00:00"))
    return sch.add_job(callback, "date", run_date=when, args=args or [], id=job_id, replace_existing=True)


def schedule_recurring(cron_expr: dict, callback: Callable, args=None, job_id: Optional[str] = None):
    """cron_expr ex: {'hour': 8, 'minute': 0}"""
    sch = get_scheduler()
    return sch.add_job(callback, "cron", args=args or [], id=job_id, replace_existing=True, **cron_expr)


def remove_job(job_id: str) -> bool:
    sch = get_scheduler()
    try:
        sch.remove_job(job_id)
        return True
    except Exception:
        return False


def list_jobs():
    sch = get_scheduler()
    out = []
    for j in sch.get_jobs():
        out.append({
            "id": j.id,
            "next_run": str(j.next_run_time) if j.next_run_time else None,
            "trigger": str(j.trigger),
        })
    return out
