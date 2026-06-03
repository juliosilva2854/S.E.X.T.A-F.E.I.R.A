import React, { useEffect, useState } from "react";
import { api } from "../api";
import { Plus, Trash, X, Clock, Check, MagicWand } from "@phosphor-icons/react";
import { toast } from "sonner";

export default function Reminders() {
  const [items, setItems] = useState([]);
  const [showAdd, setShowAdd] = useState(false);
  const [showNatural, setShowNatural] = useState(false);
  const [form, setForm] = useState({ text: "", when: "", recurrence: "" });
  const [phrase, setPhrase] = useState("");
  const [loading, setLoading] = useState(false);

  const load = () => api.get("/reminders?only_active=false").then(({ data }) => setItems(data || []));
  useEffect(() => { load(); }, []);

  const save = async () => {
    if (!form.text.trim() || !form.when) return toast.error("Texto e data são obrigatórios");
    await api.post("/reminders", {
      text: form.text,
      when: form.when,
      recurrence: form.recurrence || null,
    });
    setForm({ text: "", when: "", recurrence: "" });
    setShowAdd(false);
    toast.success("Lembrete agendado");
    load();
  };

  const saveNatural = async () => {
    if (!phrase.trim()) return toast.error("Digite uma frase");
    setLoading(true);
    try {
      await api.post("/reminders/natural", { phrase });
      setPhrase("");
      setShowNatural(false);
      toast.success("MAVIS interpretou e agendou");
      load();
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Não consegui interpretar");
    } finally { setLoading(false); }
  };

  const remove = async (id) => {
    if (!window.confirm("Remover lembrete?")) return;
    await api.delete(`/reminders/${id}`);
    toast.success("Removido");
    load();
  };

  const markDone = async (id) => {
    await api.post(`/reminders/${id}/done`);
    toast.success("Marcado como feito");
    load();
  };

  const fmt = (iso) => {
    try {
      const d = new Date(iso);
      return d.toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" });
    } catch { return iso; }
  };

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-end justify-between">
        <div>
          <h1 className="font-display text-3xl">Lembretes & Alarmes</h1>
          <p className="text-zinc-500 text-xs tracking-widest uppercase mt-1">
            // SCHEDULER NEURAL ATIVO
          </p>
        </div>
        <div className="flex gap-2">
          <button
            data-testid="natural-btn"
            onClick={() => setShowNatural(true)}
            className="btn-ghost inline-flex items-center gap-2"
          >
            <MagicWand size={16} /> POR FRASE
          </button>
          <button
            data-testid="add-reminder-btn"
            onClick={() => setShowAdd(true)}
            className="btn-amber inline-flex items-center gap-2"
          >
            <Plus size={16} weight="bold" /> NOVO
          </button>
        </div>
      </div>

      <div className="panel">
        <div className="panel-header"><span>FILA</span><span className="text-zinc-500">{items.length}</span></div>
        <div className="p-3 space-y-2 font-mono text-sm">
          {items.length === 0 && (
            <div className="text-zinc-600 text-center py-6">Nada agendado.</div>
          )}
          {items.map((r) => (
            <div
              key={r.id}
              data-testid={`reminder-${r.id}`}
              className={`flex items-center justify-between border-l-2 pl-3 py-2 ${
                r.done ? "border-zinc-700 opacity-50" : "border-amber"
              }`}
            >
              <div className="flex items-center gap-3 flex-1">
                <Clock size={14} className="text-amber/60" />
                <div className="flex-1">
                  <div className={r.done ? "line-through text-zinc-500" : "text-white"}>{r.text}</div>
                  <div className="text-[10px] text-zinc-500 tracking-widest uppercase mt-0.5">
                    {fmt(r.when)} {r.recurrence ? `· ${r.recurrence}` : ""}
                  </div>
                </div>
              </div>
              <div className="flex gap-2">
                {!r.done && (
                  <button onClick={() => markDone(r.id)} className="text-zinc-500 hover:text-ok"
                          data-testid={`done-${r.id}`}>
                    <Check size={14} />
                  </button>
                )}
                <button onClick={() => remove(r.id)} className="text-zinc-500 hover:text-err"
                        data-testid={`del-rem-${r.id}`}>
                  <Trash size={14} />
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {showAdd && (
        <div className="fixed inset-0 bg-black/80 z-50 flex items-center justify-center p-6">
          <div className="panel w-full max-w-md p-6 space-y-4">
            <div className="flex justify-between">
              <h3 className="font-display text-xl">Novo lembrete</h3>
              <button onClick={() => setShowAdd(false)} className="text-zinc-500 hover:text-amber">
                <X size={18} />
              </button>
            </div>
            <input
              data-testid="reminder-text"
              value={form.text}
              onChange={(e) => setForm({ ...form, text: e.target.value })}
              placeholder="Texto do lembrete"
              className="w-full bg-bg border border-zinc-800 focus:border-amber px-3 py-2 outline-none font-mono text-sm"
            />
            <input
              data-testid="reminder-when"
              type="datetime-local"
              value={form.when}
              onChange={(e) => setForm({ ...form, when: e.target.value })}
              className="w-full bg-bg border border-zinc-800 focus:border-amber px-3 py-2 outline-none font-mono text-sm"
            />
            <select
              data-testid="reminder-recurrence"
              value={form.recurrence}
              onChange={(e) => setForm({ ...form, recurrence: e.target.value })}
              className="w-full bg-bg border border-zinc-800 focus:border-amber px-3 py-2 outline-none font-mono text-sm"
            >
              <option value="">sem recorrência</option>
              <option value="daily">diário</option>
              <option value="weekly">semanal</option>
              <option value="monthly">mensal</option>
            </select>
            <div className="flex justify-end gap-2">
              <button onClick={() => setShowAdd(false)} className="btn-ghost">CANCELAR</button>
              <button data-testid="save-reminder-btn" onClick={save} className="btn-amber">AGENDAR</button>
            </div>
          </div>
        </div>
      )}

      {showNatural && (
        <div className="fixed inset-0 bg-black/80 z-50 flex items-center justify-center p-6">
          <div className="panel w-full max-w-md p-6 space-y-4">
            <div className="flex justify-between">
              <h3 className="font-display text-xl">Lembrete por linguagem natural</h3>
              <button onClick={() => setShowNatural(false)} className="text-zinc-500 hover:text-amber">
                <X size={18} />
              </button>
            </div>
            <p className="text-xs text-zinc-500">A MAVIS vai interpretar e agendar para você.</p>
            <textarea
              data-testid="natural-phrase"
              value={phrase}
              onChange={(e) => setPhrase(e.target.value)}
              rows={3}
              placeholder="ex: me lembra de ligar pra clínica amanhã às 14h"
              className="w-full bg-bg border border-zinc-800 focus:border-amber px-3 py-2 outline-none font-mono text-sm resize-none"
            />
            <div className="flex justify-end gap-2">
              <button onClick={() => setShowNatural(false)} className="btn-ghost">CANCELAR</button>
              <button data-testid="save-natural-btn" onClick={saveNatural} disabled={loading} className="btn-amber">
                {loading ? "PROCESSANDO..." : "AGENDAR"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
