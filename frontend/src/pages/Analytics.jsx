import React, { useEffect, useRef, useState, useCallback } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import "leaflet.heat";
import { api, API } from "../api";
import {
  BarChart, Bar, LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, CartesianGrid,
} from "recharts";
import {
  ChartLine, Gauge, MapPin, Wrench, Fire, GasPump, CalendarBlank, ArrowsClockwise,
  FileCsv, FileXls, FilePdf, FunnelSimple, X, Path, Truck, Wrench as WrenchIcon, WhatsappLogo,
} from "@phosphor-icons/react";
import { toast } from "sonner";

const AMBER = "#F59E0B";
const COLORS = ["#F59E0B", "#D97706", "#B45309", "#92400E", "#78350F", "#FBBF24", "#FCD34D", "#FEF3C7"];
const SP_CENTER = [-23.5505, -46.6333];

const chartTooltip = {
  backgroundColor: "#0A0A0A", border: "1px solid #F59E0B", borderRadius: "4px",
  color: "#F3F4F6", fontFamily: "JetBrains Mono", fontSize: 12,
};

export default function Analytics() {
  const [kpis, setKpis] = useState(null);
  const [weekly, setWeekly] = useState([]);
  const [monthly, setMonthly] = useState([]);
  const [daily, setDaily] = useState([]);
  const [heatmap, setHeatmap] = useState([]);
  const [activities, setActivities] = useState([]);
  const [mapData, setMapData] = useState(null);
  const [unidades, setUnidades] = useState([]);
  const [monthDetail, setMonthDetail] = useState(null);
  const [loading, setLoading] = useState(false);

  // filtros
  const [start, setStart] = useState("");
  const [end, setEnd] = useState("");
  const [unidade, setUnidade] = useState("");
  const [fuelCost, setFuelCost] = useState(5.89);
  const [kmPerLiter, setKmPerLiter] = useState(10);

  // relatório automático
  const [autoCfg, setAutoCfg] = useState(null);
  const [autoNext, setAutoNext] = useState(null);
  const [autoReports, setAutoReports] = useState([]);
  const [genBusy, setGenBusy] = useState(false);

  // PDF custom + favoritos WhatsApp
  const [pdfCatalog, setPdfCatalog] = useState(null);
  const [showPdfModal, setShowPdfModal] = useState(false);
  const [pdfSel, setPdfSel] = useState({ kpis: [], columns: [], sections: [] });
  const [favorites, setFavorites] = useState([]);
  const [showShareModal, setShowShareModal] = useState(false);
  const [shareDest, setShareDest] = useState("");

  // refs do mapa
  const mapInstance = useRef(null);
  const heatRef = useRef(null);
  const markersRef = useRef(null);

  // callback ref: inicializa o mapa assim que o container monta no DOM
  const setMapEl = useCallback((node) => {
    if (!node || mapInstance.current) return;
    const map = L.map(node, { zoomControl: true, scrollWheelZoom: false }).setView(SP_CENTER, 11);
    L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", {
      attribution: "&copy; <a href='https://carto.com/'>CARTO</a>", maxZoom: 19,
    }).addTo(map);
    markersRef.current = L.layerGroup().addTo(map);
    mapInstance.current = map;
    setTimeout(() => map.invalidateSize(), 200);
  }, []);

  const filterQS = useCallback((extra = {}, override = null) => {
    const src = override || { start, end, unidade };
    const p = new URLSearchParams();
    if (src.start) p.set("start", src.start);
    if (src.end) p.set("end", src.end);
    if (src.unidade) p.set("unidade", src.unidade);
    Object.entries(extra).forEach(([k, v]) => p.set(k, v));
    return p.toString();
  }, [start, end, unidade]);

  const loadAll = useCallback(async (override = null) => {
    setLoading(true);
    const base = filterQS({}, override);
    // KPIs/charts: cada um independente — falha de um não derruba a página
    const results = await Promise.allSettled([
      api.get(`/analytics/kpis?${filterQS({ fuel_cost: fuelCost, km_per_liter: kmPerLiter }, override)}`),
      api.get(`/analytics/weekly?${base}&weeks=12`),
      api.get(`/analytics/daily?days=30`),
      api.get(`/analytics/heatmap`),
      api.get(`/analytics/activities?${base}`),
    ]);
    const [k, w, d, h, a] = results;
    if (k.status === "fulfilled") setKpis(k.value.data);
    if (w.status === "fulfilled") setWeekly(w.value.data);
    if (d.status === "fulfilled") setDaily(d.value.data);
    if (h.status === "fulfilled") setHeatmap(h.value.data);
    if (a.status === "fulfilled") setActivities(a.value.data);
    if (results.some((r) => r.status === "rejected")) toast.error("Alguns dados falharam ao carregar");
    setLoading(false);
    // mapa carrega em separado (não bloqueia KPIs/gráficos)
    api.get(`/analytics/map-data?${base}&allow_remote=true`)
      .then((mp) => setMapData(mp.data))
      .catch(() => toast.error("Falha ao carregar o mapa"));
  }, [filterQS, fuelCost, kmPerLiter]);

  // carga inicial: monthly + unidades (não dependem de filtro) + tudo
  useEffect(() => {
    api.get("/analytics/monthly?months=12").then((r) => setMonthly(r.data)).catch(() => {});
    api.get("/analytics/unidades").then((r) => setUnidades(r.data)).catch(() => {});
    loadAutoReport();
    loadAll();
    // eslint-disable-next-line
  }, []);

  const loadAutoReport = async () => {
    try {
      const { data } = await api.get("/analytics/auto-report");
      setAutoCfg(data.config); setAutoNext(data.next_run); setAutoReports(data.reports || []);
    } catch { /* silencioso */ }
  };

  const saveAutoCfg = async (patch) => {
    const optimistic = { ...autoCfg, ...patch };
    setAutoCfg(optimistic);
    try {
      const { data } = await api.post("/analytics/auto-report", patch);
      setAutoCfg(data.config); setAutoNext(data.next_run);
      toast.success("Agendamento atualizado");
    } catch { toast.error("Falha ao salvar agendamento"); loadAutoReport(); }
  };

  const runReportNow = async () => {
    setGenBusy(true);
    try {
      const { data } = await api.post("/analytics/auto-report/run-now");
      toast.success(`Relatório gerado (${data.total_km} km)`);
      downloadReport(data.filename);
      loadAutoReport();
    } catch { toast.error("Falha ao gerar relatório"); }
    finally { setGenBusy(false); }
  };

  const downloadReport = (filename) => {
    const a = document.createElement("a");
    a.href = `${API}/analytics/auto-report/download/${encodeURIComponent(filename)}`;
    a.rel = "noopener";
    document.body.appendChild(a); a.click(); a.remove();
  };

  // ---- Mapa: atualiza heat + marcadores quando mapData muda ----
  useEffect(() => {
    const map = mapInstance.current;
    if (!map || !mapData) return;
    if (heatRef.current) { map.removeLayer(heatRef.current); heatRef.current = null; }
    markersRef.current.clearLayers();
    const pts = (mapData.points || []).map((p) => [p.lat, p.lng, Math.max(p.weight, 0.25)]);
    if (pts.length) {
      heatRef.current = L.heatLayer(pts, {
        radius: 28, blur: 20, maxZoom: 14, minOpacity: 0.35,
        gradient: { 0.3: "#fde68a", 0.5: "#f59e0b", 0.75: "#d97706", 1.0: "#b45309" },
      }).addTo(map);
    }
    (mapData.points || []).forEach((p) => {
      L.circleMarker([p.lat, p.lng], {
        radius: 5, color: "#F59E0B", weight: 1.5, fillColor: "#F59E0B", fillOpacity: 0.9,
      }).bindTooltip(
        `<div style="font-family:JetBrains Mono;font-size:11px"><b style="color:#F59E0B">${p.unidade}</b><br/>${p.visitas} visitas · ${p.km_total} km</div>`,
        { direction: "top", opacity: 0.95 }
      ).addTo(markersRef.current);
    });
    if (mapData.center) map.setView(mapData.center, map.getZoom());
    setTimeout(() => map.invalidateSize(), 150);
  }, [mapData]);

  const openMonth = async (mk) => {
    try { const { data } = await api.get(`/analytics/month/${mk}`); setMonthDetail(data); }
    catch { toast.error("Sem dados para o mês"); }
  };

  const exportData = (format) => {
    if (format === "pdf") {
      // Abre modal de seleção de campos
      openPdfModal();
      return;
    }
    const url = `${API}/analytics/export?${filterQS({ format, fuel_cost: fuelCost, km_per_liter: kmPerLiter })}`;
    const a = document.createElement("a");
    a.href = url; a.rel = "noopener";
    document.body.appendChild(a); a.click(); a.remove();
    toast.success(`Exportando ${format.toUpperCase()}…`);
  };

  const openPdfModal = async () => {
    try {
      if (!pdfCatalog) {
        const { data } = await api.get("/analytics/pdf-fields");
        setPdfCatalog(data);
        // Tenta carregar preferência do localStorage
        const saved = JSON.parse(localStorage.getItem("mavis_pdf_fields") || "null");
        setPdfSel(saved || data.defaults);
      }
      setShowPdfModal(true);
    } catch {
      toast.error("Falha ao carregar opções do PDF");
    }
  };

  const togglePdfItem = (group, key) => {
    setPdfSel((prev) => {
      const cur = new Set(prev[group] || []);
      cur.has(key) ? cur.delete(key) : cur.add(key);
      return { ...prev, [group]: Array.from(cur) };
    });
  };

  const resetPdfSel = () => { if (pdfCatalog) setPdfSel(pdfCatalog.defaults); };

  const downloadCustomPdf = async () => {
    try {
      localStorage.setItem("mavis_pdf_fields", JSON.stringify(pdfSel));
      const res = await api.post("/analytics/export-pdf", {
        start, end, unidade,
        fuel_cost: fuelCost, km_per_liter: kmPerLiter,
        fields: pdfSel,
      }, { responseType: "blob" });
      const url = URL.createObjectURL(res.data);
      const a = document.createElement("a");
      const stamp = new Date().toISOString().slice(0, 16).replace(/[-:T]/g, "");
      a.href = url; a.download = `mavis_analytics_${stamp}.pdf`;
      document.body.appendChild(a); a.click(); a.remove();
      URL.revokeObjectURL(url);
      setShowPdfModal(false);
      toast.success("PDF gerado com os campos selecionados");
    } catch {
      toast.error("Falha ao gerar PDF");
    }
  };

  const shareWhatsApp = async (override = null, titulo = "") => {
    // Carrega favoritos antes de abrir o modal
    try {
      if (favorites.length === 0) {
        const { data } = await api.get("/whatsapp/favorites");
        setFavorites(data || []);
      }
    } catch { /* segue mesmo sem favoritos */ }
    setShareDest("");
    setShowShareModal(true);
    // Guarda contexto para usar quando o usuário clicar "Enviar"
    setShareContext({ override, titulo });
  };

  const [shareContext, setShareContext] = useState({ override: null, titulo: "" });

  const doShareWhatsApp = async () => {
    const { override, titulo } = shareContext;
    try {
      const qs = filterQS({ fuel_cost: fuelCost, km_per_liter: kmPerLiter, ...(titulo ? { titulo } : {}) }, override);
      const { data } = await api.get(`/analytics/resumo?${qs}`);
      // baixa o PDF para o usuário anexar no WhatsApp
      const pdfUrl = `${API}/analytics/export?${filterQS({ format: "pdf", fuel_cost: fuelCost, km_per_liter: kmPerLiter }, override)}`;
      const a = document.createElement("a");
      a.href = pdfUrl; a.rel = "noopener";
      document.body.appendChild(a); a.click(); a.remove();

      // Se selecionou favorito, tenta o envio direto via backend (que detecta DESKTOP_MODE)
      if (shareDest) {
        try {
          const send = await api.post("/whatsapp/send", { favorite_id: shareDest, message: data.texto });
          if (send.data.sent) {
            toast.success(`Resumo enviado para ${send.data.destino?.nome}. PDF baixado para anexar.`);
            setShowShareModal(false);
            return;
          }
          if (send.data.wa_url) {
            // Modo hospedado: abre wa.me e mostra qual destino selecionar
            window.open(send.data.wa_url, "_blank", "noopener");
            toast.info(`Envio automático só funciona local. Selecione o destino "${send.data.destino?.nome}" e anexe o PDF.`);
            setShowShareModal(false);
            return;
          }
        } catch { /* cai no fallback wa.me genérico */ }
      }

      // Fallback: wa.me genérico (sem destino fixo)
      window.open(`https://wa.me/?text=${encodeURIComponent(data.texto)}`, "_blank", "noopener");
      toast.success("Resumo pronto! Escolha a conversa e anexe o PDF baixado.");
      setShowShareModal(false);
    } catch {
      toast.error("Falha ao gerar o resumo");
    }
  };

  const clearFilters = () => {
    setStart(""); setEnd(""); setUnidade("");
    loadAll({ start: "", end: "", unidade: "" });
  };

  const maxHeat = Math.max(1, ...heatmap.map((h) => h.km));

  return (
    <div className="min-h-screen bg-[#050505] noise relative">
      {/* HEADER GLASS */}
      <div className="backdrop-blur-xl bg-[#050505]/80 border-b border-[#27272A] sticky top-0 z-[1000]">
        <div className="max-w-[1800px] mx-auto px-4 md:px-8 py-4 flex items-center justify-between flex-wrap gap-3">
          <div>
            <h1 className="font-display text-2xl md:text-3xl font-bold tracking-tight text-gray-50">Analytics</h1>
            <p className="text-amber-500 text-[10px] md:text-xs tracking-[0.2em] uppercase font-bold mt-0.5">
              // KM · DESTINOS · COMBUSTÍVEL · MAPA DE CALOR
            </p>
          </div>
          <div className="flex items-center gap-2 flex-wrap">
            <button onClick={() => shareWhatsApp()} data-testid="share-whatsapp-button"
              className="inline-flex items-center gap-1.5 bg-[#25D366] text-[#052e16] hover:bg-[#22c55e] font-bold uppercase tracking-wider text-xs px-3 py-2 rounded transition-colors">
              <WhatsappLogo size={15} weight="fill" /> Compartilhar
            </button>
            <ExportBtn icon={FileCsv} label="CSV" onClick={() => exportData("csv")} testid="export-csv-button" />
            <ExportBtn icon={FileXls} label="EXCEL" onClick={() => exportData("xlsx")} testid="export-xlsx-button" />
            <ExportBtn icon={FilePdf} label="PDF" onClick={() => exportData("pdf")} testid="export-pdf-button" />
            <button onClick={() => loadAll()} disabled={loading} data-testid="analytics-refresh"
              className="inline-flex items-center gap-2 bg-amber-500 text-[#050505] hover:bg-amber-400 disabled:opacity-50 font-bold uppercase tracking-wider text-xs px-4 py-2 rounded transition-colors">
              <ArrowsClockwise size={14} className={loading ? "animate-spin" : ""} weight="bold" /> Atualizar
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-[1800px] mx-auto p-4 md:p-8 space-y-6">
        {/* FILTROS */}
        <div className="flex flex-wrap items-end gap-4 p-4 md:p-5 bg-[#0A0A0A] border border-[#27272A] rounded-lg">
          <div className="flex items-center gap-2 text-amber-500 mr-1">
            <FunnelSimple size={16} weight="bold" />
            <span className="text-[10px] uppercase tracking-[0.2em] font-bold hidden md:inline">Filtros</span>
          </div>
          <Field label="Data início">
            <input data-testid="filter-start" type="date" value={start} onChange={(e) => setStart(e.target.value)}
              className="bg-[#050505] border border-[#27272A] text-gray-200 text-sm rounded px-3 py-1.5 focus:border-amber-500 focus:outline-none transition-colors" />
          </Field>
          <Field label="Data fim">
            <input data-testid="filter-end" type="date" value={end} onChange={(e) => setEnd(e.target.value)}
              className="bg-[#050505] border border-[#27272A] text-gray-200 text-sm rounded px-3 py-1.5 focus:border-amber-500 focus:outline-none transition-colors" />
          </Field>
          <Field label="Unidade">
            <select data-testid="filter-unidade" value={unidade} onChange={(e) => setUnidade(e.target.value)}
              className="bg-[#050505] border border-[#27272A] text-gray-200 text-sm rounded px-3 py-1.5 focus:border-amber-500 focus:outline-none transition-colors min-w-[180px] max-w-[240px]">
              <option value="">Todas</option>
              {unidades.map((u) => <option key={u} value={u}>{u}</option>)}
            </select>
          </Field>
          <Field label="R$ / Litro">
            <input data-testid="fuel-cost" type="number" step="0.01" value={fuelCost}
              onChange={(e) => setFuelCost(parseFloat(e.target.value) || 0)}
              className="w-24 bg-[#050505] border border-[#27272A] text-gray-200 text-sm rounded px-3 py-1.5 focus:border-amber-500 focus:outline-none transition-colors" />
          </Field>
          <Field label="KM / Litro">
            <input data-testid="kmpl" type="number" step="0.5" value={kmPerLiter}
              onChange={(e) => setKmPerLiter(parseFloat(e.target.value) || 1)}
              className="w-20 bg-[#050505] border border-[#27272A] text-gray-200 text-sm rounded px-3 py-1.5 focus:border-amber-500 focus:outline-none transition-colors" />
          </Field>
          <button onClick={() => loadAll()} data-testid="apply-filters"
            className="bg-amber-500 text-[#050505] hover:bg-amber-400 font-bold uppercase tracking-wider text-xs px-5 py-2 rounded transition-colors">
            Aplicar
          </button>
          <button onClick={clearFilters} data-testid="clear-filters"
            className="border border-[#27272A] text-gray-400 hover:border-amber-500 hover:text-amber-500 font-bold uppercase tracking-wider text-xs px-4 py-2 rounded transition-colors">
            Limpar
          </button>
        </div>

        {!kpis && <div className="p-12 text-center text-gray-500 blink-caret">carregando dados</div>}

        {kpis && (
          <>
            {/* KPI CARDS */}
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
              <KPI testid="kpi-total-km" icon={Gauge} label="Total KM" value={kpis.total_km} accent />
              <KPI testid="kpi-dias" icon={CalendarBlank} label="Dias úteis" value={kpis.total_dias} />
              <KPI icon={Path} label="Média KM/dia" value={kpis.media_km_dia} />
              <KPI icon={ChartLine} label="Média KM/semana" value={kpis.media_km_semana} />
              <KPI icon={GasPump} label="Litros" value={kpis.litros_estimados} sub={`${kmPerLiter} km/L`} />
              <KPI testid="kpi-custo" icon={Fire} label="Combustível R$"
                value={kpis.custo_combustivel.toLocaleString("pt-BR", { minimumFractionDigits: 2 })} accent />
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <KPI icon={WrenchIcon} label="Preventivas" value={kpis.total_preventivas} />
              <KPI icon={Wrench} label="Atendimentos téc." value={kpis.total_atendimentos} />
              <KPI icon={Truck} label="Entregas insumos" value={kpis.total_entregas_insumos} />
              <KPI icon={ArrowsClockwise} label="Trocas equip." value={kpis.total_trocas_equipamentos} />
            </div>

            {/* MAPA DE CALOR GEOGRÁFICO */}
            <div className="bg-[#0A0A0A] border border-[#27272A] rounded-lg overflow-hidden transition-all hover:border-amber-500/40">
              <div className="flex items-center justify-between px-5 py-3 border-b border-[#27272A]">
                <span className="text-amber-500 text-xs uppercase tracking-[0.2em] font-bold flex items-center gap-2">
                  <MapPin size={14} weight="fill" /> Mapa de Calor · Unidades visitadas
                </span>
                <span className="text-gray-500 text-[11px] font-mono">
                  {mapData?.total_unidades || 0} unidades · {mapData?.total_visitas || 0} visitas
                </span>
              </div>
              <div ref={setMapEl} data-testid="heatmap-geo" className="h-[440px] w-full z-0" />
              {mapData?.unresolved?.length > 0 && (
                <div className="px-5 py-2 border-t border-[#27272A] text-[11px] text-gray-500 font-mono">
                  <span className="text-amber-500">{mapData.unresolved.length} não geolocalizadas:</span>{" "}
                  {mapData.unresolved.join(" · ")}
                </div>
              )}
            </div>

            {/* WEEKLY + ACTIVITIES */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <Panel title="KM por semana (últimas 12)" className="lg:col-span-2">
                <div data-testid="chart-weekly" className="p-5">
                  <ResponsiveContainer width="100%" height={280}>
                    <BarChart data={weekly}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#27272A" vertical={false} />
                      <XAxis dataKey="semana" stroke="#52525B" tick={{ fill: "#9CA3AF", fontSize: 11, fontFamily: "JetBrains Mono" }} />
                      <YAxis stroke="#52525B" tick={{ fill: "#9CA3AF", fontSize: 11, fontFamily: "JetBrains Mono" }} />
                      <Tooltip contentStyle={chartTooltip} itemStyle={{ color: AMBER }} cursor={{ fill: "#141414" }} />
                      <Bar dataKey="km" fill={AMBER} radius={[3, 3, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </Panel>

              <Panel title="Tipos de atividade">
                <div className="p-5" data-testid="chart-activities">
                  <ResponsiveContainer width="100%" height={220}>
                    <PieChart>
                      <Pie data={activities} dataKey="qtd" nameKey="tipo" cx="50%" cy="50%"
                        innerRadius={55} outerRadius={85} stroke="#0A0A0A" strokeWidth={2}>
                        {activities.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                      </Pie>
                      <Tooltip contentStyle={chartTooltip} itemStyle={{ color: AMBER }} />
                    </PieChart>
                  </ResponsiveContainer>
                  <div className="space-y-1.5 mt-3 font-mono text-[11px]">
                    {activities.map((a, i) => (
                      <div key={i} className="flex justify-between items-center">
                        <span className="flex items-center gap-2 text-gray-300">
                          <span className="w-2.5 h-2.5 rounded-sm" style={{ background: COLORS[i % COLORS.length] }} />
                          {a.tipo}
                        </span>
                        <span className="text-amber-500 font-bold">{a.qtd}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </Panel>
            </div>

            {/* MENSAL */}
            <Panel title="Resumo mensal" right={`${monthly.length} ${monthly.length === 1 ? "mês" : "meses"}`}>
              <div className="p-5" data-testid="chart-monthly">
                <ResponsiveContainer width="100%" height={220}>
                  <BarChart data={monthly}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#27272A" vertical={false} />
                    <XAxis dataKey="mes" stroke="#52525B" tick={{ fill: "#9CA3AF", fontSize: 11, fontFamily: "JetBrains Mono" }} />
                    <YAxis stroke="#52525B" tick={{ fill: "#9CA3AF", fontSize: 11, fontFamily: "JetBrains Mono" }} />
                    <Tooltip contentStyle={chartTooltip} itemStyle={{ color: AMBER }} cursor={{ fill: "#141414" }} />
                    <Bar dataKey="km" fill={AMBER} radius={[3, 3, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
              <div className="border-t border-[#27272A] p-5 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                {monthly.map((m) => (
                  <button key={m.mes} onClick={() => openMonth(m.mes)} data-testid={`month-${m.mes}`}
                    className="border border-[#27272A] hover:border-amber-500/60 hover:bg-[#141414] p-3 text-left font-mono text-xs space-y-1.5 rounded transition-all">
                    <div className="flex justify-between">
                      <span className="text-amber-500 tracking-widest uppercase">{m.mes}</span>
                      <span className="text-amber-500 font-bold">{m.km} km</span>
                    </div>
                    <div className="text-gray-500 grid grid-cols-2 gap-1 text-[11px]">
                      <span>{m.dias_uteis} dias</span>
                      <span>{m.visitas} visitas</span>
                      <span>{m.preventivas} prev.</span>
                      <span>{m.atendimentos} atend.</span>
                    </div>
                  </button>
                ))}
              </div>
            </Panel>

            {/* WEEKDAY HEATMAP + RANKINGS */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <Panel title="Mapa de calor · dia da semana">
                <div className="p-5 space-y-2.5" data-testid="heatmap-weekday">
                  {heatmap.map((h) => {
                    const intensity = h.km / maxHeat;
                    return (
                      <div key={h.dia} className="flex items-center gap-3 font-mono text-xs">
                        <span className="w-9 text-gray-500">{h.dia}</span>
                        <div className="flex-1 h-7 bg-[#141414] rounded-sm relative overflow-hidden border border-[#27272A]">
                          <div className="h-full rounded-sm transition-all"
                            style={{ width: `${intensity * 100}%`, background: `linear-gradient(90deg,#92400E,${AMBER})` }} />
                          <span className="absolute inset-0 flex items-center px-2 text-gray-200 text-[11px]">
                            {h.km} km · {h.dias}d
                          </span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </Panel>

              <Panel title="Top destinos">
                <div className="p-3 font-mono text-xs">
                  {kpis.top_destinos.slice(0, 10).map((d, i) => (
                    <div key={i} data-testid={`top-destino-${i}`}
                      className="flex items-center gap-3 py-2.5 px-2 border-b border-[#27272A] last:border-0 hover:bg-[#141414] rounded transition-colors">
                      <span className="text-[10px] text-amber-500 bg-amber-500/10 px-2 py-1 rounded font-bold">#{i + 1}</span>
                      <span className="flex-1 text-gray-300 truncate">{d.unidade}</span>
                      <span className="text-amber-500 font-bold">{d.visitas}×</span>
                    </div>
                  ))}
                </div>
              </Panel>

              <Panel title="Top equipamentos">
                <div className="p-3 font-mono text-xs">
                  {kpis.top_equipamentos.map((e, i) => (
                    <div key={i}
                      className="flex items-center gap-3 py-2.5 px-2 border-b border-[#27272A] last:border-0 hover:bg-[#141414] rounded transition-colors">
                      <span className="text-[10px] text-amber-500 bg-amber-500/10 px-2 py-1 rounded font-bold">#{i + 1}</span>
                      <span className="flex-1 text-gray-300 capitalize">{e.item.replace(/_/g, " ")}</span>
                      <span className="text-amber-500 font-bold">{e.qtd}×</span>
                    </div>
                  ))}
                </div>
              </Panel>
            </div>

            {/* DAILY */}
            <Panel title="KM diário (últimos 30 dias com registro)">
              <div className="p-5" data-testid="chart-daily">
                <ResponsiveContainer width="100%" height={240}>
                  <LineChart data={daily}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#27272A" vertical={false} />
                    <XAxis dataKey="date" stroke="#52525B" tick={{ fill: "#9CA3AF", fontSize: 10, fontFamily: "JetBrains Mono" }} />
                    <YAxis stroke="#52525B" tick={{ fill: "#9CA3AF", fontSize: 11, fontFamily: "JetBrains Mono" }} />
                    <Tooltip contentStyle={chartTooltip} itemStyle={{ color: AMBER }} />
                    <Line type="monotone" dataKey="km" stroke={AMBER} strokeWidth={2}
                      dot={{ fill: "#050505", stroke: AMBER, strokeWidth: 2, r: 3 }} activeDot={{ r: 6, fill: AMBER }} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </Panel>

            {/* RELATÓRIO AUTOMÁTICO */}
            {autoCfg && (
              <Panel title="Relatório automático semanal"
                right={autoNext ? `próximo: ${new Date(autoNext).toLocaleString("pt-BR")}` : "desativado"}>
                <div className="p-5 grid grid-cols-1 lg:grid-cols-2 gap-5">
                  <div className="space-y-4">
                    <label className="flex items-center gap-3 cursor-pointer">
                      <input type="checkbox" data-testid="auto-report-enabled" checked={!!autoCfg.enabled}
                        onChange={(e) => saveAutoCfg({ enabled: e.target.checked })}
                        className="w-4 h-4 accent-amber-500" />
                      <span className="text-gray-200 text-sm">Ativar geração automática (resumo + PDF)</span>
                    </label>
                    <div className="flex flex-wrap items-end gap-3">
                      <Field label="Dia">
                        <select data-testid="auto-report-day" value={autoCfg.day_of_week}
                          onChange={(e) => saveAutoCfg({ day_of_week: e.target.value })}
                          className="bg-[#050505] border border-[#27272A] text-gray-200 text-sm rounded px-3 py-1.5 focus:border-amber-500 focus:outline-none">
                          {[["mon", "Segunda"], ["tue", "Terça"], ["wed", "Quarta"], ["thu", "Quinta"], ["fri", "Sexta"], ["sat", "Sábado"], ["sun", "Domingo"]]
                            .map(([v, l]) => <option key={v} value={v}>{l}</option>)}
                        </select>
                      </Field>
                      <Field label="Hora">
                        <input data-testid="auto-report-hour" type="number" min="0" max="23" value={autoCfg.hour}
                          onChange={(e) => saveAutoCfg({ hour: parseInt(e.target.value || "0", 10) })}
                          className="w-20 bg-[#050505] border border-[#27272A] text-gray-200 text-sm rounded px-3 py-1.5 focus:border-amber-500 focus:outline-none" />
                      </Field>
                      <Field label="Min">
                        <input data-testid="auto-report-minute" type="number" min="0" max="59" value={autoCfg.minute}
                          onChange={(e) => saveAutoCfg({ minute: parseInt(e.target.value || "0", 10) })}
                          className="w-20 bg-[#050505] border border-[#27272A] text-gray-200 text-sm rounded px-3 py-1.5 focus:border-amber-500 focus:outline-none" />
                      </Field>
                    </div>
                    <label className="flex items-center gap-3 cursor-pointer">
                      <input type="checkbox" data-testid="auto-report-whatsapp" checked={!!autoCfg.send_whatsapp}
                        onChange={(e) => saveAutoCfg({ send_whatsapp: e.target.checked })}
                        className="w-4 h-4 accent-[#25D366]" />
                      <span className="text-gray-400 text-xs">Enviar no WhatsApp automaticamente <span className="text-amber-500">(somente no app desktop)</span></span>
                    </label>
                    <button onClick={runReportNow} disabled={genBusy} data-testid="auto-report-run-now"
                      className="inline-flex items-center gap-2 bg-amber-500 text-[#050505] hover:bg-amber-400 disabled:opacity-50 font-bold uppercase tracking-wider text-xs px-5 py-2 rounded transition-colors">
                      <FilePdf size={14} weight="bold" /> {genBusy ? "Gerando…" : "Gerar agora"}
                    </button>
                  </div>
                  <div>
                    <div className="text-gray-500 text-[10px] uppercase tracking-widest mb-2">Relatórios gerados</div>
                    <div className="space-y-1 font-mono text-xs max-h-52 overflow-auto" data-testid="auto-report-list">
                      {autoReports.length === 0 && <div className="text-gray-600">Nenhum relatório ainda.</div>}
                      {autoReports.map((r) => (
                        <button key={r.filename} onClick={() => downloadReport(r.filename)}
                          data-testid={`auto-report-item-${r.filename}`}
                          className="w-full flex items-center justify-between gap-3 py-2 px-2 border-b border-[#27272A] hover:bg-[#141414] rounded text-left transition-colors">
                          <span className="text-gray-300 truncate">{r.titulo || r.periodo}</span>
                          <span className="text-amber-500 whitespace-nowrap">{r.total_km} km · baixar</span>
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              </Panel>
            )}

            <div className="bg-[#0A0A0A] border border-[#27272A] rounded-lg p-4 text-xs text-gray-500 leading-relaxed">
              <span className="text-amber-500 tracking-[0.2em] uppercase text-[10px] font-bold">// Metodologia</span>{" "}
              KM calculado pelo cruzamento com banco_de_dados.json (267 rotas): cada dia CASA → loc1 → … → CASA.
              Atividades/equipamentos detectados por keywords nos relatórios sem custo de LLM. Mapa geolocalizado
              via cache + Nominatim (OpenStreetMap). Custo de combustível configurável nos filtros.
            </div>
          </>
        )}
      </div>

      {/* MODAL DETALHE MENSAL */}
      {monthDetail && (
        <div className="fixed inset-0 backdrop-blur-sm bg-black/80 z-[2000] flex items-center justify-center p-4"
          onClick={() => setMonthDetail(null)}>
          <div onClick={(e) => e.stopPropagation()}
            className="bg-[#0A0A0A] border border-amber-500/50 rounded-lg shadow-[0_0_40px_rgba(245,158,11,0.15)] w-full max-w-3xl max-h-[90vh] overflow-auto">
            <div className="flex items-center justify-between px-6 py-4 border-b border-[#27272A] sticky top-0 bg-[#0A0A0A]">
              <span className="text-lg font-bold text-amber-500 uppercase tracking-widest">Detalhe · {monthDetail.month}</span>
              <div className="flex items-center gap-2">
                <button data-testid="share-month-button"
                  onClick={() => {
                    const m = monthDetail.month; const [y, mo] = m.split("-");
                    const last = new Date(Number(y), Number(mo), 0).getDate();
                    shareWhatsApp({ start: `${m}-01`, end: `${m}-${String(last).padStart(2, "0")}` }, m);
                  }}
                  className="inline-flex items-center gap-1.5 bg-[#25D366] text-[#052e16] hover:bg-[#22c55e] font-bold uppercase tracking-wider text-[11px] px-3 py-1.5 rounded transition-colors">
                  <WhatsappLogo size={14} weight="fill" /> Compartilhar
                </button>
                <button onClick={() => setMonthDetail(null)} data-testid="close-month-modal"
                  className="text-gray-400 hover:text-amber-500 transition-colors"><X size={20} weight="bold" /></button>
              </div>
            </div>
            <div className="p-6 space-y-5">
              <div className="grid grid-cols-3 gap-4">
                <KPI label="KM no mês" value={monthDetail.total_km} accent />
                <KPI label="Dias trabalhados" value={monthDetail.dias_trabalhados} />
                <KPI label="Média KM/dia" value={monthDetail.media_km_dia} />
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                <div>
                  <div className="text-amber-500 text-[11px] tracking-widest uppercase mb-2 font-bold">Top unidades</div>
                  <div className="space-y-1 font-mono text-xs">
                    {monthDetail.top_destinos.map((d, i) => (
                      <div key={i} className="flex justify-between border-b border-[#27272A] pb-1">
                        <span className="text-gray-300 truncate">{d.unidade}</span>
                        <span className="text-amber-500">{d.visitas}×</span>
                      </div>
                    ))}
                  </div>
                </div>
                <div>
                  <div className="text-amber-500 text-[11px] tracking-widest uppercase mb-2 font-bold">Equipamentos</div>
                  <div className="space-y-1 font-mono text-xs">
                    {monthDetail.top_equipamentos.map((e, i) => (
                      <div key={i} className="flex justify-between border-b border-[#27272A] pb-1">
                        <span className="text-gray-300 capitalize">{e.item.replace(/_/g, " ")}</span>
                        <span className="text-amber-500">{e.qtd}×</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
              <div>
                <div className="text-amber-500 text-[11px] tracking-widest uppercase mb-2 font-bold">Dias do mês</div>
                <div className="space-y-1 font-mono text-xs max-h-64 overflow-auto">
                  {monthDetail.days.map((d, i) => (
                    <div key={i} className="border-l-2 border-amber-500 pl-3 py-1">
                      <div className="flex justify-between">
                        <span className="text-amber-500">{d.date}</span>
                        <span className="text-gray-300">{d.km} km · {d.locations.length} paradas</span>
                      </div>
                      <div className="text-[10px] text-gray-500 truncate">
                        {d.locations.join(" → ") || "(sem unidades detectadas)"}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* MODAL PDF: SELEÇÃO DE CAMPOS */}
      {showPdfModal && pdfCatalog && (
        <div className="fixed inset-0 backdrop-blur-sm bg-black/80 z-[2000] flex items-center justify-center p-4"
          onClick={() => setShowPdfModal(false)}>
          <div onClick={(e) => e.stopPropagation()} data-testid="pdf-fields-modal"
            className="bg-[#0A0A0A] border border-amber-500/50 rounded-lg shadow-[0_0_40px_rgba(245,158,11,0.15)] w-full max-w-3xl max-h-[90vh] overflow-auto">
            <div className="flex items-center justify-between px-6 py-4 border-b border-[#27272A] sticky top-0 bg-[#0A0A0A]">
              <span className="text-lg font-bold text-amber-500 uppercase tracking-widest">Exportar PDF — escolha os campos</span>
              <button onClick={() => setShowPdfModal(false)} className="text-gray-400 hover:text-amber-500"><X size={20} weight="bold" /></button>
            </div>
            <div className="p-6 space-y-5">
              <FieldGroup title="Indicadores (KPIs)" items={pdfCatalog.kpis}
                selected={pdfSel.kpis} onToggle={(k) => togglePdfItem("kpis", k)}
                testidPrefix="pdf-kpi" />
              <FieldGroup title="Colunas do diário" items={pdfCatalog.columns}
                selected={pdfSel.columns} onToggle={(k) => togglePdfItem("columns", k)}
                testidPrefix="pdf-col" />
              <FieldGroup title="Seções extras" items={pdfCatalog.sections}
                selected={pdfSel.sections} onToggle={(k) => togglePdfItem("sections", k)}
                testidPrefix="pdf-sec" />
              <div className="flex flex-wrap items-center justify-between gap-2 pt-3 border-t border-[#27272A]">
                <button onClick={resetPdfSel} data-testid="pdf-reset-defaults"
                  className="border border-[#27272A] text-gray-400 hover:text-amber-500 hover:border-amber-500 font-bold uppercase tracking-wider text-xs px-4 py-2 rounded transition-colors">
                  RESTAURAR PADRÃO
                </button>
                <div className="flex gap-2">
                  <button onClick={() => setShowPdfModal(false)} data-testid="pdf-cancel"
                    className="border border-[#27272A] text-gray-400 hover:text-amber-500 hover:border-amber-500 font-bold uppercase tracking-wider text-xs px-4 py-2 rounded transition-colors">
                    CANCELAR
                  </button>
                  <button onClick={downloadCustomPdf} data-testid="pdf-download"
                    className="bg-amber-500 text-[#050505] hover:bg-amber-400 font-bold uppercase tracking-wider text-xs px-5 py-2 rounded inline-flex items-center gap-2 transition-colors">
                    <FilePdf size={14} weight="bold" /> GERAR PDF
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* MODAL COMPARTILHAR WHATSAPP (com favoritos) */}
      {showShareModal && (
        <div className="fixed inset-0 backdrop-blur-sm bg-black/80 z-[2000] flex items-center justify-center p-4"
          onClick={() => setShowShareModal(false)}>
          <div onClick={(e) => e.stopPropagation()} data-testid="share-modal"
            className="bg-[#0A0A0A] border border-amber-500/50 rounded-lg shadow-[0_0_40px_rgba(245,158,11,0.15)] w-full max-w-md">
            <div className="flex items-center justify-between px-6 py-4 border-b border-[#27272A]">
              <span className="text-lg font-bold text-amber-500 uppercase tracking-widest flex items-center gap-2">
                <WhatsappLogo size={18} weight="fill" /> Compartilhar
              </span>
              <button onClick={() => setShowShareModal(false)} className="text-gray-400 hover:text-amber-500"><X size={20} weight="bold" /></button>
            </div>
            <div className="p-6 space-y-4">
              <div>
                <label className="text-[10px] uppercase tracking-widest text-gray-500 mb-1 block">Destino (opcional)</label>
                <select data-testid="share-destination" value={shareDest}
                  onChange={(e) => setShareDest(e.target.value)}
                  className="w-full bg-[#050505] border border-[#27272A] text-gray-200 text-sm rounded px-3 py-2 focus:border-amber-500 focus:outline-none">
                  <option value="">Sem destino fixo (abrir wa.me genérico)</option>
                  {favorites.map((f) => (
                    <option key={f.id} value={f.id}>[{f.tipo}] {f.display_name}</option>
                  ))}
                </select>
                <p className="text-[10px] text-gray-600 mt-1">
                  {favorites.length === 0
                    ? "Nenhum favorito cadastrado. Acesse /whatsapp para adicionar."
                    : "Se rodando local (DESKTOP_MODE=1), o envio é automático. No painel hospedado, abrimos o wa.me com o destino escolhido."}
                </p>
              </div>
              <div className="flex justify-end gap-2">
                <button onClick={() => setShowShareModal(false)} data-testid="share-cancel"
                  className="border border-[#27272A] text-gray-400 hover:text-amber-500 hover:border-amber-500 font-bold uppercase tracking-wider text-xs px-4 py-2 rounded transition-colors">
                  CANCELAR
                </button>
                <button onClick={doShareWhatsApp} data-testid="share-confirm"
                  className="bg-[#25D366] text-[#052e16] hover:bg-[#22c55e] font-bold uppercase tracking-wider text-xs px-5 py-2 rounded inline-flex items-center gap-2 transition-colors">
                  <WhatsappLogo size={14} weight="fill" /> COMPARTILHAR
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function FieldGroup({ title, items, selected, onToggle, testidPrefix }) {
  const selSet = new Set(selected || []);
  return (
    <div>
      <div className="flex items-center justify-between mb-2">
        <span className="text-amber-500 text-[11px] tracking-widest uppercase font-bold">{title}</span>
        <span className="text-gray-600 text-[10px] font-mono">{selSet.size}/{items.length}</span>
      </div>
      <div className="grid grid-cols-2 md:grid-cols-3 gap-1.5">
        {items.map((it) => (
          <label key={it.key} data-testid={`${testidPrefix}-${it.key}`}
            className={`flex items-center gap-2 px-3 py-1.5 border rounded cursor-pointer text-xs transition-colors ${
              selSet.has(it.key)
                ? "border-amber-500/50 bg-amber-500/10 text-amber-200"
                : "border-[#27272A] text-gray-400 hover:border-amber-500/50"
            }`}>
            <input type="checkbox" className="w-3.5 h-3.5 accent-amber-500"
              checked={selSet.has(it.key)} onChange={() => onToggle(it.key)} />
            <span className="truncate">{it.label}</span>
          </label>
        ))}
      </div>
    </div>
  );
}

function Field({ label, children }) {
  return (
    <div className="flex flex-col">
      <label className="text-[10px] uppercase tracking-widest text-gray-500 mb-1">{label}</label>
      {children}
    </div>
  );
}

function ExportBtn({ icon: Icon, label, onClick, testid }) {
  return (
    <button onClick={onClick} data-testid={testid}
      className="inline-flex items-center gap-1.5 border border-amber-500/40 text-amber-500 hover:bg-amber-500/10 hover:border-amber-500 font-bold uppercase tracking-wider text-xs px-3 py-2 rounded transition-colors">
      <Icon size={14} weight="bold" /> {label}
    </button>
  );
}

function Panel({ title, right, children, className = "" }) {
  return (
    <div className={`bg-[#0A0A0A] border border-[#27272A] rounded-lg transition-all hover:border-amber-500/40 ${className}`}>
      <div className="flex items-center justify-between px-5 py-3 border-b border-[#27272A]">
        <span className="text-amber-500 text-xs uppercase tracking-[0.2em] font-bold">{title}</span>
        {right && <span className="text-gray-500 text-[11px] font-mono">{right}</span>}
      </div>
      {children}
    </div>
  );
}

function KPI({ icon: Icon, label, value, sub, accent, testid }) {
  return (
    <div data-testid={testid}
      className="bg-[#0A0A0A] border border-[#27272A] rounded-lg p-5 transition-all duration-300 hover:border-amber-500/50 hover:shadow-[0_0_20px_rgba(245,158,11,0.1)]">
      <div className="text-[10px] tracking-[0.15em] text-gray-500 uppercase flex items-center gap-2">
        {Icon && <Icon size={13} className="text-amber-500" weight="bold" />} {label}
      </div>
      <div className={`font-display text-3xl md:text-4xl font-black tracking-tighter mt-2 ${accent ? "text-amber-500" : "text-gray-50"}`}>{value}</div>
      {sub && <div className="text-gray-600 text-[10px] mt-1 font-mono">{sub}</div>}
    </div>
  );
}
