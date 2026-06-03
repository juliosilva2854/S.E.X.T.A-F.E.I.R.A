"""
mavis.skills.system_info — Bateria, CPU, RAM, rede.
"""
from typing import Dict, Any


def battery() -> Dict[str, Any]:
    try:
        import psutil
        b = psutil.sensors_battery()
        if not b:
            return {"percent": None, "plugged": None, "msg": "Sem informação de bateria (desktop sem bateria?)"}
        secs = b.secsleft
        return {
            "percent": round(b.percent, 1),
            "plugged": b.power_plugged,
            "time_left_min": None if secs in (psutil.POWER_TIME_UNLIMITED, psutil.POWER_TIME_UNKNOWN) else secs // 60,
        }
    except Exception as e:
        return {"error": str(e)}


def cpu() -> Dict[str, Any]:
    try:
        import psutil
        return {
            "percent": psutil.cpu_percent(interval=0.4),
            "cores_logical": psutil.cpu_count(),
            "cores_physical": psutil.cpu_count(logical=False),
            "freq_mhz": round(psutil.cpu_freq().current, 0) if psutil.cpu_freq() else None,
        }
    except Exception as e:
        return {"error": str(e)}


def ram() -> Dict[str, Any]:
    try:
        import psutil
        v = psutil.virtual_memory()
        gb = 1024 ** 3
        return {
            "total_gb": round(v.total / gb, 2),
            "used_gb": round(v.used / gb, 2),
            "percent": v.percent,
        }
    except Exception as e:
        return {"error": str(e)}


def disk() -> Dict[str, Any]:
    try:
        import psutil
        d = psutil.disk_usage("/")
        gb = 1024 ** 3
        return {
            "total_gb": round(d.total / gb, 1),
            "used_gb": round(d.used / gb, 1),
            "percent": d.percent,
        }
    except Exception as e:
        return {"error": str(e)}


def summary() -> Dict[str, Any]:
    return {"battery": battery(), "cpu": cpu(), "ram": ram(), "disk": disk()}
