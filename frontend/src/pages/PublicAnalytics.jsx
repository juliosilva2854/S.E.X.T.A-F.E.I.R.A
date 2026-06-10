import React, { useEffect, useRef, useState, useCallback } from "react";
import { useSearchParams } from "react-router-dom";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import "leaflet.heat";
import { api, API } from "../api";
import {
  BarChart, Bar, LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, CartesianGrid,
} from "recharts";
import {
  MapPin, ArrowsClockwise, FileCsv, FileXls, FilePdf, FunnelSimple, X, Lock, Eye,
} from "@phosphor-icons/react";
import { KPI, Panel, Field, ExportBtn } from "../components/analytics/widgets";
import KpiGrid from "../components/analytics/KpiGrid";

const AMBER = "#F59E0B";
const COLORS = ["#F59E0B", "#D97706", "#B45309", "#92400E", "#78350F", "#FBBF24", "#FCD34D", "#FEF3C7"];
const SP_CENTER = [-23.5505, -46.6333];
const chartTooltip = {
  backgroundColor: "#0A0A0A", border: "1px solid #F59E0B", borderRadius: "4px",
  color: "#F3F4F6", fontFamily: "JetBrains Mono", fontSize: 12,
};

export default function PublicAnalytics() {
  const [params] = useSearchParams();
  const shareId = params.get("s") || "";

  const [token, setToken] = useState(params.get("t") || "");
  const [tokenInput, setTokenInput] = useState("");
  const [authed, setAuthed] = useState(false);
  const [authError, setAuthError] = useState("");
  const [authBusy, setAuthBusy] = useState(false);
  const [label, setLabel] = useState("");

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

  const [start, setStart] = useState("");
  const [end, setEnd] = useState("");
  const [unidade, setUnidade] = useState("");
  const [fuelCost, setFuelCost] = useState(5.89);
  const [kmPerLiter, setKmPerLiter] = useState(10);

  const mapInstance = useRef(null);
  const heatRef = useRef(null);
  const markersRef = useRef(null);

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

  const qs = useCallback((extra = {}) => {
    const p = new URLSearchParams();
    p.set("s", shareId);
    p.set("t", token);
    if (start) p.set("start", start);
    if (end) p.set("end", end);
    if (unidade) p.set("unidade", unidade);
    Object.entries(extra).forEach(([k, v]) => p.set(k, v));
    return p.toString();
  }, [shareId, token, start, end, unidade]);

  const loadAll = useCallback(async (tok = token) => {
    setLoading(true);
    try {
      const p = new URLSearchParams();
      p.set("s", shareId); p.set("t", tok);
      if (start) p.set("start", start);
      if (end) p.set("end", end);
      if (unidade) p.set("unidade", unidade);
      p.set("fuel_cost", fuelCost); p.set("km_per_liter", kmPerLiter);
      const { data } = await api.get(`/public/analytics/all?${p.toString()}`);
      setKpis(data.kpis); setWeekly(data.weekly); setDaily(data.daily);
      setHeatmap(data.heatmap); setActivities(data.activities);
      setMonthly(data.monthly); setUnidades(data.unidades); setMapData(data.map_data);
    } catch (e) {
      if (e?.response?.status === 401 || e?.response?.status === 403 || e?.response?.status === 404) {
        setAuthed(false);
        setAuthError(e?.response?.data?.detail || "Acesso negado");
      }
    } finally {
      setLoading(false);
    }
  }, [shareId, token, start, end, unidade, fuelCost, kmPerLiter]);

  const tryAuth = async (tok) => {
    if (!shareId) { setAuthError("Link inválido (sem identificador)."); return; }
    if (!tok) { setAuthError("Informe o token de acesso."); return; }
    setAuthBusy(true); setAuthError("");
    try {
      const { data } = await api.get(`/public/validate?s=${encodeURIComponent(shareId)}&t=${encodeURIComponent(tok)}`);
      setToken(tok); setLabel(data.label || ""); setAuthed(true);
      await loadAll(tok);
    } catch (e) {
      setAuthed(false);
      setAuthError(e?.response?.data?.detail || "Acesso negado");
    } finally {
      setAuthBusy(false);
    }
  };

  // tentativa inicial automática (token na URL)
  useEffect(() => {
    if (shareId && token) tryAuth(token);
    else if (!shareId) setAuthError("Link inválido (sem identificador).");
    // eslint-disable-next-line
  }, []);

  // heat map render
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
    try { const { data } = await api.get(`/public/analytics/month/${mk}?${qs()}`); setMonthDetail(data); }
    catch { /* sem dados */ }
  };

  const exportData = (format) => {
    const url = `${API}/public/analytics/export?${qs({ format, fuel_cost: fuelCost, km_per_liter: kmPerLiter })}`;
    const a = document.createElement("a");
    a.href = url; a.rel = "noopener";
    document.body.appendChild(a); a.click(); a.remove();
  };

  const clearFilters = () => { setStart(""); setEnd(""); setUnidade(""); setTimeout(() => loadAll(), 0); };
  const maxHeat = Math.max(1, ...heatmap.map((h) => h.km));

  // ---------- TELA DE TOKEN (não autenticado) ----------
  if (!authed) {
    return (
      <div className="min-h-screen bg-[#050505] noise flex items-center justify-center p-4">
        <div data-testid="public-token-gate"
          className="w-full max-w-md bg-[#0A0A0A] border border-[#27272A] rounded-lg p-8">
          <div className="flex items-center gap-3 mb-1">
            <Lock size={22} weight="fill" className="text-amber-500" />
            <h1 className="font-display text-2xl font-bold text-gray-50">Analytics · MAVIS</h1>
          </div>
          <p className="text-amber-500 text-[10px] tracking-[0.2em] uppercase font-bold mb-6">
            // acesso restrito por token
          </p>
          <label className="text-[10px] uppercase tracking-widest text-gray-500 mb-1 block">Token de acesso</label>
          <input
            data-testid="public-token-input"
            type="text"
            value={tokenInput}
            onChange={(e) => setTokenInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && tryAuth(tokenInput.trim())}
            placeholder="cole o token compartilhado"
            className="w-full bg-[#050505] border border-[#27272A] text-gray-200 text-sm rounded px-3 py-2.5 focus:border-amber-500 focus:outline-none transition-colors"
          />
          {authError && (
            <p data-testid="public-auth-error" className="text-red-400 text-xs mt-3 font-mono">{authError}</p>
          )}
          <button
            data-testid="public-token-submit"
            onClick={() => tryAuth(tokenInput.trim())}
            disabled={authBusy}
            className="mt-5 w-full inline-flex items-center justify-center gap-2 bg-amber-500 text-[#050505] hover:bg-amber-400 disabled:opacity-50 font-bold uppercase tracking-wider text-xs px-4 py-2.5 rounded transition-colors">
            <Eye size={15} weight="bold" /> {authBusy ? "Verificando…" : "Visualizar Analytics"}
          </button>
          <p className="text-gray-600 text-[10px] mt-5 leading-relaxed">
            Página somente leitura. Após várias tentativas inválidas o link expira por segurança.
          </p>
        </div>
      </div>
    );
  }

  // ---------- DASHBOARD PÚBLICO (somente leitura) ----------
  return (
    <div className="min-h-screen bg-[#050505] noise relative" data-testid="public-analytics">
      <div className="backdrop-blur-xl bg-[#050505]/80 border-b border-[#27272A] sticky top-0 z-[1000]">
        <div className="max-w-[1800px] mx-auto px-4 md:px-8 py-4 flex items-center justify-between flex-wrap gap-3">
          <div>
            <h1 className="font-display text-2xl md:text-3xl font-bold tracking-tight text-gray-50 flex items-center gap-2">
              Analytics
              <span className="text-[10px] uppercase tracking-widest text-emerald-400 border border-emerald-500/40 rounded px-2 py-0.5 flex items-center gap-1">
                <Eye size={11} weight="fill" /> somente leitura
              </span>
            </h1>
            <p className="text-amber-500 text-[10px] md:text-xs tracking-[0.2em] uppercase font-bold mt-0.5">
              // {label || "KM · DESTINOS · COMBUSTÍVEL · MAPA DE CALOR"}
            </p>
          </div>
          <div className="flex items-center gap-2 flex-wrap">
            <ExportBtn icon={FileCsv} label="CSV" onClick={() => exportData("csv")} testid="public-export-csv" />
            <ExportBtn icon={FileXls} label="EXCEL" onClick={() => exportData("xlsx")} testid="public-export-xlsx" />
            <ExportBtn icon={FilePdf} label="PDF" onClick={() => exportData("pdf")} testid="public-export-pdf" />
            <button onClick={() => loadAll()} disabled={loading} data-testid="public-refresh"
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
            <input data-testid="public-filter-start" type="date" value={start} onChange={(e) => setStart(e.target.value)}
              className="bg-[#050505] border border-[#27272A] text-gray-200 text-sm rounded px-3 py-1.5 focus:border-amber-500 focus:outline-none" />
          </Field>
          <Field label="Data fim">
            <input data-testid="public-filter-end" type="date" value={end} onChange={(e) => setEnd(e.target.value)}
              className="bg-[#050505] border border-[#27272A] text-gray-200 text-sm rounded px-3 py-1.5 focus:border-amber-500 focus:outline-none" />
          </Field>
          <Field label="Unidade">
            <select data-testid="public-filter-unidade" value={unidade} onChange={(e) => setUnidade(e.target.value)}
              className="bg-[#050505] border border-[#27272A] text-gray-200 text-sm rounded px-3 py-1.5 focus:border-amber-500 focus:outline-none min-w-[180px] max-w-[240px]">
              <option value="">Todas</option>
              {unidades.map((u) => <option key={u} value={u}>{u}</option>)}
            </select>
          </Field>
          <Field label="R$ / Litro">
            <input data-testid="public-fuel-cost" type="number" step="0.01" value={fuelCost}
              onChange={(e) => setFuelCost(parseFloat(e.target.value) || 0)}
              className="w-24 bg-[#050505] border border-[#27272A] text-gray-200 text-sm rounded px-3 py-1.5 focus:border-amber-500 focus:outline-none" />
          </Field>
          <Field label="KM / Litro">
            <input data-testid="public-kmpl" type="number" step="0.5" value={kmPerLiter}
              onChange={(e) => setKmPerLiter(parseFloat(e.target.value) || 1)}
              className="w-20 bg-[#050505] border border-[#27272A] text-gray-200 text-sm rounded px-3 py-1.5 focus:border-amber-500 focus:outline-none" />
          </Field>
          <button onClick={() => loadAll()} data-testid="public-apply-filters"
            className="bg-amber-500 text-[#050505] hover:bg-amber-400 font-bold uppercase tracking-wider text-xs px-5 py-2 rounded transition-colors">
            Aplicar
          </button>
          <button onClick={clearFilters} data-testid="public-clear-filters"
            className="border border-[#27272A] text-gray-400 hover:border-amber-500 hover:text-amber-500 font-bold uppercase tracking-wider text-xs px-4 py-2 rounded transition-colors">
            Limpar
          </button>
        </div>

        {!kpis && <div className="p-12 text-center text-gray-500">carregando dados…</div>}

        {kpis && (
          <>
            <KpiGrid kpis={kpis} kmPerLiter={kmPerLiter} />

            {/* MAPA */}
            <div className="bg-[#0A0A0A] border border-[#27272A] rounded-lg overflow-hidden">
              <div className="flex items-center justify-between px-5 py-3 border-b border-[#27272A]">
                <span className="text-amber-500 text-xs uppercase tracking-[0.2em] font-bold flex items-center gap-2">
                  <MapPin size={14} weight="fill" /> Mapa de Calor · Unidades visitadas
                </span>
                <span className="text-gray-500 text-[11px] font-mono">
                  {mapData?.total_unidades || 0} unidades · {mapData?.total_visitas || 0} visitas
                </span>
              </div>
              <div ref={setMapEl} data-testid="public-heatmap-geo" className="h-[440px] w-full z-0" />
            </div>

            {/* WEEKLY + ACTIVITIES */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <Panel title="KM por semana (últimas 12)" className="lg:col-span-2">
                <div className="p-5">
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
                <div className="p-5">
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
              <div className="p-5">
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
                  <button key={m.mes} onClick={() => openMonth(m.mes)} data-testid={`public-month-${m.mes}`}
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
                <div className="p-5 space-y-2.5">
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
                  {(kpis.top_destinos || []).slice(0, 10).map((d, i) => (
                    <div key={i} className="flex items-center gap-3 py-2.5 px-2 border-b border-[#27272A] last:border-0 hover:bg-[#141414] rounded transition-colors">
                      <span className="text-[10px] text-amber-500 bg-amber-500/10 px-2 py-1 rounded font-bold">#{i + 1}</span>
                      <span className="flex-1 text-gray-300 truncate">{d.unidade}</span>
                      <span className="text-amber-500 font-bold">{d.visitas}×</span>
                    </div>
                  ))}
                </div>
              </Panel>
              <Panel title="Top equipamentos">
                <div className="p-3 font-mono text-xs">
                  {(kpis.top_equipamentos || []).map((e, i) => (
                    <div key={i} className="flex items-center gap-3 py-2.5 px-2 border-b border-[#27272A] last:border-0 hover:bg-[#141414] rounded transition-colors">
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
              <div className="p-5">
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
          </>
        )}
      </div>

      {/* MODAL DETALHE MENSAL (read-only) */}
      {monthDetail && (
        <div className="fixed inset-0 backdrop-blur-sm bg-black/80 z-[2000] flex items-center justify-center p-4"
          onClick={() => setMonthDetail(null)}>
          <div onClick={(e) => e.stopPropagation()}
            className="bg-[#0A0A0A] border border-amber-500/50 rounded-lg w-full max-w-3xl max-h-[90vh] overflow-auto">
            <div className="flex items-center justify-between px-6 py-4 border-b border-[#27272A] sticky top-0 bg-[#0A0A0A]">
              <span className="text-lg font-bold text-amber-500 uppercase tracking-widest">Detalhe · {monthDetail.month}</span>
              <button onClick={() => setMonthDetail(null)} className="text-gray-400 hover:text-amber-500"><X size={20} weight="bold" /></button>
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
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
