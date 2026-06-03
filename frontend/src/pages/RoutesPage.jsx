import React, { useEffect, useState } from "react";
import { api } from "../api";
import { MagnifyingGlass, Plus, Trash, PencilSimple, X } from "@phosphor-icons/react";
import { toast } from "sonner";

export default function RoutesPage() {
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [q, setQ] = useState("");
  const [loading, setLoading] = useState(false);
  const [showAdd, setShowAdd] = useState(false);
  const [form, setForm] = useState({ origem: "", destino: "", km: "" });
  const [editing, setEditing] = useState(null);

  const load = async () => {
    setLoading(true);
    try {
      const { data } = await api.get("/routes", { params: q ? { q } : {} });
      setItems(data.items || []);
      setTotal(data.total || 0);
    } catch (e) {
      toast.error("Falha ao carregar rotas");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const t = setTimeout(load, 200);
    return () => clearTimeout(t);
  }, [q]);

  const save = async () => {
    const { origem, destino, km } = form;
    if (!origem.trim() || !destino.trim() || !km) {
      toast.error("Preencha origem, destino e KM");
      return;
    }
    try {
      await api.post("/routes", { origem, destino, km: parseFloat(km) });
      toast.success("Rota adicionada");
      setForm({ origem: "", destino: "", km: "" });
      setShowAdd(false);
      load();
    } catch (e) {
      toast.error("Falha ao salvar rota");
    }
  };

  const saveEdit = async () => {
    try {
      await api.put(`/routes/${encodeURIComponent(editing.key)}`, {
        km: parseFloat(editing.km),
      });
      toast.success("Rota atualizada");
      setEditing(null);
      load();
    } catch (e) {
      toast.error("Falha ao atualizar");
    }
  };

  const remove = async (key) => {
    if (!window.confirm(`Remover rota: ${key}?`)) return;
    try {
      await api.delete(`/routes/${encodeURIComponent(key)}`);
      toast.success("Rota removida");
      load();
    } catch (e) {
      toast.error("Falha ao remover");
    }
  };

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-end justify-between gap-4">
        <div>
          <h1 className="font-display text-3xl">Banco de Rotas KM</h1>
          <p className="text-zinc-500 text-xs tracking-widest uppercase mt-1">
            // {total} REGISTROS NA BASE NEURAL
          </p>
        </div>
        <button
          data-testid="add-route-btn"
          onClick={() => setShowAdd(true)}
          className="btn-amber inline-flex items-center gap-2"
        >
          <Plus size={16} weight="bold" /> NOVA ROTA
        </button>
      </div>

      <div className="panel p-3 flex items-center gap-3">
        <MagnifyingGlass size={16} className="text-zinc-500" />
        <input
          data-testid="route-search"
          placeholder="buscar origem ou destino..."
          value={q}
          onChange={(e) => setQ(e.target.value)}
          className="flex-1 bg-transparent outline-none font-mono text-sm placeholder-zinc-600"
        />
        {q && (
          <button onClick={() => setQ("")} className="text-zinc-500 hover:text-amber">
            <X size={14} />
          </button>
        )}
      </div>

      <div className="panel overflow-hidden">
        <table className="w-full text-sm font-mono">
          <thead>
            <tr className="text-[10px] tracking-widest uppercase text-zinc-500 border-b border-zinc-800">
              <th className="text-left p-3">Origem</th>
              <th className="text-left p-3">→ Destino</th>
              <th className="text-right p-3 w-32">KM</th>
              <th className="text-right p-3 w-32">Ações</th>
            </tr>
          </thead>
          <tbody data-testid="routes-table-body">
            {loading && (
              <tr>
                <td colSpan={4} className="p-6 text-center text-zinc-600 blink-caret">
                  carregando
                </td>
              </tr>
            )}
            {!loading && items.length === 0 && (
              <tr>
                <td colSpan={4} className="p-6 text-center text-zinc-600">
                  Nenhuma rota encontrada.
                </td>
              </tr>
            )}
            {items.map((r) => (
              <tr
                key={r.key}
                className="border-b border-zinc-900 hover:bg-surface2"
                data-testid={`route-row-${r.key}`}
              >
                <td className="p-3 text-zinc-300">{r.origem}</td>
                <td className="p-3 text-zinc-400">{r.destino}</td>
                <td className="p-3 text-right">
                  {editing?.key === r.key ? (
                    <input
                      autoFocus
                      type="number"
                      value={editing.km}
                      onChange={(e) =>
                        setEditing({ ...editing, km: e.target.value })
                      }
                      onKeyDown={(e) => e.key === "Enter" && saveEdit()}
                      className="w-20 bg-bg border border-amber px-2 py-1 text-right text-amber outline-none"
                    />
                  ) : (
                    <span className="text-amber font-bold">{r.km} km</span>
                  )}
                </td>
                <td className="p-3 text-right">
                  {editing?.key === r.key ? (
                    <button onClick={saveEdit} className="text-ok hover:text-amber px-2">
                      OK
                    </button>
                  ) : (
                    <button
                      onClick={() => setEditing({ key: r.key, km: r.km })}
                      className="text-zinc-500 hover:text-amber px-2"
                      data-testid={`edit-${r.key}`}
                    >
                      <PencilSimple size={14} />
                    </button>
                  )}
                  <button
                    onClick={() => remove(r.key)}
                    className="text-zinc-500 hover:text-err px-2"
                    data-testid={`delete-${r.key}`}
                  >
                    <Trash size={14} />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* MODAL ADD */}
      {showAdd && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-6">
          <div className="panel w-full max-w-md p-6 space-y-4 relative">
            <div className="flex items-start justify-between">
              <h3 className="font-display text-xl">Nova rota</h3>
              <button onClick={() => setShowAdd(false)} className="text-zinc-500 hover:text-amber">
                <X size={18} />
              </button>
            </div>
            <div className="space-y-3">
              <div>
                <label className="text-[10px] tracking-widest uppercase text-zinc-500">Origem</label>
                <input
                  data-testid="route-origem"
                  value={form.origem}
                  onChange={(e) => setForm({ ...form, origem: e.target.value })}
                  className="w-full bg-bg border border-zinc-800 focus:border-amber px-3 py-2 outline-none font-mono text-sm"
                  placeholder="ex: CASA"
                />
              </div>
              <div>
                <label className="text-[10px] tracking-widest uppercase text-zinc-500">Destino</label>
                <input
                  data-testid="route-destino"
                  value={form.destino}
                  onChange={(e) => setForm({ ...form, destino: e.target.value })}
                  className="w-full bg-bg border border-zinc-800 focus:border-amber px-3 py-2 outline-none font-mono text-sm"
                  placeholder="ex: BOX"
                />
              </div>
              <div>
                <label className="text-[10px] tracking-widest uppercase text-zinc-500">KM</label>
                <input
                  data-testid="route-km"
                  type="number"
                  step="0.1"
                  value={form.km}
                  onChange={(e) => setForm({ ...form, km: e.target.value })}
                  className="w-full bg-bg border border-zinc-800 focus:border-amber px-3 py-2 outline-none font-mono text-sm"
                  placeholder="ex: 35"
                />
              </div>
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <button onClick={() => setShowAdd(false)} className="btn-ghost">CANCELAR</button>
              <button data-testid="save-route-btn" onClick={save} className="btn-amber">SALVAR</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
