import React, { useState } from "react";
import { api } from "../api";
import { MagnifyingGlass, FileText, Copy } from "@phosphor-icons/react";
import { toast } from "sonner";

export default function Research() {
  const [topic, setTopic] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const run = async () => {
    if (!topic.trim()) return toast.error("Digite um tópico");
    setLoading(true); setResult(null);
    try {
      const { data } = await api.post("/research", { topic });
      setResult(data);
    } catch (e) {
      toast.error("Falha na pesquisa");
    } finally { setLoading(false); }
  };

  const copy = (txt) => { navigator.clipboard.writeText(txt); toast.success("Copiado"); };

  return (
    <div className="p-6 space-y-4">
      <div>
        <h1 className="font-display text-3xl">Research / Dossier</h1>
        <p className="text-zinc-500 text-xs tracking-widest uppercase mt-1">
          // INTELIGÊNCIA MULTI-STEP · GEMINI + WEB SEARCH
        </p>
      </div>

      <div className="panel p-4">
        <div className="flex items-center gap-2">
          <MagnifyingGlass size={16} className="text-amber" />
          <input
            data-testid="research-topic"
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && run()}
            placeholder="ex: equipamentos médicos hospitalares para pediatria — tendências 2026"
            className="flex-1 bg-transparent outline-none font-mono text-sm placeholder-zinc-600"
          />
          <button onClick={run} disabled={loading} className="btn-amber" data-testid="research-run">
            {loading ? "INVESTIGANDO..." : "INVESTIGAR"}
          </button>
        </div>
        <div className="text-[10px] text-zinc-500 mt-2 tracking-widest uppercase">
          // STEP 1: GERAR SUBQUERIES · STEP 2: BUSCAR WEB · STEP 3: SINTETIZAR DOSSIER
        </div>
      </div>

      {loading && (
        <div className="panel p-8 text-center text-zinc-500 blink-caret font-mono">
          analisando rede global · gerando dossier
        </div>
      )}

      {result && (
        <>
          <div className="panel">
            <div className="panel-header">
              <span>DOSSIER: {result.topic}</span>
              <button onClick={() => copy(result.dossier)} className="text-zinc-400 hover:text-amber">
                <Copy size={14} />
              </button>
            </div>
            <pre data-testid="dossier-output" className="p-5 whitespace-pre-wrap text-sm leading-relaxed text-white font-mono">
              {result.dossier}
            </pre>
          </div>

          <div className="panel">
            <div className="panel-header">FONTES CONSULTADAS</div>
            <div className="p-4 space-y-4">
              {(result.findings || []).map((f, i) => (
                <div key={i} className="border-l-2 border-amber pl-3">
                  <div className="text-amber text-[11px] tracking-widest uppercase mb-1">
                    ▸ {f.query}
                  </div>
                  <div className="space-y-1">
                    {(f.raw || []).map((r, j) => (
                      <a key={j} href={r.href} target="_blank" rel="noreferrer"
                         className="block text-xs text-zinc-400 hover:text-amber">
                        <span className="text-white">{r.title}</span>
                        <span className="text-zinc-600"> — {r.href}</span>
                      </a>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
