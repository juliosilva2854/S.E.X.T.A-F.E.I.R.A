import React, { useEffect, useState } from "react";
import { api } from "../api";
import { Plus, Trash, Play, X, Lightning, ListChecks } from "@phosphor-icons/react";
import { toast } from "sonner";

const ACTIONS = [
  { id: "chat",           label: "Chat com MAVIS",          args: [{ k: "message", placeholder: "ex: resuma o dia" }] },
  { id: "web_search",     label: "Busca web",                args: [{ k: "query", placeholder: "termo de busca" }] },
  { id: "calendar.today", label: "Agenda de hoje (Google)",  args: [] },
  { id: "gmail.unread",   label: "Emails não lidos",          args: [] },
  { id: "weather",        label: "Clima",                     args: [] },
  { id: "news",           label: "Manchetes",                 args: [{ k: "source", placeholder: "g1 | uol | tecmundo" }] },
  { id: "summarize",      label: "Resumir texto",             args: [{ k: "text", placeholder: "texto ou {{label_anterior}}" }] },
  { id: "translate",      label: "Traduzir",                  args: [{ k: "text", placeholder: "{{label}}" }, { k: "to_lang", placeholder: "inglês" }] },
  { id: "research",       label: "Dossier",                   args: [{ k: "topic", placeholder: "tópico" }] },
  { id: "generate_code",  label: "Gerar código",              args: [{ k: "prompt", placeholder: "o que codar" }, { k: "language", placeholder: "python" }] },
  { id: "compose_email",  label: "Escrever email",            args: [{ k: "intent", placeholder: "intenção do email" }, { k: "tone", placeholder: "formal" }] },
  { id: "save_note",      label: "Salvar quick note",         args: [{ k: "text", placeholder: "{{step_0}}" }, { k: "tag", placeholder: "tag" }] },
  { id: "sleep",          label: "Aguardar segundos",         args: [{ k: "seconds", placeholder: "5" }] },
];

