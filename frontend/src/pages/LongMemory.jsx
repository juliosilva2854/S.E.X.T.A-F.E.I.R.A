import React, { useEffect, useState } from "react";
import { api } from "../api";
import { Plus, Trash, X, PencilSimple, Lightbulb } from "@phosphor-icons/react";
import { toast } from "sonner";

const CATEGORIES = ["pessoal", "preferencia", "trabalho", "contato", "lugar", "agenda", "outro"];

export default function LongMemory() {
  const [items, setItems] = useState([]);
  const [showAdd, setShowAdd] = useState(false);
  const [form, setForm] = useState({ category: "pessoal", fact: "" });
  const [editing, setEditing] = useState(null);

  const load = () => api.get("/long-memory").then(({ data }) => setItems(data || []));
  useEffect(() => { load(); }, []);

  const save = async () => {
    if (!form.fact.trim()) return toast.error("Fato vazio");
    await api.post("/long-memory", form);
    toast.success("Fato gravado na memória neural");
    setForm({ category: "pessoal", fact: "" });
    setShowAdd(false);
    load();
  };

  const remove = async (id) => {
    if (!window.confirm("Esquecer este fato?")) return;
    await api.delete(`/long-memory/${id}`);
    toast.success("Esquecido");
    load();
  };

  const saveEdit = async () => {
    await api.put(`/long-memory/${editing.id}`, {
      category: editing.category, fact: editing.fact,
    });
    setEditing(null);
    toast.success("Atualizado");
    load();
  };

  const grupos = CATEGORIES.map((c) => ({
    cat: c, items: items.filter((i) => i.category === c),
  })).filter((g) => g.items.length > 0);

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-end justify-between">
        <div>
          <h1 className="font-display text-3xl">Memória de Longo Prazo</h1>
          <p className="text-zinc-500 text-xs tracking-widest uppercase mt-1">
            // {items.length} FATOS PERSISTENTES SOBRE O OPERADOR
          </p>
        </div>
        <button
          data-testid="add-fact-btn"
          onClick={() => setShowAdd(true)}
          className="btn-amber inline-flex items-center gap-2"
        >
          <Plus size={16} weight="bold" /> GRAVAR FATO
        </button>
      </div>

      {items.length === 0 && (
        <div className="panel p-8 text-center text-zinc-500">
          <Lightbulb size={32} className="mx-auto text-amber/40 mb-3" />
          Nenhum fato persistente ainda. Diga "lembre disso: ..." no chat ou clique acima.
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {grupos.map(({ cat, items }) => (
          <div key={cat} className="panel">
            <div className="panel-header">
              <span>{cat}</span>
              <span className="text-zinc-500">{items.length}</span>
            </div>
            <div className="p-3 space-y-2">
              {items.map((it) => (
                <div
                  key={it.id}
                  data-testid={`fact-${it.id}`}
                  className="border-l-2 border-amber/40 pl-3 py-1 flex items-start justify-between gap-3 group"
                >
                  {editing?.id === it.id ? (
                    <input
                      autoFocus
                      value={editing.fact}
                      onChange={(e) => setEditing({ ...editing, fact: e.target.value })}
                      onKeyDown={(e) => e.key === "Enter" && saveEdit()}
                      className="flex-1 bg-bg border border-amber px-2 py-1 text-sm outline-none"
                    />
                  ) : (
                    <div className="text-sm text-zinc-200 flex-1">{it.fact}</div>
                  )}
                  <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-none">
                    <button
                      onClick={() =>
                        editing?.id === it.id
                          ? saveEdit()
                          : setEditing({ id: it.id, category: it.category, fact: it.fact })
                      }
                      className="text-zinc-500 hover:text-amber"
                    >
                      <PencilSimple size={13} />
                    </button>
                    <button
                      onClick={() => remove(it.id)}
                      className="text-zinc-500 hover:text-err"
                      data-testid={`del-fact-${it.id}`}
                    >
                      <Trash size={13} />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      {showAdd && (
        <div className="fixed inset-0 bg-black/80 z-50 flex items-center justify-center p-6">
          <div className="panel w-full max-w-lg p-6 space-y-4">
            <div className="flex justify-between">
              <h3 className="font-display text-xl">Gravar fato</h3>
              <button onClick={() => setShowAdd(false)} className="text-zinc-500 hover:text-amber">
                <X size={18} />
              </button>
            </div>
            <div>
              <label className="text-[10px] tracking-widest uppercase text-zinc-500">Categoria</label>
              <select
                data-testid="fact-category"
                value={form.category}
                onChange={(e) => setForm({ ...form, category: e.target.value })}
                className="w-full bg-bg border border-zinc-800 focus:border-amber px-3 py-2 outline-none font-mono text-sm"
              >
                {CATEGORIES.map((c) => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
            <div>
              <label className="text-[10px] tracking-widest uppercase text-zinc-500">Fato</label>
              <textarea
                data-testid="fact-text"
                value={form.fact}
                onChange={(e) => setForm({ ...form, fact: e.target.value })}
                rows={4}
                placeholder="ex: Minha esposa se chama Maria, casamento em 12/abril"
                className="w-full bg-bg border border-zinc-800 focus:border-amber px-3 py-2 outline-none font-mono text-sm resize-none"
              />
            </div>
            <div className="flex justify-end gap-2">
              <button onClick={() => setShowAdd(false)} className="btn-ghost">CANCELAR</button>
              <button data-testid="save-fact-btn" onClick={save} className="btn-amber">GRAVAR</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
