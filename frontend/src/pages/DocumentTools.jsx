import React, { useState } from "react";
import { api } from "../api";
import { FileText, Translate, PencilSimple, ListBullets, Smiley, EnvelopeSimple } from "@phosphor-icons/react";
import { toast } from "sonner";

const TONES = ["formal", "casual", "criativo", "técnico", "persuasivo"];
const SUMMARY_MODES = [
  { id: "executivo", label: "Executivo (bullets)" },
  { id: "detalhado", label: "Detalhado (parágrafos)" },
  { id: "tldr", label: "TL;DR (1 frase)" },
];
const LANGS = ["inglês", "espanhol", "francês", "alemão", "italiano", "japonês", "chinês"];

const TABS = [
  { id: "summarize", label: "Resumir", icon: FileText, path: "/doc/summarize" },
  { id: "translate", label: "Traduzir", icon: Translate, path: "/doc/translate" },
  { id: "rewrite", label: "Reescrever", icon: PencilSimple, path: "/doc/rewrite" },
  { id: "key", label: "Pontos-chave", icon: ListBullets, path: "/doc/key-points" },
  { id: "sentiment", label: "Sentimento", icon: Smiley, path: "/doc/sentiment" },
  { id: "email", label: "Escrever email", icon: EnvelopeSimple, path: "/doc/compose-email", emailMode: true },
];

export default function DocumentTools() {
  const [tab, setTab] = useState(TABS[0]);
  const [text, setText] = useState("");
  const [mode, setMode] = useState("executivo");
  const [toLang, setToLang] = useState("inglês");
  const [tone, setTone] = useState("formal");
  const [emailIntent, setEmailIntent] = useState("");
  const [out, setOut] = useState("");
  const [loading, setLoading] = useState(false);

  const run = async () => {
    setLoading(true); setOut("");
    try {
      let payload;
      if (tab.emailMode) payload = { intent: emailIntent, tone };
      else payload = { text, mode, to_lang: toLang, tone };
      const { data } = await api.post(tab.path, payload);
      setOut(data.output || "(sem retorno)");
    } catch (e) {
      toast.error("Falha");
    } finally { setLoading(false); }
  };

  return (
    <div className="p-6 space-y-4">
      <div>
        <h1 className="font-display text-3xl">Document Tools</h1>
        <p className="text-zinc-500 text-xs tracking-widest uppercase mt-1">// RESUMIR · TRADUZIR · REESCREVER · ANALISAR · EMAIL</p>
      </div>

      <div className="flex flex-wrap gap-2">
        {TABS.map((t) => {
          const Icon = t.icon;
          const ativo = tab.id === t.id;
          return (
            <button
              key={t.id}
              data-testid={`doc-tab-${t.id}`}
              onClick={() => { setTab(t); setOut(""); }}
              className={`btn-ghost inline-flex items-center gap-2 ${ativo ? "border-amber text-amber bg-surface" : ""}`}
            >
              <Icon size={14} /> {t.label}
            </button>
          );
        })}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="panel">
          <div className="panel-header">ENTRADA</div>
          <div className="p-4 space-y-3">
            {!tab.emailMode && (
              <textarea
                data-testid="doc-text"
                value={text}
                onChange={(e) => setText(e.target.value)}
                rows={14}
                placeholder="cole o texto aqui..."
                className="w-full bg-bg border border-zinc-800 focus:border-amber px-3 py-2 outline-none font-mono text-xs resize-none"
              />
            )}
            {tab.emailMode && (
              <textarea
                data-testid="email-intent"
                value={emailIntent}
                onChange={(e) => setEmailIntent(e.target.value)}
                rows={4}
                placeholder="ex: pedir reagendamento da reunião com o gerente para próxima sexta"
                className="w-full bg-bg border border-zinc-800 focus:border-amber px-3 py-2 outline-none font-mono text-sm resize-none"
              />
            )}
            <div className="flex flex-wrap gap-2">
              {tab.id === "summarize" && (
                <select value={mode} onChange={(e) => setMode(e.target.value)}
                        className="bg-bg border border-zinc-800 focus:border-amber px-3 py-2 font-mono text-sm">
                  {SUMMARY_MODES.map((m) => <option key={m.id} value={m.id}>{m.label}</option>)}
                </select>
              )}
              {tab.id === "translate" && (
                <select value={toLang} onChange={(e) => setToLang(e.target.value)}
                        className="bg-bg border border-zinc-800 focus:border-amber px-3 py-2 font-mono text-sm">
                  {LANGS.map((l) => <option key={l} value={l}>→ {l}</option>)}
                </select>
              )}
              {(tab.id === "rewrite" || tab.emailMode) && (
                <select value={tone} onChange={(e) => setTone(e.target.value)}
                        className="bg-bg border border-zinc-800 focus:border-amber px-3 py-2 font-mono text-sm">
                  {TONES.map((t) => <option key={t} value={t}>tom: {t}</option>)}
                </select>
              )}
              <button onClick={run} disabled={loading} className="btn-amber ml-auto" data-testid="doc-run">
                {loading ? "PROCESSANDO..." : "EXECUTAR"}
              </button>
            </div>
          </div>
        </div>

        <div className="panel">
          <div className="panel-header">SAÍDA</div>
          <div className="p-4 font-mono text-sm">
            {loading && <div className="text-zinc-500 blink-caret">processando</div>}
            {out && (
              <pre data-testid="doc-output" className="whitespace-pre-wrap text-white border-l-2 border-amber pl-3">{out}</pre>
            )}
            {!loading && !out && <div className="text-zinc-600">Aguardando.</div>}
          </div>
        </div>
      </div>
    </div>
  );
}
