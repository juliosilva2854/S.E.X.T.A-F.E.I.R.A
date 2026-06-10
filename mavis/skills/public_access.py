"""
mavis.skills.public_access — Tokens de compartilhamento (somente leitura).

Gera links públicos para a página Analytics. Cada token é guardado APENAS como
hash (SHA-256) — o valor em texto puro é mostrado uma única vez na criação.
Após N tentativas inválidas o link é revogado automaticamente (brute-force).
"""
import secrets
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, List

from mavis.core import storage
from mavis.core.paths import APP_ROOT

TOKENS_FILE = str(APP_ROOT / "public_tokens.json")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _load() -> List[Dict[str, Any]]:
    return storage.read_json(TOKENS_FILE, [])


def _save(data: List[Dict[str, Any]]) -> None:
    storage.write_json(TOKENS_FILE, data)


def _public(rec: Dict[str, Any]) -> Dict[str, Any]:
    """Metadados seguros (sem o hash do token)."""
    return {
        "id": rec["id"],
        "label": rec.get("label", ""),
        "page": rec.get("page", "analytics"),
        "created_at": rec.get("created_at"),
        "revoked": rec.get("revoked", False),
        "failures": rec.get("failures", 0),
        "max_failures": rec.get("max_failures", 5),
        "views": rec.get("views", 0),
        "last_access": rec.get("last_access"),
    }


def list_tokens() -> List[Dict[str, Any]]:
    return [_public(r) for r in _load()]


def create(label: str = "", max_failures: int = 5, page: str = "analytics") -> Dict[str, Any]:
    data = _load()
    token = secrets.token_urlsafe(24)
    rec = {
        "id": secrets.token_hex(8),
        "label": (label or "").strip(),
        "page": page,
        "token_hash": _hash(token),
        "created_at": _now(),
        "revoked": False,
        "failures": 0,
        "max_failures": max(1, int(max_failures or 5)),
        "views": 0,
        "last_access": None,
    }
    data.append(rec)
    _save(data)
    out = _public(rec)
    out["token"] = token  # exibido UMA única vez
    return out


def revoke(tid: str) -> bool:
    data = _load()
    for r in data:
        if r["id"] == tid:
            r["revoked"] = True
            _save(data)
            return True
    return False


def reactivate(tid: str) -> bool:
    data = _load()
    for r in data:
        if r["id"] == tid:
            r["revoked"] = False
            r["failures"] = 0
            _save(data)
            return True
    return False


def delete(tid: str) -> bool:
    data = _load()
    novos = [r for r in data if r["id"] != tid]
    if len(novos) == len(data):
        return False
    _save(novos)
    return True


def mark_view(tid: str) -> None:
    data = _load()
    for r in data:
        if r["id"] == tid:
            r["views"] = r.get("views", 0) + 1
            r["last_access"] = _now()
            _save(data)
            return


def validate(share_id: str, token: str) -> Dict[str, Any]:
    """Valida um token contra um link (share_id). Conta falhas e auto-revoga."""
    if not share_id or not token:
        return {"ok": False, "status": 401, "error": "token ausente"}
    data = _load()
    rec = next((r for r in data if r["id"] == share_id), None)
    if not rec:
        return {"ok": False, "status": 404, "error": "link inválido"}
    if rec.get("revoked"):
        return {"ok": False, "status": 403, "error": "link expirado — gere e compartilhe um novo"}
    if _hash(token) == rec.get("token_hash"):
        if rec.get("failures", 0) > 0:
            rec["failures"] = 0
            _save(data)
        return {"ok": True, "id": rec["id"], "page": rec.get("page", "analytics"),
                "label": rec.get("label", "")}
    # token errado: conta falha e revoga ao atingir o limite
    rec["failures"] = rec.get("failures", 0) + 1
    revoked = rec["failures"] >= rec.get("max_failures", 5)
    if revoked:
        rec["revoked"] = True
    _save(data)
    if revoked:
        return {"ok": False, "status": 403,
                "error": "link expirado por excesso de tentativas — gere um novo"}
    restantes = rec.get("max_failures", 5) - rec["failures"]
    return {"ok": False, "status": 401,
            "error": f"token inválido ({restantes} tentativa(s) restante(s))"}
