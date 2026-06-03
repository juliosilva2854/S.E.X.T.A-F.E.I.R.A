import React, { useEffect, useState } from "react";
import { api } from "../api";
import { Copy, Trash, FileText, X, Plus, Lightning } from "@phosphor-icons/react";
import { toast } from "sonner";

export default function Reports() {
  const [list, setList] = useState([]);
  const [selected, setSelected] = useState(null);
  const [showAdd, setShowAdd] = useState(false);
  const [form, setForm] = useState({ periodo: "", conteudo_relatorio: "" });

  const load = () =>
    api
      .get("/reports")
      .then(({ data }) => setList(data || []))
      .catch(() => toast.error("Falha ao carregar relatórios"));

  useEffect(() => { load(); }, []);

  const open = async (id) => {
    const { data } = await api.get(`/reports/${id}`);
    setSelected(data);
  };

  const remove = async (id) => {
    if (!window.confirm("Apagar este relatório?")) return;
    await api.delete(`/reports/${id}`);
    setSelected(null);
    toast.success("Removido");
    load();
  };

  const copy = (txt) => {
    navigator.clipboard.writeText(txt);
    toast.success("Copiado");
  };

  const save = async () => {
    if (!form.periodo.trim() || !form.conteudo_relatorio.trim()) {
      toast.error("Preencha período e conteúdo");
      return;
    }
    await api.post("/reports", form);
    setForm({ periodo: "", conteudo_relatorio: "" });
    setShowAdd(false);
    toast.success("Relatório criado");
    load();
  };

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-end justify-between">
        <div>
          <h1 className="font-display text-3xl">Relatórios Armazenados</h1>
          <p className="text-zinc-500 text-xs tracking-widest uppercase mt-1">
            // {list.length} REGISTROS NO BANCO
          </p>
        </div>
        <button
          data-testid="add-report-btn"
          onClick={() => setShowAdd(true)}
          className="btn-amber inline-flex items-center gap-2"
        >
          <Plus size={16} weight="bold" /> ADICIONAR
        </button>
        <button
          data-testid="auto-weekly-btn"
          onClick={async () => {
            try {
              const { data } = await api.post("/reports/auto-weekly");
              if (data.created) { toast.success("Resumo semanal gerado"); load(); }
              else toast.info(data.reason || "Sem dados");
            } catch { toast.error("Falha"); }
          }}
          className="btn-ghost inline-flex items-center gap-2"
        >
          <Lightning size={14} weight="fill" /> RESUMO SEMANAL AGORA
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {list.length === 0 && (
          <div className="panel p-6 text-zinc-600 text-sm col-span-3">
            Nenhum relatório arquivado.
          </div>
        )}
        {list.map((r) => (
          <button
            data-testid={`report-card-${r.id}`}
            key={r.id}
            onClick={() => open(r.id)}
            className="panel p-4 text-left hover:border-amber transition-none"
          >
            <div className="flex items-center gap-2 text-amber text-[11px] tracking-widest uppercase">
              <FileText size={14} weight="fill" /> {r.periodo}
            </div>
            <div className="text-zinc-500 text-[10px] mt-1">{r.gerado_em}</div>
            <div className="text-zinc-300 text-xs mt-3 line-clamp-5 whitespace-pre-wrap">
              {r.preview}
            </div>
          </button>
        ))}
      </div>

      {/* VIEWER */}
      {selected && (
        <div className="fixed inset-0 bg-black/80 z-50 flex items-center justify-center p-6">
          <div className="panel w-full max-w-3xl max-h-[90vh] flex flex-col">
            <div className="panel-header">
              <span className="text-amber">{selected.periodo}</span>
              <div className="flex items-center gap-2">
                <button
                  data-testid="copy-report-btn"
                  onClick={() => copy(selected.conteudo_relatorio)}
                  className="text-zinc-400 hover:text-amber"
                >
                  <Copy size={14} />
                </button>
                <button
                  data-testid="delete-report-btn"
                  onClick={() => remove(selected.id)}
                  className="text-zinc-400 hover:text-err"
                >
                  <Trash size={14} />
                </button>
                <button onClick={() => setSelected(null)} className="text-zinc-400 hover:text-amber">
                  <X size={14} />
                </button>
              </div>
            </div>
            <div className="p-6 overflow-auto whitespace-pre-wrap text-sm leading-relaxed">
              {selected.conteudo_relatorio}
            </div>
          </div>
        </div>
      )}

      {showAdd && (
        <div className="fixed inset-0 bg-black/80 z-50 flex items-center justify-center p-6">
          <div className="panel w-full max-w-2xl p-6 space-y-4">
            <div className="flex justify-between">
              <h3 className="font-display text-xl">Novo relatório</h3>
              <button onClick={() => setShowAdd(false)} className="text-zinc-500 hover:text-amber">
                <X size={18} />
              </button>
            </div>
            <input
              data-testid="report-periodo"
              value={form.periodo}
              onChange={(e) => setForm({ ...form, periodo: e.target.value })}
              placeholder="período (ex: 26/05/2025 a 30/05/2025)"
              className="w-full bg-bg border border-zinc-800 focus:border-amber px-3 py-2 outline-none font-mono text-sm"
            />
            <textarea
              data-testid="report-conteudo"
              value={form.conteudo_relatorio}
              onChange={(e) => setForm({ ...form, conteudo_relatorio: e.target.value })}
              rows={12}
              placeholder="conteúdo do relatório..."
              className="w-full bg-bg border border-zinc-800 focus:border-amber px-3 py-2 outline-none font-mono text-sm resize-none"
            />
            <div className="flex justify-end gap-2">
              <button onClick={() => setShowAdd(false)} className="btn-ghost">CANCELAR</button>
              <button data-testid="save-report-btn" onClick={save} className="btn-amber">SALVAR</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
