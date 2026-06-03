import React, { useEffect, useState } from "react";
import { api } from "../api";
import { Robot, Play, Lightning, ArrowRight, CheckCircle } from "@phosphor-icons/react";
import { toast } from "sonner";

const EXEMPLOS = [
  "Faz um briefing executivo do meu dia: agenda, emails, clima e top 3 manchetes",
  "Resume o que rodei essa semana em KM e quais foram as unidades mais visitadas",
  "Pega o relatório mais recente, identifica padrões e cria um quick note com insights",
  "Cota dólar, euro e bitcoin agora e converte 1000 USD pra reais",
  "Investiga: equipamentos hospitalares com maior taxa de falha em 2026",
];

export default function Agent() {
  const [goal, setGoal] = useState("");
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState(null);
  const [tools, setTools] = useState([]);

  useEffect(() => {
    api.get("/agent/tools").then(({ data }) => setTools(data || []));
  }, []);

  const run = async () => {
    if (!goal.trim()) return toast.error("Digite uma meta");
    setRunning(true); setResult(null);
    try {
      const { data } = await api.post("/agent/run", { goal });
      setResult(data);
      toast.success(`Agente concluiu ${data.steps.length} passos`);
    } catch (e) {
      toast.error("Falha no agente");
    } finally { setRunning(false); }
  };

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-end justify-between">
        <div>
          <h1 className="font-display text-3xl">Agent Mode</h1>
          <p className="text-zinc-500 text-xs tracking-widest uppercase mt-1">
            // MAVIS PLANEJA · EXECUTA · SINTETIZA · AUTÔNOMA
          </p>
        </div>
        <div className="text-amber text-[11px] tracking-widest uppercase">
          {tools.length} ferramentas
        </div>
      </div>

      <div className="panel p-4 space-y-3">
        <textarea
          data-testid="agent-goal"
          value={goal}
          onChange={(e) => setGoal(e.target.value)}
          rows={3}
          placeholder="dê uma missão complexa pra MAVIS resolver sozinha..."
          className="w-full bg-bg border border-zinc-800 focus:border-amber px-3 py-2 outline-none font-mono text-sm resize-none"
        />
        <div className="flex flex-wrap gap-2">
          {EXEMPLOS.map((e, i) => (
            <button key={i} onClick={() => setGoal(e)}
                    className="btn-ghost text-[11px] tracking-wider">
              {e.slice(0, 60)}{e.length > 60 ? "..." : ""}
            </button>
          ))}
        </div>
        <div className="flex justify-end">
          <button onClick={run} disabled={running} data-testid="agent-run"
                  className="btn-amber inline-flex items-center gap-2">
            <Robot size={16} weight="fill" /> {running ? "EXECUTANDO..." : "EXECUTAR MISSÃO"}
          </button>
        </div>
      </div>

      {running && (
        <div className="panel p-8 text-center text-amber blink-caret font-mono text-sm">
          analisando · planejando · executando ferramentas
        </div>
      )}

      {result && (
        <>
          {/* PLANO */}
          <div className="panel">
            <div className="panel-header">
              <span className="flex items-center gap-2"><Lightning size={12} className="text-amber" /> PLANO</span>
              <span className="text-zinc-500">{result.plan.length} passos</span>
            </div>
            <div className="p-4 space-y-2 font-mono text-xs">
              {result.plan.length === 0 && <div className="text-zinc-500">Sem ferramentas — respondida do conhecimento.</div>}
              {result.plan.map((p, i) => (
                <div key={i} className="flex items-start gap-3 border-l-2 border-amber pl-3">
                  <span className="text-zinc-500">#{i + 1}</span>
                  <div className="flex-1">
                    <div className="text-amber tracking-widest uppercase">{p.tool}</div>
                    {p.why && <div className="text-zinc-500 text-[11px] mt-0.5">↳ {p.why}</div>}
                    {Object.keys(p.args || {}).length > 0 && (
                      <div className="text-zinc-600 text-[11px]">args: {JSON.stringify(p.args)}</div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* EXECUÇÃO */}
          <div className="panel">
            <div className="panel-header">EXECUÇÃO</div>
            <div className="p-4 space-y-3 font-mono text-xs">
              {result.steps.map((s, i) => (
                <details key={i} data-testid={`agent-step-${i}`} className="border border-zinc-800">
                  <summary className="cursor-pointer p-2 flex items-center gap-2 hover:bg-surface2">
                    <CheckCircle size={12} weight="fill" className="text-ok" />
                    <span className="text-amber tracking-widest uppercase">{s.tool}</span>
                    <ArrowRight size={10} className="text-zinc-600" />
                    <span className="text-zinc-500">step {i + 1}</span>
                  </summary>
                  <pre className="p-3 whitespace-pre-wrap text-zinc-300 text-[11px] bg-bg border-t border-zinc-800 max-h-60 overflow-auto">
{JSON.stringify(s.output, null, 2)}
                  </pre>
                </details>
              ))}
            </div>
          </div>

          {/* SÍNTESE */}
          <div className="panel">
            <div className="panel-header">
              <span className="flex items-center gap-2"><Robot size={12} weight="fill" className="text-amber" /> SÍNTESE FINAL</span>
            </div>
            <pre data-testid="agent-answer"
                 className="p-5 whitespace-pre-wrap text-white text-sm leading-relaxed font-mono border-l-2 border-amber">
              {result.answer}
            </pre>
          </div>
        </>
      )}

      <div className="panel">
        <div className="panel-header"><span>ARSENAL DE FERRAMENTAS</span></div>
        <div className="p-4 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2 font-mono text-[11px]">
          {tools.map((t) => (
            <div key={t.name} className="border border-zinc-800 p-2">
              <div className="text-amber tracking-widest uppercase">{t.name}</div>
              <div className="text-zinc-400 mt-1">{t.desc}</div>
            </div>
          ))}
        </div>
      </div>

      <div className="panel p-4 text-[11px] text-zinc-500 leading-relaxed">
        <span className="text-amber tracking-widest uppercase">// COMO FUNCIONA</span> Gemini recebe sua meta + lista de ferramentas → gera um plano JSON em até 6 passos → MAVIS executa cada um sequencialmente → resultados são sintetizados em resposta final. Tudo automatizado, sem confirmação a cada step.
      </div>
    </div>
  );
}
