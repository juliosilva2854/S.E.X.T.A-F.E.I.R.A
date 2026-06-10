import React from "react";
import {
  Gauge, CalendarBlank, Path, ChartLine, GasPump, Fire,
  Wrench, Truck, ArrowsClockwise,
} from "@phosphor-icons/react";
import { KPI } from "./widgets";

/**
 * Grade de KPIs do Analytics (extraída do Analytics.jsx).
 * 2 linhas:
 *  - linha 1: KM totais, dias úteis, médias, litros, custo
 *  - linha 2: preventivas, atendimentos, entregas, trocas
 */
export default function KpiGrid({ kpis, kmPerLiter }) {
  if (!kpis) return null;

  return (
    <>
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        <KPI testid="kpi-total-km" icon={Gauge} label="Total KM" value={kpis.total_km} accent />
        <KPI testid="kpi-dias" icon={CalendarBlank} label="Dias úteis" value={kpis.total_dias} />
        <KPI icon={Path} label="Média KM/dia" value={kpis.media_km_dia} />
        <KPI icon={ChartLine} label="Média KM/semana" value={kpis.media_km_semana} />
        <KPI icon={GasPump} label="Litros" value={kpis.litros_estimados} sub={`${kmPerLiter} km/L`} />
        <KPI
          testid="kpi-custo"
          icon={Fire}
          label="Combustível R$"
          value={(kpis.custo_combustivel || 0).toLocaleString("pt-BR", {
            minimumFractionDigits: 2,
          })}
          accent
        />
      </div>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <KPI icon={Wrench} label="Preventivas" value={kpis.total_preventivas} />
        <KPI icon={Wrench} label="Atendimentos téc." value={kpis.total_atendimentos} />
        <KPI icon={Truck} label="Entregas insumos" value={kpis.total_entregas_insumos} />
        <KPI icon={ArrowsClockwise} label="Trocas equip." value={kpis.total_trocas_equipamentos} />
      </div>
    </>
  );
}
