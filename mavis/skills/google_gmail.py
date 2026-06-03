"""mavis.skills.google_gmail — Gmail leitura/envio."""
import base64
from email.mime.text import MIMEText
from typing import List, Dict, Any, Optional
from .google_auth import service


def list_unread(max_results: int = 10) -> List[Dict[str, Any]]:
    gmail = service("gmail", "v1")
    res = gmail.users().messages().list(userId="me", q="is:unread", maxResults=max_results).execute()
    msgs = res.get("messages", [])
    out = []
    for m in msgs:
        full = gmail.users().messages().get(userId="me", id=m["id"], format="metadata",
                                            metadataHeaders=["Subject", "From", "Date"]).execute()
        headers = {h["name"]: h["value"] for h in full.get("payload", {}).get("headers", [])}
        out.append({
            "id": m["id"],
            "from": headers.get("From", ""),
            "subject": headers.get("Subject", "(sem assunto)"),
            "date": headers.get("Date", ""),
            "snippet": full.get("snippet", ""),
        })
    return out


def get_message(message_id: str) -> Dict[str, Any]:
    gmail = service("gmail", "v1")
    full = gmail.users().messages().get(userId="me", id=message_id, format="full").execute()
    headers = {h["name"]: h["value"] for h in full.get("payload", {}).get("headers", [])}
    body = _extract_body(full.get("payload", {}))
    return {
        "id": message_id,
        "from": headers.get("From", ""),
        "to": headers.get("To", ""),
        "subject": headers.get("Subject", ""),
        "date": headers.get("Date", ""),
        "body": body,
    }


def _extract_body(payload: dict) -> str:
    if not payload:
        return ""
    if payload.get("body", {}).get("data"):
        try:
            return base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", "ignore")
        except Exception:
            return ""
    for p in payload.get("parts", []):
        if p.get("mimeType") in ("text/plain", "text/html"):
            data = p.get("body", {}).get("data")
            if data:
                try:
                    return base64.urlsafe_b64decode(data).decode("utf-8", "ignore")
                except Exception:
                    continue
        inner = _extract_body(p)
        if inner:
            return inner
    return ""


def mark_as_read(message_id: str) -> bool:
    gmail = service("gmail", "v1")
    gmail.users().messages().modify(userId="me", id=message_id, body={"removeLabelIds": ["UNREAD"]}).execute()
    return True


def send(to: str, subject: str, body: str) -> Dict[str, Any]:
    gmail = service("gmail", "v1")
    mime = MIMEText(body, _charset="utf-8")
    mime["to"] = to
    mime["subject"] = subject
    raw = base64.urlsafe_b64encode(mime.as_bytes()).decode("utf-8")
    sent = gmail.users().messages().send(userId="me", body={"raw": raw}).execute()
    return {"id": sent.get("id"), "to": to}


def summarize_unread(max_results: int = 5) -> str:
    msgs = list_unread(max_results)
    if not msgs:
        return "Caixa de entrada limpa, senhor."
    out = f"Senhor, {len(msgs)} email(s) não lidos: "
    out += "; ".join(f"{m['from'].split('<')[0].strip()}: {m['subject']}" for m in msgs[:3])
    return out + "."
