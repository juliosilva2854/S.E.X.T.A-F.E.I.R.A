"""mavis.skills.google_calendar — Google Calendar."""
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
from .google_auth import service


def list_today() -> List[Dict[str, Any]]:
    return _list_window(0, 1)


def list_week() -> List[Dict[str, Any]]:
    return _list_window(0, 7)


def list_next(days: int = 7) -> List[Dict[str, Any]]:
    return _list_window(0, max(1, days))


def _list_window(offset_days: int, span_days: int) -> List[Dict[str, Any]]:
    cal = service("calendar", "v3")
    now = datetime.now(timezone.utc)
    start = (now + timedelta(days=offset_days)).replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=span_days)
    events = cal.events().list(
        calendarId="primary",
        timeMin=start.isoformat(),
        timeMax=end.isoformat(),
        singleEvents=True,
        orderBy="startTime",
        maxResults=50,
    ).execute().get("items", [])
    out = []
    for e in events:
        start_dt = e.get("start", {}).get("dateTime") or e.get("start", {}).get("date", "")
        end_dt = e.get("end", {}).get("dateTime") or e.get("end", {}).get("date", "")
        out.append({
            "id": e.get("id"),
            "summary": e.get("summary", "(sem título)"),
            "start": start_dt,
            "end": end_dt,
            "location": e.get("location", ""),
            "description": (e.get("description", "") or "")[:200],
            "link": e.get("htmlLink", ""),
        })
    return out


def create_event(summary: str, start_iso: str, end_iso: Optional[str] = None,
                 description: str = "", location: str = "") -> Dict[str, Any]:
    cal = service("calendar", "v3")
    start = datetime.fromisoformat(start_iso.replace("Z", "+00:00"))
    if end_iso:
        end = datetime.fromisoformat(end_iso.replace("Z", "+00:00"))
    else:
        end = start + timedelta(hours=1)
    body = {
        "summary": summary,
        "description": description,
        "location": location,
        "start": {"dateTime": start.isoformat(), "timeZone": "America/Sao_Paulo"},
        "end": {"dateTime": end.isoformat(), "timeZone": "America/Sao_Paulo"},
    }
    ev = cal.events().insert(calendarId="primary", body=body).execute()
    return {"id": ev["id"], "link": ev.get("htmlLink", "")}


def delete_event(event_id: str) -> bool:
    cal = service("calendar", "v3")
    cal.events().delete(calendarId="primary", eventId=event_id).execute()
    return True


def speakable_today() -> str:
    """Frase falável para a MAVIS narrar a agenda do dia."""
    evs = list_today()
    if not evs:
        return "Senhor, sua agenda de hoje está limpa."
    partes = []
    for e in evs[:5]:
        hora = (e["start"] or "")[11:16] if "T" in (e["start"] or "") else "dia inteiro"
        partes.append(f"{hora} — {e['summary']}")
    return "Sua agenda de hoje, senhor: " + "; ".join(partes) + "."
