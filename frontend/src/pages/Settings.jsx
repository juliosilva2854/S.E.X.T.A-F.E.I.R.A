import React, { useEffect, useState } from "react";
import { api, API } from "../api";
import { toast } from "sonner";
import { Play } from "@phosphor-icons/react";

const PERSONALITIES = [
  { id: "corporativa", title: "Corporativa", desc: "JARVIS-like. Tom sóbrio, 'senhor', eficiente." },
  { id: "casual", title: "Casual", desc: "Amigável, descontraída, sem 'senhor'." },
  { id: "sarcastica", title: "Sarcástica", desc: "Humor afiado, irônica, leal." },
];

export default function Settings() {
  const [cfg, setCfg] = useState(null);
  const [voices, setVoices] = useState([]);
  const [testing, setTesting] = useState(null);

  useEffect(() => {
    api.get("/config").then(({ data }) => setCfg(data));
    api.get("/tts/voices").then(({ data }) => setVoices(data || []));
  }, []);

  if (!cfg) return <div className="p-6 text-zinc-500 blink-caret">carregando</div>;

  const testVoice = async (voice) => {
    setTesting(voice);
    try {
      const res = await fetch(`${API}/tts`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: "Pronta para operar, senhor.", voice }),
      });
      const blob = await res.blob();
      new Audio(URL.createObjectURL(blob)).play();
    } catch (e) { toast.error("Falha"); }
    finally { setTesting(null); }
  };

  const setPersonality = async (p) => {
    await api.patch("/config", { personality: p });
    setCfg({ ...cfg, personality: p });
    toast.success(`Personalidade: ${p}`);
  };

  return (
    <div className="p-6 space-y-6 max-w-5xl">
      <div>
        <h1 className="font-display text-3xl">Configuração do Sistema</h1>
        <p className="text-zinc-500 text-xs tracking-widest uppercase mt-1">// PARÂMETROS CORE</p>
      </div>

      <div className="panel">
        <div className="panel-header">IDENTIDADE</div>
        <div className="p-5 grid grid-cols-1 md:grid-cols-2 gap-4 text-sm font-mono">
          <Row label="Nome da IA" value={cfg.nome_ia} />
          <Row label="Modelo Cognitivo" value={cfg.modelo_gemini} accent />
          <Row label="Voz Atual" value={cfg.voz} />
          <Row label="Pause Threshold" value={`${cfg.pause_threshold}s`} />
          <Row label="Chave Gemini" value={
            cfg.tem_chave_gemini ? <span className="text-ok">{cfg.chave_gemini_mask}</span>
                                  : <span className="text-err">NÃO CONFIGURADA</span>} />
          <Row label="Personalidade" value={<span className="text-amber capitalize">{cfg.personality}</span>} />
        </div>
      </div>

      <div className="panel">
        <div className="panel-header">PERSONALIDADE</div>
        <div className="p-5 grid grid-cols-1 md:grid-cols-3 gap-3">
          {PERSONALITIES.map((p) => {
            const ativa = cfg.personality === p.id;
            return (
              <button
                key={p.id}
                onClick={() => setPersonality(p.id)}
                data-testid={`persona-${p.id}`}
                className={`border p-4 text-left ${
                  ativa ? "border-amber" : "border-zinc-800 hover:border-amber/50"
                }`}
              >
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
          <span>VOZES NEURAIS PT-BR</span>
          <span className="text-zinc-500">{voices.length}</span>
        </div>
        <div className="p-5 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {voices.map((v) => {
            const ativa = v.short_name === cfg.voz;
            return (
              <div
                key={v.short_name}
                data-testid={`voice-${v.short_name}`}
                className={`border p-3 flex items-center justify-between ${
                  ativa ? "border-amber" : "border-zinc-800 hover:border-amber/50"
                }`}
              >
                <div>
                  <div className="text-amber text-xs tracking-widest uppercase">
                    {v.short_name.replace("pt-BR-", "").replace("Neural", "")}
                    {ativa && <span className="text-ok ml-2">// ATIVA</span>}
                  </div>
                  <div className="text-zinc-500 text-[10px]">{v.locale} · {v.gender}</div>
                </div>
                <button onClick={() => testVoice(v.short_name)} disabled={testing === v.short_name}
                        className="btn-ghost p-2" data-testid={`test-voice-${v.short_name}`}>
                  <Play size={14} weight="fill" />
                </button>
              </div>
            );
          })}
        </div>
      </div>

      <div className="panel p-5 text-xs text-zinc-500 leading-relaxed">
        <div className="text-amber text-[11px] tracking-widest uppercase mb-2">// ARQUITETURA HÍBRIDA</div>
        Skills pesadas (PyAutoGUI, microfone, screenshot do PC, wake word, WhatsApp, FieldControl) rodam <span className="text-white">apenas no app desktop</span> (sexta-feira.py). O painel web orquestra cérebro, Google APIs, memória de longo prazo, lembretes, visão de imagens, banco de rotas e relatórios. Ambos compartilham os mesmos arquivos JSON.
      </div>
    </div>
  );
}

function Row({ label, value, accent }) {
  return (
    <div className="flex justify-between border-b border-zinc-900 pb-2">
      <span className="text-zinc-500 text-[10px] tracking-widest uppercase">{label}</span>
      <span className={accent ? "text-amber" : "text-white"}>{value}</span>
    </div>
  );
}
