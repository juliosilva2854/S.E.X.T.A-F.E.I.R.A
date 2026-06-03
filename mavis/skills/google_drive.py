"""mavis.skills.google_drive — Drive search."""
from typing import List, Dict, Any
from .google_auth import service


def search(query: str, max_results: int = 10) -> List[Dict[str, Any]]:
    drive = service("drive", "v3")
    q = f"name contains '{query}' and trashed=false"
    res = drive.files().list(
        q=q,
        pageSize=max_results,
        fields="files(id,name,mimeType,modifiedTime,webViewLink,size)"
    ).execute()
    return res.get("files", [])


def recent(max_results: int = 10) -> List[Dict[str, Any]]:
    drive = service("drive", "v3")
    res = drive.files().list(
        orderBy="modifiedTime desc",
        pageSize=max_results,
        fields="files(id,name,mimeType,modifiedTime,webViewLink,size)"
    ).execute()
    return res.get("files", [])
