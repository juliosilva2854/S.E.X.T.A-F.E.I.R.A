import React from "react";

/**
 * Widgets utilitários do Analytics (extraídos do Analytics.jsx).
 * KPI, Panel, Field, ExportBtn e FieldGroup vivem aqui para enxugar a página
 * principal e permitir reuso em outras telas.
 */

export function KPI({ icon: Icon, label, value, sub, accent, testid }) {
  return (
    <div
      data-testid={testid}
      className="bg-[#0A0A0A] border border-[#27272A] rounded-lg p-5 transition-all duration-300 hover:border-amber-500/50 hover:shadow-[0_0_20px_rgba(245,158,11,0.1)]"
    >
      <div className="text-[10px] tracking-[0.15em] text-gray-500 uppercase flex items-center gap-2">
        {Icon && <Icon size={13} className="text-amber-500" weight="bold" />} {label}
      </div>
      <div
        className={`font-display text-3xl md:text-4xl font-black tracking-tighter mt-2 ${
          accent ? "text-amber-500" : "text-gray-50"
        }`}
      >
        {value}
      </div>
      {sub && <div className="text-gray-600 text-[10px] mt-1 font-mono">{sub}</div>}
    </div>
  );
}

export function Panel({ title, right, children, className = "" }) {
  return (
    <div
      className={`bg-[#0A0A0A] border border-[#27272A] rounded-lg transition-all hover:border-amber-500/40 ${className}`}
    >
      <div className="flex items-center justify-between px-5 py-3 border-b border-[#27272A]">
        <span className="text-amber-500 text-xs uppercase tracking-[0.2em] font-bold">{title}</span>
        {right && <span className="text-gray-500 text-[11px] font-mono">{right}</span>}
      </div>
      {children}
    </div>
  );
}

export function Field({ label, children }) {
  return (
    <div className="flex flex-col">
      <label className="text-[10px] uppercase tracking-widest text-gray-500 mb-1">{label}</label>
      {children}
    </div>
  );
}

export function ExportBtn({ icon: Icon, label, onClick, testid }) {
  return (
    <button
      onClick={onClick}
      data-testid={testid}
      className="inline-flex items-center gap-1.5 border border-amber-500/40 text-amber-500 hover:bg-amber-500/10 hover:border-amber-500 font-bold uppercase tracking-wider text-xs px-3 py-2 rounded transition-colors"
    >
      <Icon size={14} weight="bold" /> {label}
    </button>
  );
}

export function FieldGroup({ title, items, selected, onToggle, testidPrefix }) {
  const selSet = new Set(selected || []);
  return (
    <div>
      <div className="flex items-center justify-between mb-2">
        <span className="text-amber-500 text-[11px] tracking-widest uppercase font-bold">{title}</span>
        <span className="text-gray-600 text-[10px] font-mono">
          {selSet.size}/{items.length}
        </span>
      </div>
      <div className="grid grid-cols-2 md:grid-cols-3 gap-1.5">
        {items.map((it) => (
          <label
            key={it.key}
            data-testid={`${testidPrefix}-${it.key}`}
            className={`flex items-center gap-2 px-3 py-1.5 border rounded cursor-pointer text-xs transition-colors ${
              selSet.has(it.key)
                ? "border-amber-500/50 bg-amber-500/10 text-amber-200"
                : "border-[#27272A] text-gray-400 hover:border-amber-500/50"
            }`}
          >
            <input
              type="checkbox"
              className="w-3.5 h-3.5 accent-amber-500"
              checked={selSet.has(it.key)}
              onChange={() => onToggle(it.key)}
            />
            <span className="truncate">{it.label}</span>
          </label>
        ))}
      </div>
    </div>
  );
}
