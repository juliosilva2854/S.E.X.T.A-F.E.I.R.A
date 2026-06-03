import React, { useEffect, useState } from "react";
import { api } from "../api";
import { Lightning, Monitor, Cloud, Newspaper, ArrowsClockwise } from "@phosphor-icons/react";

const ICONS = {
  Sistema: Monitor, Computador: Monitor, Visão: Monitor, WhatsApp: Cloud,
  Google: Cloud, Mídia: Lightning, Informação: Newspaper, Memória: Lightning, Relatórios: Lightning,
};

export default function Skills() {
  const [skills, setSkills] = useState([]);
  const [sys, setSys] = useState(null);
  const [news, setNews] = useState([]);
  const [weather, setWeather] = useState(null);

  const loadAll = async () => {
    api.get("/skills").then(({ data }) => setSkills(data.categorias || []));
    api.get("/system/info").then(({ data }) => setSys(data)).catch(() => {});
    api.get("/news?limit=3").then(({ data }) => setNews(data || [])).catch(() => {});
    api.get("/weather").then(({ data }) => setWeather(data)).catch(() => {});
  };
  useEffect(() => { loadAll(); }, []);

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-end justify-between">
        <div>
          <h1 className="font-display text-3xl">Skills & Telemetria</h1>
          <p className="text-zinc-500 text-xs tracking-widest uppercase mt-1">
            // ARSENAL DA MAVIS
          </p>
        </div>
        <button onClick={loadAll} className="btn-ghost inline-flex items-center gap-2"
                data-testid="skills-refresh">
          <ArrowsClockwise size={14} /> ATUALIZAR
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <SkillCard label="CPU" value={sys?.cpu?.percent ? `${sys.cpu.percent.toFixed(0)}%` : "—"}
                   sub={sys?.cpu?.cores_logical ? `${sys.cpu.cores_logical} threads` : ""} />
        <SkillCard label="RAM" value={sys?.ram?.percent != null ? `${sys.ram.percent.toFixed(0)}%` : "—"}
                   sub={sys?.ram?.total_gb ? `${sys.ram.used_gb}/${sys.ram.total_gb} GB` : ""} />
        <SkillCard label="DISCO" value={sys?.disk?.percent != null ? `${sys.disk.percent}%` : "—"}
                   sub={sys?.disk?.total_gb ? `${sys.disk.used_gb}/${sys.disk.total_gb} GB` : ""} />
        <SkillCard label="CLIMA SP" value={weather?.temp_c != null ? `${weather.temp_c.toFixed(0)}°C` : "—"}
                   sub={weather ? `min ${weather.min_c?.toFixed(0)}° / max ${weather.max_c?.toFixed(0)}° · chuva ${weather.rain_prob}%` : ""} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="panel lg:col-span-2">
          <div className="panel-header">CATÁLOGO DE SKILLS</div>
          <div className="p-4 grid grid-cols-1 md:grid-cols-2 gap-4">
            {skills.map((cat) => {
              const Icon = ICONS[cat.nome] || Lightning;
              return (
                <div key={cat.nome}>
                  <div className="flex items-center gap-2 text-amber text-[11px] tracking-widest uppercase mb-2">
                    <Icon size={14} weight="fill" /> {cat.nome}
                  </div>
                  <div className="space-y-1">
                    {cat.skills.map((s) => (
                      <div key={s} data-testid={`skill-${s}`}
                           className="font-mono text-xs text-zinc-300 border-l border-zinc-800 pl-3">
                        {s}
                      </div>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        <div className="panel">
          <div className="panel-header"><span className="flex items-center gap-2"><Newspaper size={14} /> MANCHETES</span></div>
          <div className="p-4 space-y-3 font-mono text-xs">
            {news.length === 0 && <div className="text-zinc-600">—</div>}
            {news.map((n, i) => (
              <a key={i} href={n.link} target="_blank" rel="noreferrer"
                 className="block border-l-2 border-amber pl-3 hover:bg-surface2">
                <div className="text-white">{n.title}</div>
                <div className="text-[10px] text-zinc-500 mt-1">{(n.published || "").slice(0, 25)}</div>
              </a>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function SkillCard({ label, value, sub }) {
  return (
    <div className="panel p-4">
      <div className="text-[10px] tracking-widest text-zinc-500 uppercase">{label}</div>
      <div className="font-display text-4xl text-amber mt-1">{value}</div>
      <div className="text-zinc-500 text-[10px] mt-1">{sub}</div>
    </div>
  );
}
