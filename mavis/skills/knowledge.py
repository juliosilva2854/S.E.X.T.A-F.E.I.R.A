"""
mavis.skills.knowledge — Knowledge Base simples com chunking + busca por keyword
e síntese via Gemini (RAG-lite, sem embeddings — funciona sem API extra).

Para PDFs: extrai texto com pypdf (instalar via requirements). Para .txt/.md: leitura direta.
"""
import os
import re
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any
from mavis.core.storage import read_json, write_json
from mavis.core.paths import DATA_DIR

KB_INDEX = str(DATA_DIR / "kb_index.json")
KB_DIR = str(DATA_DIR / "kb_docs")
os.makedirs(KB_DIR, exist_ok=True)

CHUNK_WORDS = 220
TOP_K = 6


def list_documents() -> List[Dict[str, Any]]:
    idx = read_json(KB_INDEX, [])
    return [{"id": d["id"], "name": d["name"], "added": d["added"],
             "chunks": len(d.get("chunks", []))} for d in idx]


def add_document(name: str, content_bytes: bytes) -> Dict[str, Any]:
    """Adiciona doc: extrai texto, faz chunking, salva no índice."""
    text = _extract(name, content_bytes)
    if not text.strip():
        return {"error": "Não consegui extrair texto do documento."}
    chunks = _chunk(text)
    doc_id = str(uuid.uuid4())
    raw_path = os.path.join(KB_DIR, f"{doc_id}__{_safe(name)}")
    with open(raw_path, "wb") as f:
        f.write(content_bytes)
    idx = read_json(KB_INDEX, [])
    idx.append({
        "id": doc_id,
        "name": name,
        "added": datetime.now(timezone.utc).isoformat(),
        "chunks": chunks,
        "raw_path": raw_path,
    })
    write_json(KB_INDEX, idx)
    return {"id": doc_id, "name": name, "chunks": len(chunks)}


def delete_document(doc_id: str) -> bool:
    idx = read_json(KB_INDEX, [])
    novos = []
    deleted = False
    for d in idx:
        if d["id"] == doc_id:
            deleted = True
            try:
                if d.get("raw_path") and os.path.exists(d["raw_path"]):
                    os.remove(d["raw_path"])
            except Exception:
                pass
            continue
        novos.append(d)
    if deleted:
        write_json(KB_INDEX, novos)
    return deleted


def search(query: str, top_k: int = TOP_K) -> List[Dict[str, Any]]:
    """Busca chunks por keyword (TF simples). Retorna top_k mais relevantes."""
    idx = read_json(KB_INDEX, [])
    terms = [t.lower() for t in re.findall(r"\w+", query) if len(t) > 2]
    scored = []
    for doc in idx:
        for ci, chunk in enumerate(doc.get("chunks", [])):
            text_lower = chunk.lower()
            score = sum(text_lower.count(t) for t in terms)
            if score > 0:
                scored.append({
                    "doc_id": doc["id"],
                    "doc_name": doc["name"],
                    "chunk_idx": ci,
                    "score": score,
                    "text": chunk,
                })
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:top_k]


def ask(query: str) -> Dict[str, Any]:
    """Faz busca + sintetiza resposta com Gemini citando trechos."""
    hits = search(query, TOP_K)
    if not hits:
        return {"answer": "Não encontrei nada nos documentos sobre isso, senhor.",
                "sources": [], "hits": []}
    context = "\n\n---\n\n".join(
        f"[FONTE: {h['doc_name']} #chunk{h['chunk_idx']}]\n{h['text']}" for h in hits
    )
    chave = os.environ.get("CHAVE_GEMINI", "")
    if not chave:
        return {"answer": "Sem chave Gemini.", "sources": hits, "hits": hits}
    from google import genai
    client = genai.Client(api_key=chave)
    prompt = (
        f"Responda à pergunta do usuário usando APENAS os trechos abaixo. "
        f"Se a resposta não estiver clara nos trechos, diga 'Não há informação suficiente'. "
        f"Seja objetiva e cite as fontes entre colchetes.\n\n"
        f"PERGUNTA: {query}\n\nTRECHOS:\n{context}"
    )
    resp = client.models.generate_content(
        model=os.environ.get("GEMINI_MODEL", "gemini-2.5-flash"), contents=prompt
    )
    return {
        "answer": (resp.text or "").strip(),
        "sources": [{"name": h["doc_name"], "chunk": h["chunk_idx"]} for h in hits],
        "hits": hits,
    }


def _extract(name: str, data: bytes) -> str:
    lname = name.lower()
    if lname.endswith(".pdf"):
        try:
            from pypdf import PdfReader
            import io
            r = PdfReader(io.BytesIO(data))
            out = ""
            for p in r.pages:
                out += p.extract_text() or ""
                out += "\n"
            return out
        except Exception:
            return ""
    elif lname.endswith((".txt", ".md", ".csv", ".log", ".json", ".py", ".js", ".html")):
        try:
            return data.decode("utf-8", "ignore")
        except Exception:
            return ""
    else:
        try:
            return data.decode("utf-8", "ignore")
        except Exception:
            return ""


def _chunk(text: str) -> List[str]:
    words = text.split()
    chunks = []
    for i in range(0, len(words), CHUNK_WORDS):
        chunks.append(" ".join(words[i:i + CHUNK_WORDS]))
    return [c for c in chunks if c.strip()]


def _safe(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", name)[:80]