export default function Workflows() {
  const [list, setList] = useState([]);
  const [runs, setRuns] = useState([]);
  const [editing, setEditing] = useState(null);
  const [running, setRunning] = useState(null);
  const [lastRun, setLastRun] = useState(null);

  const load = async () => {
    const [a, b] = await Promise.all([api.get("/workflows"), api.get("/workflows/runs?limit=10")]);
    setList(a.data || []); setRuns(b.data || []);
  };
  useEffect(() => { load(); }, []);

  const newWf = () => setEditing({ name: "Novo workflow", description: "", steps: [] });
  const addStep = () => setEditing({ ...editing, steps: [...editing.steps, { action: "chat", args: {}, label: `step_${editing.steps.length}` }] });
  const removeStep = (i) => setEditing({ ...editing, steps: editing.steps.filter((_, idx) => idx !== i) });
  const updateStep = (i, patch) => {
    const steps = [...editing.steps];
    steps[i] = { ...steps[i], ...patch };
    setEditing({ ...editing, steps });
  };

  const save = async () => {
    if (!editing.name?.trim()) return toast.error("nome obrigatório");
    const { data } = await api.post("/workflows", editing);
    toast.success("Salvo");
    setEditing(null);
    load();
    return data;
  };

  const remove = async (id) => {
    if (!window.confirm("Apagar workflow?")) return;
    await api.delete(`/workflows/${id}`);
    toast.success("Removido");
    load();
  };

  const run = async (wid) => {
    setRunning(wid); setLastRun(null);
    try {
      const { data } = await api.post(`/workflows/${wid}/run`);
      setLastRun(data);
      toast.success("Executado");
      load();
    } catch (e) {
      toast.error("Falha");
    } finally { setRunning(null); }
  };

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-end justify-between">
        <div>
          <h1 className="font-display text-3xl">Workflows</h1>
          <p className="text-zinc-500 text-xs tracking-widest uppercase mt-1">
            // AUTOMATIZE SEQUÊNCIAS DE SKILLS
          </p>
        </div>
        <button onClick={newWf} className="btn-amber inline-flex items-center gap-2" data-testid="wf-new">
          <Plus size={14} /> NOVO WORKFLOW
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="panel lg:col-span-2">
          <div className="panel-header"><span className="flex items-center gap-2"><Lightning size={14} /> WORKFLOWS SALVOS</span><span className="text-zinc-500">{list.length}</span></div>
          <div className="p-3 space-y-2">
            {list.length === 0 && (
              <div className="text-zinc-600 text-center py-6 text-sm">Nenhum workflow. Crie um para automatizar sequências.</div>
            )}
            {list.map((w) => (
              <div key={w.id} data-testid={`wf-${w.id}`} className="border border-zinc-800 hover:border-amber p-3 group">
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1">
                    <div className="text-amber text-[11px] tracking-widest uppercase">{w.name}</div>
                    <div className="text-zinc-500 text-xs mt-1">{w.description}</div>
                    <div className="text-[10px] text-zinc-600 mt-1 font-mono">
                      {(w.steps || []).map((s, i) => `${i + 1}. ${s.action}`).join(" → ")}
                    </div>
                  </div>
                  <div className="flex gap-1 opacity-100">
                    <button onClick={() => run(w.id)} disabled={running === w.id}
                            className="btn-ghost p-2" data-testid={`run-${w.id}`}>
                      <Play size={12} weight="fill" />
                    </button>
                    <button onClick={() => setEditing({ ...w })} className="btn-ghost p-2">EDIT</button>
                    <button onClick={() => remove(w.id)} className="text-zinc-500 hover:text-err p-2">
                      <Trash size={12} />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="panel">
          <div className="panel-header"><span className="flex items-center gap-2"><ListChecks size={14} /> ÚLTIMAS EXECUÇÕES</span></div>
          <div className="p-3 space-y-2 font-mono text-xs">
            {runs.length === 0 && <div className="text-zinc-600 text-xs">—</div>}
            {runs.map((r) => (
              <div key={r.id} className="border-l-2 border-amber pl-2">
                <div className="text-amber tracking-widest uppercase">{r.workflow_name}</div>
                <div className="text-[10px] text-zinc-500">{(r.started || "").slice(11, 19)} · {r.log?.length || 0} steps</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {lastRun && (
        <div className="panel">
          <div className="panel-header">
            <span>RESULTADO: {lastRun.workflow_name}</span>
            <button onClick={() => setLastRun(null)} className="text-zinc-500 hover:text-amber"><X size={14} /></button>
          </div>
          <div className="p-4 space-y-2 font-mono text-xs">
            {(lastRun.log || []).map((l, i) => (
              <div key={i} className={`border-l-2 pl-3 py-1 ${l.ok ? "border-ok" : "border-err"}`}>
                <div className="flex items-center gap-2">
                  <span className={l.ok ? "text-ok" : "text-err"}>[{l.ok ? "OK" : "ERR"}]</span>
                  <span className="text-amber tracking-widest uppercase">{l.action}</span>
                  <span className="text-zinc-500">@{l.label}</span>
                </div>
                {l.error && <div className="text-err mt-1">{l.error}</div>}
                {l.output_preview && <pre className="whitespace-pre-wrap text-zinc-300 text-[11px] mt-1">{l.output_preview}</pre>}
              </div>
            ))}
          </div>
        </div>
      )}

      {editing && (
        <div className="fixed inset-0 bg-black/90 z-50 flex items-center justify-center p-6">
          <div className="panel w-full max-w-3xl max-h-[90vh] overflow-auto p-6 space-y-4">
            <div className="flex justify-between">
              <h3 className="font-display text-xl">{editing.id ? "Editar" : "Novo"} workflow</h3>
              <button onClick={() => setEditing(null)} className="text-zinc-500 hover:text-amber"><X size={18} /></button>
            </div>
            <input
              data-testid="wf-name"
              value={editing.name}
              onChange={(e) => setEditing({ ...editing, name: e.target.value })}
              placeholder="nome"
              className="w-full bg-bg border border-zinc-800 focus:border-amber px-3 py-2 outline-none font-mono text-sm"
            />
            <input
              value={editing.description || ""}
              onChange={(e) => setEditing({ ...editing, description: e.target.value })}
              placeholder="descrição (opcional)"
              className="w-full bg-bg border border-zinc-800 focus:border-amber px-3 py-2 outline-none font-mono text-xs"
            />

            <div className="space-y-3">
              <div className="text-amber text-[11px] tracking-widest uppercase">STEPS</div>
              {editing.steps.map((s, i) => {
                const def = ACTIONS.find((a) => a.id === s.action) || ACTIONS[0];
                return (
                  <div key={i} className="border border-zinc-800 p-3 space-y-2">
                    <div className="flex items-center gap-2">
                      <span className="text-zinc-500 font-mono text-xs">#{i + 1}</span>
                      <select
                        value={s.action}
                        onChange={(e) => updateStep(i, { action: e.target.value, args: {} })}
                        className="bg-bg border border-zinc-800 focus:border-amber px-3 py-1.5 font-mono text-xs"
                      >
                        {ACTIONS.map((a) => <option key={a.id} value={a.id}>{a.label}</option>)}
                      </select>
                      <input
                        value={s.label || ""}
                        onChange={(e) => updateStep(i, { label: e.target.value })}
                        placeholder={`step_${i}`}
                        className="bg-bg border border-zinc-800 focus:border-amber px-3 py-1.5 font-mono text-xs flex-1"
                      />
                      <button onClick={() => removeStep(i)} className="text-zinc-500 hover:text-err"><Trash size={13} /></button>
                    </div>
                    {def.args.map((arg) => (
                      <input
                        key={arg.k}
                        value={s.args?.[arg.k] || ""}
                        onChange={(e) => updateStep(i, { args: { ...(s.args || {}), [arg.k]: e.target.value } })}
                        placeholder={arg.placeholder}
                        className="w-full bg-bg border border-zinc-800 focus:border-amber px-3 py-1.5 font-mono text-xs"
                      />
                    ))}
                  </div>
                );
              })}
              <button onClick={addStep} className="btn-ghost w-full" data-testid="wf-add-step">
                + ADICIONAR STEP
              </button>
            </div>

            <div className="flex justify-end gap-2">
              <button onClick={() => setEditing(null)} className="btn-ghost">CANCELAR</button>
              <button onClick={save} className="btn-amber" data-testid="wf-save">SALVAR</button>
            </div>

            <div className="text-[10px] text-zinc-500 leading-relaxed border-t border-zinc-800 pt-3">
              <span className="text-amber">DICA:</span> Use <span className="text-amber">{`{{label}}`}</span> nos campos para usar o output de um step anterior. Ex: step 0 com label "noticias" → step 1 "summarize" com text=<span className="text-amber">{`{{noticias}}`}</span>.
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
