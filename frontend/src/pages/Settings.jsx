import React, { useEffect, useRef, useState } from "react";
import { api, API } from "../api";
import { toast } from "sonner";
import { Play, FloppyDisk, Upload, Eye, EyeSlash } from "@phosphor-icons/react";

const PERSONALITIES = [
  { id: "corporativa", title: "Corporativa", desc: "JARVIS-like. Sóbria, 'senhor'." },
  { id: "casual", title: "Casual", desc: "Amigável, sem 'senhor'." },
  { id: "sarcastica", title: "Sarcástica", desc: "Humor afiado, 'chefe'." },
];

export default function Settings() {
  const [cfg, setCfg] = useState(null);
  const [voices, setVoices] = useState([]);
  const [envItems, setEnvItems] = useState([]);
  const [edits, setEdits] = useState({});
  const [showSensitive, setShowSensitive] = useState({});
  const credInputRef = useRef(null);

  const reload = async () => {
    const [c, v, e] = await Promise.all([
      api.get("/config"), api.get("/tts/voices"), api.get("/env/items"),
    ]);
    setCfg(c.data); setVoices(v.data || []); setEnvItems(e.data.items || []);
  };
  useEffect(() => { reload(); }, []);

  if (!cfg) return <div className="p-6 text-zinc-500 blink-caret">carregando</div>;

  const testVoice = async (voice) => {
    try {
      const res = await fetch(`${API}/tts`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: "Pronta para operar, senhor.", voice }),
      });
      new Audio(URL.createObjectURL(await res.blob())).play();
    } catch { toast.error("Falha"); }
  };

  const setPersonality = async (p) => {
    await api.patch("/config", { personality: p });
    await api.post("/env/update", { updates: { MAVIS_PERSONALITY: p } });
    setCfg({ ...cfg, personality: p });
    toast.success(`Personalidade: ${p}`);
  };

  const saveEnv = async () => {
    if (Object.keys(edits).length === 0) return toast.error("Nada para salvar");
    try {
      await api.post("/env/update", { updates: edits });
      toast.success("Salvo no .env (backup .env.bak criado)");
      setEdits({});
      reload();
    } catch (e) { toast.error(e?.response?.data?.detail || "Falha"); }
  };

  const uploadCreds = async (e) => {
    const f = e.target.files?.[0];
    if (!f) return;
    const fd = new FormData(); fd.append("file", f);
    try {
      const res = await fetch(`${API}/google/credentials`, { method: "POST", body: fd });
      if (!res.ok) throw new Error("falhou");
      toast.success("credenciais.json salvo. Rode o app desktop para autorizar.");
      reload();
    } catch { toast.error("Falha. Verifique se é um JSON OAuth válido."); }
    e.target.value = "";
  };

  return (
    <div className="p-6 space-y-6 max-w-5xl">
      <div>
        <h1 className="font-display text-3xl">Configuração do Sistema</h1>
        <p className="text-zinc-500 text-xs tracking-widest uppercase mt-1">// .ENV · PERSONALIDADE · VOZ · GOOGLE</p>
      </div>

      <div className="panel">
        <div className="panel-header">PERSONALIDADE</div>
        <div className="p-5 grid grid-cols-1 md:grid-cols-3 gap-3">
          {PERSONALITIES.map((p) => {
            const ativa = cfg.personality === p.id;
            return (
              <button key={p.id} onClick={() => setPersonality(p.id)}
                      data-testid={`persona-${p.id}`}
                      className={`border p-4 text-left ${ativa ? "border-amber" : "border-zinc-800 hover:border-amber/50"}`}>
                <div className="text-amber text-[11px] tracking-widest uppercase">
                  {p.title} {ativa && <span className="text-ok ml-2">// ATIVA</span>}
                </div>
                <div className="text-zinc-400 text-xs mt-2">{p.desc}</div>
              </button>
            );
          })}
        </div>
      </div>

      <div className="panel">
        <div className="panel-header">
          <span>EDITOR .ENV</span>
          <button onClick={saveEnv} disabled={Object.keys(edits).length === 0}
                  className="btn-amber inline-flex items-center gap-2 disabled:opacity-40 text-xs"
                  data-testid="env-save">
            <FloppyDisk size={12} weight="fill" /> SALVAR {Object.keys(edits).length || ""}
          </button>
        </div>
        <div className="p-5 grid grid-cols-1 md:grid-cols-2 gap-3">
          {envItems.map((item) => (
            <div key={item.key} className="border border-zinc-800 p-3 space-y-1">
              <label className="text-[10px] tracking-widest uppercase text-zinc-500 flex justify-between">
                <span>{item.label} <span className="text-zinc-700">({item.key})</span></span>
                {item.sensitive && (
                  <button onClick={() => setShowSensitive({ ...showSensitive, [item.key]: !showSensitive[item.key] })}
                          className="text-zinc-500 hover:text-amber">
                    {showSensitive[item.key] ? <EyeSlash size={11} /> : <Eye size={11} />}
                  </button>
                )}
              </label>
              <input
                data-testid={`env-${item.key}`}
                type={item.sensitive && !showSensitive[item.key] ? "password" : "text"}
                value={edits[item.key] ?? (item.sensitive && !showSensitive[item.key] ? "" : item.value)}
                placeholder={item.sensitive ? item.value : ""}
                onChange={(e) => setEdits({ ...edits, [item.key]: e.target.value })}
                className="w-full bg-bg border border-zinc-800 focus:border-amber px-3 py-1.5 outline-none font-mono text-xs"
              />
            </div>
          ))}
        </div>
        <div className="border-t border-zinc-800 p-3 text-[11px] text-zinc-500">
          <span className="text-amber">DICA:</span> Após salvar, reinicie o backend (<code className="text-amber">sudo supervisorctl restart backend</code>) para o cérebro recarregar a chave Gemini. Outras chaves entram em efeito imediato.
        </div>
      </div>

      <div className="panel">
        <div className="panel-header">GOOGLE CREDENCIAIS</div>
        <div className="p-5 space-y-3">
          <div className="text-xs text-zinc-400">
            Status: <span className={cfg.google_credenciais_path ? "text-amber" : "text-zinc-500"}>{cfg.google_credenciais_path}</span>
          </div>
          <button onClick={() => credInputRef.current?.click()}
                  className="btn-amber inline-flex items-center gap-2" data-testid="upload-creds">
            <Upload size={14} /> CARREGAR credenciais.json
          </button>
          <input ref={credInputRef} type="file" accept=".json" hidden onChange={uploadCreds}
                 data-testid="creds-input" />
          <div className="text-[11px] text-zinc-500 leading-relaxed border-t border-zinc-800 pt-3">
            Baixe o JSON no <span className="text-amber">Google Cloud Console → Credenciais → OAuth Client ID (Desktop App)</span>. Após upload, rode o app desktop pela primeira vez para concluir o consentimento OAuth (token será salvo automaticamente).
          </div>
        </div>
      </div>

      <div className="panel">
        <div className="panel-header"><span>VOZES NEURAIS PT-BR</span><span className="text-zinc-500">{voices.length}</span></div>
        <div className="p-5 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {voices.map((v) => {
            const ativa = v.short_name === cfg.voz;
            return (
              <div key={v.short_name} className={`border p-3 flex items-center justify-between ${ativa ? "border-amber" : "border-zinc-800 hover:border-amber/50"}`}>
                <div>
                  <div className="text-amber text-xs tracking-widest uppercase">
                    {v.short_name.replace("pt-BR-", "").replace("Neural", "")}
                    {ativa && <span className="text-ok ml-2">// ATIVA</span>}
                  </div>
                  <div className="text-zinc-500 text-[10px]">{v.locale} · {v.gender}</div>
                </div>
                <button onClick={() => testVoice(v.short_name)} className="btn-ghost p-2">
                  <Play size={14} weight="fill" />
                </button>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
