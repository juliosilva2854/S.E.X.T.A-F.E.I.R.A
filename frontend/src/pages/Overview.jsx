import React, { useEffect, useState } from "react";
import { useOutletContext, Link } from "react-router-dom";
import { api } from "../api";
import {
  ChatCircle,
  MapPinLine,
  FileText,
  Brain,
  Pulse,
  Circuitry,
} from "@phosphor-icons/react";

function Stat({ label, value, accent, testid }) {
  return (
    <div
      data-testid={testid}
      className="panel p-5 flex flex-col gap-2 hover:border-amber transition-none"
    >
      <div className="text-[10px] tracking-[0.3em] text-zinc-500 uppercase">
        {label}
      </div>
      <div
        className={`font-display font-light text-5xl leading-none ${
          accent ? "text-amber" : "text-white"
        }`}
      >
        {value}
      </div>
    </div>
  );
}

export default function Overview() {
  const { status } = useOutletContext();
  const [logs, setLogs] = useState([]);
  const [recentReports, setRecentReports] = useState([]);

  useEffect(() => {
    api.get("/logs?limit=8").then(({ data }) => setLogs(data || [])).catch(() => {});
    api.get("/reports").then(({ data }) => setRecentReports((data || []).slice(0, 3))).catch(() => {});
  }, []);

  return (
    <div className="p-6 space-y-6">
      {/* HERO */}
      <div className="panel p-8 relative overflow-hidden noise">
        <div className="scanline"></div>
        <div className="flex items-start justify-between gap-6 relative">
          <div>
            <div className="text-[10px] tracking-[0.4em] text-amber uppercase mb-3">
              // CORE INITIALIZED
            </div>
            <h1 className="font-display font-light text-5xl leading-tight">
              Pronta para operar, <span className="text-amber font-bold">senhor.</span>
            </h1>
            <p className="text-zinc-400 mt-3 max-w-xl text-sm leading-relaxed">
              Cérebro neural <span className="text-amber">{status?.modelo}</span> conectado.
              Voz <span className="text-amber">{status?.voz}</span> em standby. Aguardando
              comandos do operador.
            </p>
            <div className="flex gap-3 mt-6">
              <Link to="/chat" data-testid="hero-chat-btn" className="btn-amber inline-flex items-center gap-2">
                <ChatCircle size={16} weight="fill" /> INICIAR DIÁLOGO
              </Link>
              <Link to="/routes" data-testid="hero-routes-btn" className="btn-ghost inline-flex items-center gap-2">
                <MapPinLine size={16} /> BANCO DE ROTAS
              </Link>
            </div>
          </div>
          <Circuitry size={160} className="text-amber/20 hidden md:block" weight="duotone" />
        </div>
      </div>

      {/* STATS */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Stat testid="stat-routes" label="Rotas KM" value={status?.total_rotas ?? "—"} accent />
        <Stat testid="stat-memory" label="Memórias" value={status?.total_memorias ?? "—"} />
        <Stat testid="stat-reports" label="Relatórios" value={status?.total_relatorios ?? "—"} />
        <Stat
          testid="stat-status"
          label="Cérebro"
          value={status?.gemini_configurado ? "OK" : "OFF"}
          accent={status?.gemini_configurado}
        />
      </div>

      {/* LIVE LOGS + REPORTS */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="panel lg:col-span-2">
          <div className="panel-header">
            <span className="flex items-center gap-2">
              <Pulse size={14} className="text-amber animate-pulse" />
              SYSTEM LOGS // LIVE
            </span>
            <Link to="/logs" className="text-amber hover:underline">stream &gt;</Link>
          </div>
          <div className="p-4 font-mono text-[12px] space-y-1 max-h-80 overflow-auto">
            {logs.length === 0 && (
              <div className="text-zinc-600">[ silêncio na rede... ]</div>
            )}
            {logs.map((l) => (
              <div key={l.id} className="flex gap-3">
                <span className="text-zinc-600">{(l.ts || "").slice(11, 19)}</span>
                <span
                  className={
                    l.level === "ERROR"
                      ? "text-err"
                      : l.level === "WARN"
                      ? "text-warn"
                      : "text-amber/70"
                  }
                >
                  [{l.level}]
                </span>
                <span className="text-zinc-500">{l.source}</span>
                <span className="text-white flex-1 truncate">{l.message}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="panel">
          <div className="panel-header">
            <span className="flex items-center gap-2">
              <FileText size={14} className="text-amber" /> ÚLTIMOS RELATÓRIOS
            </span>
            <Link to="/reports" className="text-amber hover:underline">tudo &gt;</Link>
          </div>
          <div className="p-4 space-y-3">
            {recentReports.length === 0 && (
              <div className="text-zinc-600 text-sm">Nenhum relatório armazenado.</div>
            )}
            {recentReports.map((r) => (
              <Link
                to="/reports"
                key={r.id}
                className="block border border-zinc-800 hover:border-amber p-3"
              >
                <div className="text-amber text-[11px] tracking-widest uppercase">
                  {r.periodo}
                </div>
                <div className="text-zinc-500 text-[10px] mt-1">{r.gerado_em}</div>
                <div className="text-zinc-300 text-xs mt-2 line-clamp-3">{r.preview}</div>
              </Link>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
