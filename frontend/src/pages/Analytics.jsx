import React, { useEffect, useState } from "react";
import { api } from "../api";
import {
  BarChart, Bar, LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, CartesianGrid,
} from "recharts";
import {
  ChartLine, Gauge, MapPin, Wrench, Fire, GasPump, CalendarBlank, ArrowsClockwise,
} from "@phosphor-icons/react";
import { toast } from "sonner";

const AMBER = "#F59E0B";
const COLORS = ["#F59E0B", "#D97706", "#B45309", "#92400E", "#78350F", "#451A03", "#FBBF24", "#FCD34D"];

export default function Analytics() {
  const [kpis, setKpis] = useState(null);
  const [weekly, setWeekly] = useState([]);
  const [monthly, setMonthly] = useState([]);
  const [daily, setDaily] = useState([]);
  const [heatmap, setHeatmap] = useState([]);
  const [activities, setActivities] = useState([]);
  const [fuelCost, setFuelCost] = useState(5.89);
  const [kmPerLiter, setKmPerLiter] = useState(10);
  const [loading, setLoading] = useState(false);
  const [monthDetail, setMonthDetail] = useState(null);

  const loadAll = async () => {
    setLoading(true);
    try {
      const [k, w, m, d, h, a] = await Promise.all([
        api.get(`/analytics/kpis?fuel_cost=${fuelCost}&km_per_liter=${kmPerLiter}`),
        api.get("/analytics/weekly?weeks=12"),
        api.get("/analytics/monthly?months=12"),
        api.get("/analytics/daily?days=30"),
        api.get("/analytics/heatmap"),
        api.get("/analytics/activities"),
      ]);
      setKpis(k.data); setWeekly(w.data); setMonthly(m.data);
      setDaily(d.data); setHeatmap(h.data); setActivities(a.data);
    } catch (e) {
      toast.error("Falha ao carregar analytics");
    } finally { setLoading(false); }
  };

  useEffect(() => { loadAll(); /* eslint-disable-next-line */ }, []);

  const openMonth = async (mk) => {
    try {
      const { data } = await api.get(`/analytics/month/${mk}`);
      setMonthDetail(data);
    } catch { toast.error("Sem dados para o mês"); }
  };

  const maxHeat = Math.max(1, ...heatmap.map((h) => h.km));

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-end justify-between flex-wrap gap-3">
        <div>
          <h1 className="font-display text-3xl">Analytics Dashboard</h1>
          <p className="text-zinc-500 text-xs tracking-widest uppercase mt-1">
            // KM · DESTINOS · COMBUSTÍVEL · MAPA DE CALOR · MENSAL
          </p>
        </div>
        <div className="flex items-end gap-2">
          <div>
            <label className="text-[10px] tracking-widest uppercase text-zinc-500">R$/L</label>
            <input data-testid="fuel-cost" type="number" step="0.01" value={fuelCost}
                   onChange={(e) => setFuelCost(parseFloat(e.target.value) || 0)}
                   className="w-24 bg-bg border border-zinc-800 focus:border-amber px-2 py-1.5 font-mono text-sm" />
          </div>
          <div>
            <label className="text-[10px] tracking-widest uppercase text-zinc-500">km/L</label>
            <input data-testid="kmpl" type="number" step="0.5" value={kmPerLiter}
                   onChange={(e) => setKmPerLiter(parseFloat(e.target.value) || 1)}
                   className="w-20 bg-bg border border-zinc-800 focus:border-amber px-2 py-1.5 font-mono text-sm" />
          </div>
          <button onClick={loadAll} disabled={loading}
                  className="btn-amber inline-flex items-center gap-2" data-testid="analytics-refresh">
            <ArrowsClockwise size={14} className={loading ? "animate-spin" : ""} /> ATUALIZAR
          </button>
        </div>
      </div>

      {!kpis && <div className="panel p-8 text-center text-zinc-500 blink-caret">carregando dados</div>}

      {kpis && (
        <>
          {/* KPI CARDS */}
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
            <KPI testid="kpi-km" icon={Gauge} label="Total KM" value={kpis.total_km} accent />
            <KPI testid="kpi-dias" icon={CalendarBlank} label="Dias úteis" value={kpis.total_dias} />
            <KPI icon={MapPin} label="Média KM/dia" value={kpis.media_km_dia} />
            <KPI icon={ChartLine} label="Média KM/semana" value={kpis.media_km_semana} />
            <KPI icon={GasPump} label="Litros" value={kpis.litros_estimados} sub={`${kmPerLiter} km/L`} />
            <KPI testid="kpi-custo" icon={Fire} label="Combustível R$" value={kpis.custo_combustivel.toLocaleString("pt-BR")} accent />
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <KPI label="Preventivas" value={kpis.total_preventivas} />
            <KPI label="Atendimentos técnicos" value={kpis.total_atendimentos} />
            <KPI label="Entregas insumos" value={kpis.total_entregas_insumos} />
            <KPI label="Trocas equipamentos" value={kpis.total_trocas_equipamentos} />
          </div>

          {/* CHART: KM POR SEMANA + ATIVIDADES */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            <div className="panel lg:col-span-2">
              <div className="panel-header"><span>KM POR SEMANA (últimas 12)</span></div>
              <div className="p-4" data-testid="chart-weekly">
                <ResponsiveContainer width="100%" height={260}>
                  <BarChart data={weekly}>
                    <CartesianGrid stroke="#27272a" strokeDasharray="3 3" />
                    <XAxis dataKey="semana" stroke="#71717a" style={{ fontSize: 10 }} />
                    <YAxis stroke="#71717a" style={{ fontSize: 10 }} />
                    <Tooltip contentStyle={{ background: "#0a0a0a", border: "1px solid #27272a", borderRadius: 0, fontFamily: "JetBrains Mono" }} />
                    <Bar dataKey="km" fill={AMBER} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="panel">
              <div className="panel-header"><span>TIPOS DE ATIVIDADE</span></div>
              <div className="p-4" data-testid="chart-activities">
                <ResponsiveContainer width="100%" height={260}>
                  <PieChart>
                    <Pie data={activities} dataKey="qtd" nameKey="tipo" cx="50%" cy="50%"
                         innerRadius={45} outerRadius={90} stroke="#0a0a0a">
                      {activities.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                    </Pie>
                    <Tooltip contentStyle={{ background: "#0a0a0a", border: "1px solid #27272a", borderRadius: 0 }} />
                  </PieChart>
                </ResponsiveContainer>
                <div className="space-y-1 mt-2 font-mono text-[11px]">
                  {activities.map((a, i) => (
                    <div key={i} className="flex justify-between border-b border-zinc-900 pb-1">
                      <span className="flex items-center gap-2 text-zinc-300">
                        <span className="w-2 h-2 inline-block" style={{ background: COLORS[i % COLORS.length] }}></span>
                        {a.tipo}
                      </span>
                      <span className="text-amber">{a.qtd}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* CHART: KM POR MÊS */}
          <div className="panel">
            <div className="panel-header"><span>RESUMO MENSAL</span><span className="text-zinc-500">{monthly.length} {monthly.length === 1 ? "mês" : "meses"}</span></div>
            <div className="p-4" data-testid="chart-monthly">
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={monthly}>
                  <CartesianGrid stroke="#27272a" strokeDasharray="3 3" />
                  <XAxis dataKey="mes" stroke="#71717a" style={{ fontSize: 10 }} />
                  <YAxis stroke="#71717a" style={{ fontSize: 10 }} />
                  <Tooltip contentStyle={{ background: "#0a0a0a", border: "1px solid #27272a", borderRadius: 0 }} />
                  <Bar dataKey="km" fill={AMBER} />
                </BarChart>
              </ResponsiveContainer>
            </div>
            <div className="border-t border-zinc-800 p-4 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {monthly.map((m) => (
                <button key={m.mes} onClick={() => openMonth(m.mes)}
                        data-testid={`month-${m.mes}`}
                        className="border border-zinc-800 hover:border-amber p-3 text-left font-mono text-xs space-y-1">
                  <div className="flex justify-between">
                    <span className="text-amber tracking-widest uppercase">{m.mes}</span>
                    <span className="text-amber font-bold">{m.km} km</span>
                  </div>
                  <div className="text-zinc-500 grid grid-cols-2 gap-1">
                    <span>📅 {m.dias_uteis} dias</span>
                    <span>📍 {m.visitas} visitas</span>
                    <span>🛠 {m.preventivas} prev.</span>
                    <span>🚨 {m.atendimentos} atend.</span>
                  </div>
                  {m.top3_destinos?.length > 0 && (
                    <div className="text-[10px] text-zinc-500 border-t border-zinc-900 pt-1">
                      Top: {m.top3_destinos.map((d) => d.unidade.split(" ").slice(0, 3).join(" ")).join(" · ")}
                    </div>
                  )}
                </button>
              ))}
            </div>
          </div>

          {/* HEATMAP DIAS DA SEMANA + RANKINGS */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            <div className="panel">
              <div className="panel-header"><span>MAPA DE CALOR · DIA DA SEMANA</span></div>
              <div className="p-4 space-y-2" data-testid="heatmap">
                {heatmap.map((h) => {
                  const intensity = h.km / maxHeat;
                  return (
                    <div key={h.dia} className="flex items-center gap-2 font-mono text-xs">
                      <span className="w-8 text-zinc-500">{h.dia}</span>
                      <div className="flex-1 h-6 border border-zinc-800 relative">
                        <div className="h-full bg-amber/80"
                             style={{ width: `${intensity * 100}%` }}></div>
                        <span className="absolute inset-0 flex items-center px-2 text-white mix-blend-difference">
                          {h.km} km · {h.dias}d
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            <div className="panel">
              <div className="panel-header"><span>TOP DESTINOS</span></div>
              <div className="p-4 space-y-2 font-mono text-xs">
                {kpis.top_destinos.slice(0, 10).map((d, i) => (
                  <div key={i} className="flex items-center gap-3" data-testid={`top-destino-${i}`}>
                    <span className="text-amber w-6">#{i + 1}</span>
                    <span className="flex-1 text-zinc-300 truncate">{d.unidade}</span>
                    <span className="text-amber font-bold">{d.visitas}×</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="panel">
              <div className="panel-header"><span><Wrench size={12} className="inline mr-1" /> TOP EQUIPAMENTOS</span></div>
              <div className="p-4 space-y-2 font-mono text-xs">
                {kpis.top_equipamentos.map((e, i) => (
                  <div key={i} className="flex items-center gap-3">
                    <span className="text-amber w-6">#{i + 1}</span>
                    <span className="flex-1 text-zinc-300 capitalize">{e.item.replace("_", " ")}</span>
                    <span className="text-amber font-bold">{e.qtd}×</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* KM DIÁRIO */}
          <div className="panel">
            <div className="panel-header"><span>KM DIÁRIO (últimos 30 dias com registro)</span></div>
            <div className="p-4" data-testid="chart-daily">
              <ResponsiveContainer width="100%" height={220}>
                <LineChart data={daily}>
                  <CartesianGrid stroke="#27272a" strokeDasharray="3 3" />
                  <XAxis dataKey="date" stroke="#71717a" style={{ fontSize: 10 }} />
                  <YAxis stroke="#71717a" style={{ fontSize: 10 }} />
                  <Tooltip contentStyle={{ background: "#0a0a0a", border: "1px solid #27272a", borderRadius: 0 }} />
                  <Line type="monotone" dataKey="km" stroke={AMBER} strokeWidth={2}
                        dot={{ fill: AMBER, r: 3 }} activeDot={{ r: 5 }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="panel p-3 text-xs text-zinc-500">
            <span className="text-amber tracking-widest uppercase text-[10px]">// METODOLOGIA</span> KM calculado pelo cruzamento com banco_de_dados.json (267 rotas). Cada dia: CASA → loc1 → loc2 → ... → CASA. Atividades/equipamentos detectados por keywords nos relatórios sem custo de LLM. Custo combustível configurável acima.
          </div>
        </>
      )}

      {/* MODAL DETALHE MENSAL */}
      {monthDetail && (
        <div className="fixed inset-0 bg-black/90 z-50 flex items-center justify-center p-6">
          <div className="panel w-full max-w-4xl max-h-[90vh] overflow-auto">
            <div className="panel-header">
              <span>DETALHE: {monthDetail.month}</span>
              <button onClick={() => setMonthDetail(null)} className="text-zinc-500 hover:text-amber">×</button>
            </div>
            <div className="p-5 space-y-4">
              <div className="grid grid-cols-3 gap-3 text-center">
                <KPI label="KM no mês" value={monthDetail.total_km} accent />
                <KPI label="Dias trabalhados" value={monthDetail.dias_trabalhados} />
                <KPI label="Média KM/dia" value={monthDetail.media_km_dia} />
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <div className="text-amber text-[11px] tracking-widest uppercase mb-2">TOP UNIDADES</div>
                  <div className="space-y-1 font-mono text-xs">
                    {monthDetail.top_destinos.map((d, i) => (
                      <div key={i} className="flex justify-between border-b border-zinc-900 pb-1">
                        <span className="text-zinc-300 truncate">{d.unidade}</span>
                        <span className="text-amber">{d.visitas}×</span>
                      </div>
                    ))}
                  </div>
                </div>
                <div>
                  <div className="text-amber text-[11px] tracking-widest uppercase mb-2">EQUIPAMENTOS</div>
                  <div className="space-y-1 font-mono text-xs">
                    {monthDetail.top_equipamentos.map((e, i) => (
                      <div key={i} className="flex justify-between border-b border-zinc-900 pb-1">
                        <span className="text-zinc-300 capitalize">{e.item.replace("_", " ")}</span>
                        <span className="text-amber">{e.qtd}×</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
              <div>
                <div className="text-amber text-[11px] tracking-widest uppercase mb-2">DIAS DO MÊS</div>
                <div className="space-y-1 font-mono text-xs max-h-64 overflow-auto">
                  {monthDetail.days.map((d, i) => (
                    <div key={i} className="border-l-2 border-amber pl-2 py-1">
                      <div className="flex justify-between">
                        <span className="text-amber">{d.date}</span>
                        <span className="text-zinc-300">{d.km} km · {d.locations.length} paradas</span>
                      </div>
                      <div className="text-[10px] text-zinc-500 truncate">
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
    </div>
  );
}

function KPI({ icon: Icon, label, value, sub, accent, testid }) {
  return (
    <div data-testid={testid} className="panel p-4">
      <div className="text-[10px] tracking-widest text-zinc-500 uppercase flex items-center gap-2">
        {Icon && <Icon size={12} className="text-amber" />} {label}
      </div>
      <div className={`font-display text-3xl mt-1 ${accent ? "text-amber" : "text-white"}`}>{value}</div>
      {sub && <div className="text-zinc-500 text-[10px] mt-0.5">{sub}</div>}
    </div>
  );
}
