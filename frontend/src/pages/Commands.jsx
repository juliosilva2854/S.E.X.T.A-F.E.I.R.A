import React, { useEffect, useState } from "react";
import { api } from "../api";
import { Plus, Trash, Lightning, X } from "@phosphor-icons/react";
import { toast } from "sonner";

const EXEMPLOS = [
  { pattern: "bom dia", reply: "Bom dia, senhor. Espero que esteja bem disposto." },
  { pattern: "qual seu nome\\??", reply: "Sou a Sexta-feira, sua IA pessoal." },
  { pattern: "obrigad[oa]", reply: "Sempre às ordens, senhor." },
];

export default function Commands() {
  const [items, setItems] = useState([]);
  const [showAdd, setShowAdd] = useState(false);
  const [form, setForm] = useState({ pattern: "", reply: "", description: "" });

  const load = () => api.get("/custom-commands").then(({ data }) => setItems(data || []));
  useEffect(() => { load(); }, []);

  const save = async () => {
    if (!form.pattern.trim()) return toast.error("regex obrigatório");
    try {
      await api.post("/custom-commands", form);
      toast.success("Comando criado");
      setForm({ pattern: "", reply: "", description: "" });
      setShowAdd(false);
      load();
    } catch (e) { toast.error(e?.response?.data?.detail || "regex inválido"); }
  };

  const usarExemplo = (ex) => {
    setForm({ pattern: ex.pattern, reply: ex.reply, description: "" });
    setShowAdd(true);
  };

  const remove = async (id) => {
    if (!window.confirm("Apagar comando?")) return;
    await api.delete(`/custom-commands/${id}`);
    toast.success("Removido");
    load();
  };

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-end justify-between">
        <div>
          <h1 className="font-display text-3xl">Comandos Personalizados</h1>
          <p className="text-zinc-500 text-xs tracking-widest uppercase mt-1">
            // ATALHOS REGEX → RESPOSTA RÁPIDA · AVALIADOS ANTES DO CÉREBRO
          </p>
        </div>
        <button onClick={() => setShowAdd(true)} className="btn-amber inline-flex items-center gap-2"
                data-testid="cmd-new">
          <Plus size={14} /> NOVO COMANDO
        </button>
      </div>

      <div className="panel">
        <div className="panel-header"><span><Lightning size={12} className="inline mr-1" /> SEUS COMANDOS</span><span className="text-zinc-500">{items.length}</span></div>
        <div className="p-3 space-y-2">
          {items.length === 0 && (
            <div className="text-zinc-600 text-center py-6 text-sm">
              Nenhum comando customizado. Veja exemplos abaixo.
            </div>
          )}
          {items.map((c) => (
            <div key={c.id} data-testid={`cmd-${c.id}`}
                 className="border border-zinc-800 hover:border-amber p-3 flex items-start gap-3 group">
              <div className="flex-1 min-w-0 font-mono">
                <div className="text-amber text-xs tracking-widest uppercase">
                  /{c.pattern}/i
                </div>
                <div className="text-zinc-300 text-sm mt-1">↳ {c.reply}</div>
                {c.description && <div className="text-zinc-500 text-[11px] mt-1">{c.description}</div>}
              </div>
              <button onClick={() => remove(c.id)} className="text-zinc-500 hover:text-err opacity-0 group-hover:opacity-100">
                <Trash size={13} />
              </button>
            </div>
          ))}
        </div>
      </div>

      <div className="panel">
        <div className="panel-header"><span>EXEMPLOS</span></div>
        <div className="p-4 grid grid-cols-1 md:grid-cols-3 gap-3">
          {EXEMPLOS.map((e, i) => (
            <button key={i} onClick={() => usarExemplo(e)}
                    className="border border-zinc-800 hover:border-amber p-3 text-left font-mono text-xs">
              <div className="text-amber tracking-widest uppercase">/{e.pattern}/i</div>
              <div className="text-zinc-400 mt-2 text-[11px]">↳ {e.reply}</div>
            </button>
          ))}
        </div>
      </div>

      <div className="panel p-4 text-[11px] text-zinc-500 leading-relaxed">
        <span className="text-amber tracking-widest uppercase text-[10px]">// COMO FUNCIONA</span> Cada comando tem um regex (case-insensitive) que é testado contra suas mensagens. Se o regex bater, a resposta cadastrada é dita imediatamente, sem chamar o Gemini (instantâneo, sem custo). Use isso pra cumprimentos, brincadeiras internas, atalhos pessoais.
      </div>

      {showAdd && (
        <div className="fixed inset-0 bg-black/80 z-50 flex items-center justify-center p-6">
          <div className="panel w-full max-w-lg p-6 space-y-4">
            <div className="flex justify-between">
              <h3 className="font-display text-xl">Novo comando</h3>
              <button onClick={() => setShowAdd(false)} className="text-zinc-500 hover:text-amber"><X size={18} /></button>
            </div>
            <div>
              <label className="text-[10px] tracking-widest uppercase text-zinc-500">Padrão (regex)</label>
              <input data-testid="cmd-pattern" value={form.pattern}
                     onChange={(e) => setForm({ ...form, pattern: e.target.value })}
                     placeholder="ex: bom dia"
                     className="w-full bg-bg border border-zinc-800 focus:border-amber px-3 py-2 outline-none font-mono text-sm" />
            </div>
            <div>
              <label className="text-[10px] tracking-widest uppercase text-zinc-500">Resposta</label>
              <textarea data-testid="cmd-reply" value={form.reply}
                        onChange={(e) => setForm({ ...form, reply: e.target.value })} rows={3}
                        placeholder="o que a MAVIS responderá"
                        className="w-full bg-bg border border-zinc-800 focus:border-amber px-3 py-2 outline-none font-mono text-sm resize-none" />
            </div>
            <div>
              <label className="text-[10px] tracking-widest uppercase text-zinc-500">Descrição</label>
              <input value={form.description}
                     onChange={(e) => setForm({ ...form, description: e.target.value })}
                     placeholder="(opcional)"
                     className="w-full bg-bg border border-zinc-800 focus:border-amber px-3 py-2 outline-none font-mono text-xs" />
            </div>
            <div className="flex justify-end gap-2">
              <button onClick={() => setShowAdd(false)} className="btn-ghost">CANCELAR</button>
              <button onClick={save} className="btn-amber" data-testid="cmd-save">SALVAR</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
