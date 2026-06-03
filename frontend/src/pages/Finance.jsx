import React, { useEffect, useState } from "react";
import { api } from "../api";
import { CurrencyDollar, Calculator, ChartLine, ArrowsClockwise } from "@phosphor-icons/react";
import { toast } from "sonner";

export default function Finance() {
  const [forex, setForex] = useState([]);
  const [crypto, setCrypto] = useState(null);
  const [loanForm, setLoanForm] = useState({ principal: 10000, annual_rate_pct: 12, months: 24 });
  const [loanRes, setLoanRes] = useState(null);
  const [compForm, setCompForm] = useState({ principal: 1000, annual_rate_pct: 12, years: 10, monthly_contribution: 200 });
  const [compRes, setCompRes] = useState(null);

  const loadForex = async () => {
    try {
      const { data } = await api.get("/finance/multi");
      setForex(data || []);
    } catch { setForex([]); }
  };
  const loadCrypto = async () => {
    try {
      const { data } = await api.get("/finance/crypto?coin=bitcoin&vs=brl");
      setCrypto(data);
    } catch { setCrypto(null); }
  };

  useEffect(() => { loadForex(); loadCrypto(); }, []);

  const calcLoan = async () => {
    try {
      const { data } = await api.post("/finance/loan", loanForm);
      setLoanRes(data);
    } catch { toast.error("Falha"); }
  };

  const calcComp = async () => {
    try {
      const { data } = await api.post("/finance/compound", compForm);
      setCompRes(data);
    } catch { toast.error("Falha"); }
  };

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-end justify-between">
        <div>
          <h1 className="font-display text-3xl">Finance</h1>
          <p className="text-zinc-500 text-xs tracking-widest uppercase mt-1">
            // COTAÇÕES · CALCULADORA FINANCEIRA
          </p>
        </div>
        <button onClick={() => { loadForex(); loadCrypto(); }} className="btn-ghost inline-flex items-center gap-2">
          <ArrowsClockwise size={14} /> ATUALIZAR
        </button>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
        {forex.map((f, i) => (
          <div key={i} className="panel p-4">
            <div className="text-[10px] tracking-widest uppercase text-zinc-500">
              {f.pair || "—"}
            </div>
            <div className="font-display text-2xl text-amber mt-1">
              {f.bid ? `R$ ${f.bid.toFixed(2)}` : f.error ? "—" : "..."}
            </div>
            {f.variation_pct !== undefined && (
              <div className={`text-[11px] mt-1 ${f.variation_pct >= 0 ? "text-ok" : "text-err"}`}>
                {f.variation_pct >= 0 ? "▲" : "▼"} {Math.abs(f.variation_pct).toFixed(2)}%
              </div>
            )}
          </div>
        ))}
        {forex.length === 0 && (
          <div className="panel p-4 col-span-5 text-zinc-600 text-xs text-center">
            Cotação indisponível agora (limite por IP). No PC do usuário funciona normalmente.
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="panel">
          <div className="panel-header"><span className="flex items-center gap-2"><Calculator size={14} /> SIMULADOR DE EMPRÉSTIMO (PRICE)</span></div>
          <div className="p-5 space-y-3">
            <NumberInput label="Valor principal (R$)" value={loanForm.principal}
                         onChange={(v) => setLoanForm({ ...loanForm, principal: v })}
                         testid="loan-principal" />
            <NumberInput label="Taxa anual (%)" value={loanForm.annual_rate_pct}
                         onChange={(v) => setLoanForm({ ...loanForm, annual_rate_pct: v })}
                         testid="loan-rate" />
            <NumberInput label="Prazo (meses)" value={loanForm.months}
                         onChange={(v) => setLoanForm({ ...loanForm, months: v })}
                         testid="loan-months" />
            <button onClick={calcLoan} className="btn-amber w-full" data-testid="loan-calc">CALCULAR</button>
            {loanRes && (
              <div className="border-t border-zinc-800 pt-3 space-y-2 text-sm font-mono">
                <KV label="Parcela mensal" value={`R$ ${loanRes.monthly_payment}`} accent />
                <KV label="Total a pagar" value={`R$ ${loanRes.total_paid}`} />
                <KV label="Juros total" value={`R$ ${loanRes.total_interest}`} />
              </div>
            )}
          </div>
        </div>

        <div className="panel">
          <div className="panel-header"><span className="flex items-center gap-2"><ChartLine size={14} /> JUROS COMPOSTOS</span></div>
          <div className="p-5 space-y-3">
            <NumberInput label="Aporte inicial (R$)" value={compForm.principal}
                         onChange={(v) => setCompForm({ ...compForm, principal: v })} testid="comp-principal" />
            <NumberInput label="Taxa anual (%)" value={compForm.annual_rate_pct}
                         onChange={(v) => setCompForm({ ...compForm, annual_rate_pct: v })} testid="comp-rate" />
            <NumberInput label="Anos" value={compForm.years}
                         onChange={(v) => setCompForm({ ...compForm, years: v })} testid="comp-years" />
            <NumberInput label="Aporte mensal (R$)" value={compForm.monthly_contribution}
                         onChange={(v) => setCompForm({ ...compForm, monthly_contribution: v })} testid="comp-monthly" />
            <button onClick={calcComp} className="btn-amber w-full" data-testid="comp-calc">SIMULAR</button>
            {compRes && (
              <div className="border-t border-zinc-800 pt-3 space-y-2 text-sm font-mono">
                <KV label="Saldo final" value={`R$ ${compRes.final_balance.toLocaleString("pt-BR")}`} accent />
                <KV label="Total aportado" value={`R$ ${compRes.total_aportado.toLocaleString("pt-BR")}`} />
                <KV label="Lucro" value={`R$ ${compRes.lucro.toLocaleString("pt-BR")}`} />
              </div>
            )}
          </div>
        </div>
      </div>

      {crypto && !crypto.error && (
        <div className="panel p-4 flex items-center gap-4">
          <CurrencyDollar size={24} className="text-amber" weight="fill" />
          <div>
            <div className="text-[10px] tracking-widest uppercase text-zinc-500">BITCOIN</div>
            <div className="font-display text-2xl text-amber">R$ {crypto.price?.toLocaleString("pt-BR")}</div>
          </div>
          {crypto.change_24h_pct != null && (
            <div className={`ml-auto text-sm ${crypto.change_24h_pct >= 0 ? "text-ok" : "text-err"}`}>
              24h: {crypto.change_24h_pct >= 0 ? "▲" : "▼"} {Math.abs(crypto.change_24h_pct).toFixed(2)}%
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function NumberInput({ label, value, onChange, testid }) {
  return (
    <div>
      <label className="text-[10px] tracking-widest uppercase text-zinc-500">{label}</label>
      <input
        data-testid={testid}
        type="number"
        value={value}
        onChange={(e) => onChange(parseFloat(e.target.value) || 0)}
        className="w-full bg-bg border border-zinc-800 focus:border-amber px-3 py-2 outline-none font-mono text-sm"
      />
    </div>
  );
}

function KV({ label, value, accent }) {
  return (
    <div className="flex justify-between">
      <span className="text-zinc-500 text-[10px] tracking-widest uppercase">{label}</span>
      <span className={accent ? "text-amber font-bold" : "text-white"}>{value}</span>
    </div>
  );
}
