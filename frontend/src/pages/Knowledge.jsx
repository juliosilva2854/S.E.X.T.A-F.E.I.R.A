import React, { useEffect, useState, useRef } from "react";
import { api, API } from "../api";
import { BookOpen, Plus, Trash, Question, Upload } from "@phosphor-icons/react";
import { toast } from "sonner";

export default function Knowledge() {
  const [docs, setDocs] = useState([]);
  const [query, setQuery] = useState("");
  const [answer, setAnswer] = useState(null);
  const [loading, setLoading] = useState(false);
  const inputRef = useRef(null);

  const load = () => api.get("/knowledge/documents").then(({ data }) => setDocs(data || []));
  useEffect(() => { load(); }, []);

  const onPick = async (e) => {
    const f = e.target.files?.[0];
    if (!f) return;
    const fd = new FormData();
    fd.append("file", f);
    try {
      const res = await fetch(`${API}/knowledge/documents`, { method: "POST", body: fd });
      if (!res.ok) throw new Error("falhou");
      const data = await res.json();
      toast.success(`+${data.chunks} chunks indexados`);
      load();
    } catch {
      toast.error("Falha ao indexar");
    }
    e.target.value = "";
  };

  const del = async (id) => {
    if (!window.confirm("Remover documento?")) return;
    await api.delete(`/knowledge/documents/${id}`);
    load();
  };

  const ask = async () => {
    if (!query.trim()) return;
    setLoading(true); setAnswer(null);
    try {
      const { data } = await api.post("/knowledge/ask", { query });
      setAnswer(data);
    } catch { toast.error("Falha"); }
    finally { setLoading(false); }
  };

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-end justify-between">
        <div>
          <h1 className="font-display text-3xl">Knowledge Base</h1>
          <p className="text-zinc-500 text-xs tracking-widest uppercase mt-1">
            // INDEXE PDF · TXT · MD E PERGUNTE
          </p>
        </div>
        <button onClick={() => inputRef.current?.click()} className="btn-amber inline-flex items-center gap-2"
                data-testid="kb-upload">
          <Upload size={14} /> CARREGAR DOC
        </button>
        <input ref={inputRef} type="file" hidden onChange={onPick}
               accept=".pdf,.txt,.md,.csv,.log,.json,.py,.js,.html"
               data-testid="kb-file-input" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="panel lg:col-span-1">
          <div className="panel-header">
            <span className="flex items-center gap-2"><BookOpen size={14} /> DOCUMENTOS</span>
            <span className="text-zinc-500">{docs.length}</span>
          </div>
          <div className="p-3 space-y-2">
            {docs.length === 0 && <div className="text-zinc-600 text-xs text-center py-4">Nenhum documento.</div>}
            {docs.map((d) => (
              <div key={d.id} data-testid={`kb-doc-${d.id}`}
                   className="border border-zinc-800 p-3 flex items-start justify-between gap-2 group">
                <div className="flex-1 min-w-0">
                  <div className="text-amber text-xs tracking-widest uppercase truncate">{d.name}</div>
                  <div className="text-[10px] text-zinc-500 mt-1">{d.chunks} chunks · {(d.added || "").slice(0, 10)}</div>
                </div>
                <button onClick={() => del(d.id)} className="text-zinc-600 hover:text-err opacity-0 group-hover:opacity-100">
                  <Trash size={13} />
                </button>
              </div>
            ))}
          </div>
        </div>

        <div className="panel lg:col-span-2">
          <div className="panel-header"><span className="flex items-center gap-2"><Question size={14} /> PERGUNTAR</span></div>
          <div className="p-4 space-y-3">
            <div className="flex gap-2">
              <input
                data-testid="kb-query"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && ask()}
                placeholder="pergunte algo sobre os documentos..."
                className="flex-1 bg-bg border border-zinc-800 focus:border-amber px-3 py-2 outline-none font-mono text-sm"
              />
              <button onClick={ask} disabled={loading || !docs.length} className="btn-amber" data-testid="kb-ask">
                {loading ? "BUSCANDO..." : "PERGUNTAR"}
              </button>
            </div>

            {loading && <div className="text-zinc-500 blink-caret font-mono text-sm">analisando documentos</div>}

            {answer && (
              <div className="space-y-3 mt-2">
                <div className="border-l-2 border-amber pl-3">
                  <div className="text-amber text-[11px] tracking-widest uppercase mb-1">RESPOSTA</div>
                  <pre data-testid="kb-answer" className="whitespace-pre-wrap text-white text-sm font-mono">
                    {answer.answer}
                  </pre>
                </div>
                {answer.sources?.length > 0 && (
                  <div>
                    <div className="text-zinc-500 text-[10px] tracking-widest uppercase mb-1">FONTES</div>
                    <div className="flex flex-wrap gap-2">
                      {answer.sources.map((s, i) => (
                        <span key={i} className="border border-zinc-800 px-2 py-1 text-[10px] font-mono">
                          {s.name} #chunk{s.chunk}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="panel p-3 text-xs text-zinc-500">
        <span className="text-amber tracking-widest uppercase text-[10px]">// COMO FUNCIONA</span> Texto extraído (pypdf para PDF), chunkado em ~220 palavras, indexado por keyword. Pergunta → busca top-6 chunks → Gemini sintetiza com citação de fonte. Sem embeddings (= sem API extra), funciona com seu Gemini.
      </div>
    </div>
  );
}
