import React, { useEffect, useState } from "react";
import { api, API } from "../api";
import { Copy, Trash, FileText, X, Plus, Lightning, CalendarBlank, FilePdf, Gear } from "@phosphor-icons/react";
import { toast } from "sonner";

export default function Reports() {
  const [list, setList] = useState([]);
  const [selected, setSelected] = useState(null);
  const [showAdd, setShowAdd] = useState(false);
  const [form, setForm] = useState({ periodo: "", conteudo_relatorio: "" });

  // mensal
  const [monthlyCfg, setMonthlyCfg] = useState(null);
  const [monthlyHistory, setMonthlyHistory] = useState([]);
  const [monthlyBusy, setMonthlyBusy] = useState(false);
  const [showMonthlyCfg, setShowMonthlyCfg] = useState(false);
  const [favorites, setFavorites] = useState([]);
  const [monthInput, setMonthInput] = useState("");

  const load = () =>
    api.get("/reports").then(({ data }) => setList(data || []))
      .catch(() => toast.error("Falha ao carregar relatórios"));

  const loadMonthly = async () => {
    try {
      const [{ data: cfgData }, { data: favs }] = await Promise.all([
        api.get("/analytics/auto-monthly"),
        api.get("/whatsapp/favorites"),
      ]);
      setMonthlyCfg(cfgData.config);
      setMonthlyHistory(cfgData.reports || []);
      setFavorites(favs || []);
    } catch { /* silencioso */ }
  };

  useEffect(() => { load(); loadMonthly(); }, []);

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

  const copy = (txt) => { navigator.clipboard.writeText(txt); toast.success("Copiado"); };

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

  const generateMonthly = async (month = null) => {
    setMonthlyBusy(true);
    try {
      const { data } = await api.post("/analytics/auto-monthly/run-now", { month });
      toast.success(`Resumo mensal ${data.month} gerado`);
      loadMonthly();
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Falha ao gerar resumo mensal");
    } finally {
      setMonthlyBusy(false);
    }
  };

  const downloadMonthly = (filename) => {
    window.open(`${API}/analytics/auto-monthly/download/${filename}`, "_blank", "noopener");
  };

  const saveMonthlyCfg = async (patch) => {
    try {
      const { data } = await api.post("/analytics/auto-monthly", { ...monthlyCfg, ...patch });
      setMonthlyCfg(data.config);
      toast.success("Agendamento mensal atualizado");
    } catch { toast.error("Falha ao salvar"); }
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-end justify-between flex-wrap gap-3">
        <div>
          <h1 className="font-display text-3xl">Relatórios Armazenados</h1>
          <p className="text-zinc-500 text-xs tracking-widest uppercase mt-1">
            // {list.length} REGISTROS NO BANCO · {monthlyHistory.length} RESUMOS MENSAIS GERADOS
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button data-testid="add-report-btn" onClick={() => setShowAdd(true)}
            className="btn-amber inline-flex items-center gap-2">
            <Plus size={16} weight="bold" /> ADICIONAR
          </button>
          <button data-testid="auto-weekly-btn"
            onClick={async () => {
              try {
                const { data } = await api.post("/reports/auto-weekly");
                if (data.created) { toast.success("Resumo semanal gerado"); load(); }
                else toast.info(data.reason || "Sem dados");
              } catch { toast.error("Falha"); }
            }}
            className="btn-ghost inline-flex items-center gap-2">
            <Lightning size={14} weight="fill" /> RESUMO SEMANAL AGORA
          </button>
          <button data-testid="auto-monthly-btn" onClick={() => generateMonthly()}
            disabled={monthlyBusy}
            className="bg-amber-500 text-[#050505] hover:bg-amber-400 disabled:opacity-50 font-bold uppercase tracking-wider text-xs px-4 py-2 rounded inline-flex items-center gap-2 transition-colors">
            <CalendarBlank size={14} weight="fill" />
            {monthlyBusy ? "GERANDO…" : "RESUMO MENSAL AGORA"}
          </button>
          <button data-testid="monthly-config-btn" onClick={() => setShowMonthlyCfg(true)}
            className="btn-ghost inline-flex items-center gap-2">
            <Gear size={14} weight="fill" /> AGENDAR MENSAL
          </button>
        </div>
      </div>

      {/* MENSAIS GERADOS */}
      {monthlyHistory.length > 0 && (
        <div className="panel p-5">
          <div className="flex items-center justify-between mb-3">
            <span className="text-amber text-[11px] tracking-widest uppercase font-bold flex items-center gap-2">
              <CalendarBlank size={14} weight="fill" /> Resumos mensais (macro)
            </span>
            <span className="text-zinc-600 text-[10px] font-mono">{monthlyHistory.length} arquivos</span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {monthlyHistory.map((r) => (
              <button key={r.filename}
                onClick={() => downloadMonthly(r.filename)}
                data-testid={`monthly-card-${r.filename}`}
                className="border border-zinc-800 hover:border-amber rounded p-3 text-left transition-colors">
                <div className="flex items-center gap-2 text-amber text-[11px] tracking-widest uppercase">
                  <FilePdf size={14} weight="fill" /> {r.month}
                </div>
                <div className="text-zinc-500 text-[10px] mt-1">
                  {new Date(r.gerado_em).toLocaleString("pt-BR")}
                </div>
                <div className="text-zinc-300 text-xs mt-2">
                  {r.total_atendimentos} atend. · {r.total_preventivas} prev.
                </div>
                <div className="text-amber text-[10px] mt-1">[baixar PDF]</div>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* RELATÓRIOS NO BANCO */}
      <div>
        <div className="text-zinc-500 text-[11px] tracking-widest uppercase font-bold mb-3 mt-2">
          // RELATÓRIOS NO BANCO
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {list.length === 0 && (
            <div className="panel p-6 text-zinc-600 text-sm col-span-3">
              Nenhum relatório arquivado.
            </div>
          )}
          {list.map((r) => (
            <button data-testid={`report-card-${r.id}`} key={r.id} onClick={() => open(r.id)}
              className="panel p-4 text-left hover:border-amber transition-none">
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
      </div>

      {/* VIEWER */}
      {selected && (
        <div className="fixed inset-0 bg-black/80 z-50 flex items-center justify-center p-6">
          <div className="panel w-full max-w-3xl max-h-[90vh] flex flex-col">
            <div className="panel-header">
              <span className="text-amber">{selected.periodo}</span>
              <div className="flex items-center gap-2">
                <button data-testid="copy-report-btn" onClick={() => copy(selected.conteudo_relatorio)} className="text-zinc-400 hover:text-amber">
                  <Copy size={14} />
                </button>
                <button data-testid="delete-report-btn" onClick={() => remove(selected.id)} className="text-zinc-400 hover:text-err">
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

      {/* ADD MANUAL */}
      {showAdd && (
        <div className="fixed inset-0 bg-black/80 z-50 flex items-center justify-center p-6">
          <div className="panel w-full max-w-2xl p-6 space-y-4">
            <div className="flex justify-between">
              <h3 className="font-display text-xl">Novo relatório</h3>
              <button onClick={() => setShowAdd(false)} className="text-zinc-500 hover:text-amber"><X size={18} /></button>
            </div>
            <input data-testid="report-periodo" value={form.periodo}
              onChange={(e) => setForm({ ...form, periodo: e.target.value })}
              placeholder="período (ex: 26/05/2026 a 30/05/2026)"
              className="w-full bg-bg border border-zinc-800 focus:border-amber px-3 py-2 outline-none font-mono text-sm" />
            <textarea data-testid="report-conteudo" value={form.conteudo_relatorio}
              onChange={(e) => setForm({ ...form, conteudo_relatorio: e.target.value })}
              rows={12} placeholder="conteúdo do relatório..."
              className="w-full bg-bg border border-zinc-800 focus:border-amber px-3 py-2 outline-none font-mono text-sm resize-none" />
            <div className="flex justify-end gap-2">
              <button onClick={() => setShowAdd(false)} className="btn-ghost">CANCELAR</button>
              <button data-testid="save-report-btn" onClick={save} className="btn-amber">SALVAR</button>
            </div>
          </div>
        </div>
      )}

      {/* CONFIG MENSAL */}
      {showMonthlyCfg && monthlyCfg && (
        <div className="fixed inset-0 bg-black/80 z-50 flex items-center justify-center p-6">
          <div className="panel w-full max-w-lg p-6 space-y-4">
            <div className="flex justify-between items-center">
              <h3 className="font-display text-xl">Resumo mensal — agendamento</h3>
              <button onClick={() => setShowMonthlyCfg(false)} className="text-zinc-500 hover:text-amber"><X size={18} /></button>
            </div>

            <label className="flex items-center gap-3 cursor-pointer">
              <input type="checkbox" data-testid="monthly-cfg-enabled"
                checked={!!monthlyCfg.monthly_enabled}
                onChange={(e) => saveMonthlyCfg({ monthly_enabled: e.target.checked })}
                className="w-4 h-4 accent-amber-500" />
              <span className="text-gray-200 text-sm">Gerar resumo macro automaticamente todo mês</span>
            </label>

            <div className="grid grid-cols-3 gap-3">
              <div>
                <label className="text-[10px] uppercase tracking-widest text-zinc-500 mb-1 block">Dia do mês</label>
                <input data-testid="monthly-cfg-day" type="number" min="1" max="28"
                  value={monthlyCfg.monthly_day}
                  onChange={(e) => setMonthlyCfg({ ...monthlyCfg, monthly_day: parseInt(e.target.value || "1", 10) })}
                  onBlur={() => saveMonthlyCfg({ monthly_day: monthlyCfg.monthly_day })}
                  className="w-full bg-bg border border-zinc-800 focus:border-amber px-3 py-2 outline-none font-mono text-sm" />
              </div>
              <div>
                <label className="text-[10px] uppercase tracking-widest text-zinc-500 mb-1 block">Hora</label>
                <input data-testid="monthly-cfg-hour" type="number" min="0" max="23"
                  value={monthlyCfg.monthly_hour}
                  onChange={(e) => setMonthlyCfg({ ...monthlyCfg, monthly_hour: parseInt(e.target.value || "0", 10) })}
                  onBlur={() => saveMonthlyCfg({ monthly_hour: monthlyCfg.monthly_hour })}
                  className="w-full bg-bg border border-zinc-800 focus:border-amber px-3 py-2 outline-none font-mono text-sm" />
              </div>
              <div>
                <label className="text-[10px] uppercase tracking-widest text-zinc-500 mb-1 block">Minuto</label>
                <input data-testid="monthly-cfg-min" type="number" min="0" max="59"
                  value={monthlyCfg.monthly_minute}
                  onChange={(e) => setMonthlyCfg({ ...monthlyCfg, monthly_minute: parseInt(e.target.value || "0", 10) })}
                  onBlur={() => saveMonthlyCfg({ monthly_minute: monthlyCfg.monthly_minute })}
                  className="w-full bg-bg border border-zinc-800 focus:border-amber px-3 py-2 outline-none font-mono text-sm" />
              </div>
            </div>

            <label className="flex items-center gap-3 cursor-pointer">
              <input type="checkbox" data-testid="monthly-cfg-whatsapp"
                checked={!!monthlyCfg.monthly_send_whatsapp}
                onChange={(e) => saveMonthlyCfg({ monthly_send_whatsapp: e.target.checked })}
                className="w-4 h-4 accent-[#25D366]" />
              <span className="text-gray-400 text-xs">Enviar no WhatsApp automaticamente <span className="text-amber-500">(somente no app desktop)</span></span>
            </label>

            <div>
              <label className="text-[10px] uppercase tracking-widest text-zinc-500 mb-1 block">Destino padrão (WhatsApp)</label>
              <select data-testid="monthly-cfg-destination"
                value={monthlyCfg.monthly_whatsapp_destination_id || ""}
                onChange={(e) => saveMonthlyCfg({ monthly_whatsapp_destination_id: e.target.value || null })}
                className="w-full bg-bg border border-zinc-800 focus:border-amber px-3 py-2 outline-none font-mono text-sm">
                <option value="">— nenhum (usa WHATSAPP_GRUPO do .env) —</option>
                {favorites.map((f) => (
                  <option key={f.id} value={f.id}>[{f.tipo}] {f.display_name}</option>
                ))}
              </select>
              {favorites.length === 0 && (
                <p className="text-[10px] text-zinc-600 mt-1">Cadastre favoritos em /whatsapp para usar no dropdown.</p>
              )}
            </div>

            <div className="border-t border-[#27272A] pt-3">
              <label className="text-[10px] uppercase tracking-widest text-zinc-500 mb-1 block">Gerar resumo de um mês específico</label>
              <div className="flex gap-2">
                <input data-testid="monthly-cfg-month-input" type="month" value={monthInput}
                  onChange={(e) => setMonthInput(e.target.value)}
                  className="flex-1 bg-bg border border-zinc-800 focus:border-amber px-3 py-2 outline-none font-mono text-sm" />
                <button data-testid="monthly-cfg-generate-month"
                  onClick={() => { if (!monthInput) { toast.error("Escolha um mês"); return; } generateMonthly(monthInput); }}
                  disabled={monthlyBusy}
                  className="btn-amber inline-flex items-center gap-2 text-xs">
                  <FilePdf size={14} weight="fill" /> GERAR
                </button>
              </div>
              <p className="text-[10px] text-zinc-600 mt-1">Vazio = gera do mês anterior fechado (default).</p>
            </div>

            <div className="flex justify-end pt-2">
              <button onClick={() => setShowMonthlyCfg(false)} className="btn-ghost">FECHAR</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
