import React, { useState } from "react";
import { api } from "../api";
import { Code, Play, Wrench, MagnifyingGlass, ArrowsClockwise, Bug, FileCode } from "@phosphor-icons/react";
import { toast } from "sonner";

const LANGS = ["python", "javascript", "typescript", "go", "rust", "java", "c++", "bash", "sql"];
const MODES = [
  { id: "generate", label: "Gerar", icon: Code, path: "/code/generate", inputs: ["prompt", "language"] },
  { id: "explain", label: "Explicar", icon: MagnifyingGlass, path: "/code/explain", inputs: ["code", "language"] },
  { id: "review", label: "Revisar", icon: Wrench, path: "/code/review", inputs: ["code", "language"] },
  { id: "refactor", label: "Refatorar", icon: ArrowsClockwise, path: "/code/refactor", inputs: ["code", "instruction", "language"] },
  { id: "convert", label: "Converter", icon: FileCode, path: "/code/convert", inputs: ["code", "language", "to_lang"] },
  { id: "debug", label: "Debug", icon: Bug, path: "/code/debug", inputs: ["code", "error", "language"] },
  { id: "execute", label: "Executar (py)", icon: Play, path: "/code/execute", inputs: ["code", "stdin"], onlyPython: true },
];

export default function CodeLab() {
  const [mode, setMode] = useState(MODES[0]);
  const [form, setForm] = useState({ language: "python", to_lang: "javascript" });
  const [out, setOut] = useState("");
  const [exec, setExec] = useState(null);
  const [loading, setLoading] = useState(false);

  const run = async () => {
    setLoading(true);
    setOut(""); setExec(null);
    try {
      const { data } = await api.post(mode.path, form);
      if (mode.id === "execute") setExec(data);
      else setOut(data.output || "(sem retorno)");
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Falha");
    } finally { setLoading(false); }
  };

  return (
    <div className="p-6 space-y-4">
      <div>
        <h1 className="font-display text-3xl">Code Lab</h1>
        <p className="text-zinc-500 text-xs tracking-widest uppercase mt-1">// GERAR · EXPLICAR · REVISAR · REFATORAR · CONVERTER · DEBUG · EXECUTAR PY</p>
      </div>

      <div className="flex flex-wrap gap-2">
        {MODES.map((m) => {
          const Icon = m.icon;
          const ativo = mode.id === m.id;
          return (
            <button
              key={m.id}
              data-testid={`mode-${m.id}`}
              onClick={() => { setMode(m); setOut(""); setExec(null); }}
              className={`btn-ghost inline-flex items-center gap-2 ${
                ativo ? "border-amber text-amber bg-surface" : ""
              }`}
            >
              <Icon size={14} /> {m.label}
            </button>
          );
        })}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="panel">
          <div className="panel-header">ENTRADA</div>
          <div className="p-4 space-y-3">
            {mode.inputs.includes("prompt") && (
              <textarea
                data-testid="code-prompt"
                placeholder="ex: função que valida CPF brasileiro com dígitos verificadores"
                value={form.prompt || ""}
                onChange={(e) => setForm({ ...form, prompt: e.target.value })}
                rows={4}
                className="w-full bg-bg border border-zinc-800 focus:border-amber px-3 py-2 outline-none font-mono text-sm resize-none"
              />
            )}
            {mode.inputs.includes("code") && (
              <textarea
                data-testid="code-input"
                placeholder="cole o código aqui..."
                value={form.code || ""}
                onChange={(e) => setForm({ ...form, code: e.target.value })}
                rows={mode.id === "execute" ? 12 : 10}
                className="w-full bg-bg border border-zinc-800 focus:border-amber px-3 py-2 outline-none font-mono text-xs resize-none"
              />
            )}
            {mode.inputs.includes("instruction") && (
              <input
                value={form.instruction || ""}
                onChange={(e) => setForm({ ...form, instruction: e.target.value })}
                placeholder="instrução de refatoração (ex: 'usar async/await')"
                className="w-full bg-bg border border-zinc-800 focus:border-amber px-3 py-2 outline-none font-mono text-sm"
              />
            )}
            {mode.inputs.includes("error") && (
              <textarea
                value={form.error || ""}
                onChange={(e) => setForm({ ...form, error: e.target.value })}
                rows={3}
                placeholder="cole a stack trace ou mensagem de erro"
                className="w-full bg-bg border border-zinc-800 focus:border-amber px-3 py-2 outline-none font-mono text-xs resize-none"
              />
            )}
            {mode.inputs.includes("stdin") && (
              <input
                value={form.stdin || ""}
                onChange={(e) => setForm({ ...form, stdin: e.target.value })}
                placeholder="stdin (opcional)"
                className="w-full bg-bg border border-zinc-800 focus:border-amber px-3 py-2 outline-none font-mono text-xs"
              />
            )}
            <div className="flex gap-2">
              {mode.inputs.includes("language") && (
                <select
                  value={form.language || "python"}
                  onChange={(e) => setForm({ ...form, language: e.target.value })}
                  disabled={mode.onlyPython}
                  className="bg-bg border border-zinc-800 focus:border-amber px-3 py-2 outline-none font-mono text-sm"
                >
                  {LANGS.map((l) => <option key={l} value={l}>{l}</option>)}
                </select>
              )}
              {mode.inputs.includes("to_lang") && (
                <select
                  value={form.to_lang || "javascript"}
                  onChange={(e) => setForm({ ...form, to_lang: e.target.value })}
                  className="bg-bg border border-zinc-800 focus:border-amber px-3 py-2 outline-none font-mono text-sm"
                >
                  {LANGS.map((l) => <option key={l} value={l}>→ {l}</option>)}
                </select>
              )}
              <button
                onClick={run}
                disabled={loading}
                data-testid="code-run-btn"
                className="btn-amber inline-flex items-center gap-2 ml-auto disabled:opacity-40"
              >
                <Play size={14} weight="fill" /> {loading ? "PROCESSANDO..." : "RODAR"}
              </button>
            </div>
          </div>
        </div>

        <div className="panel">
          <div className="panel-header">SAÍDA</div>
          <div className="p-4 font-mono text-xs">
            {loading && <div className="text-zinc-500 blink-caret">processando</div>}
            {exec && (
              <div data-testid="exec-output" className="space-y-2">
                <div className="flex gap-3 text-[11px] tracking-widest uppercase">
                  <span className={exec.returncode === 0 ? "text-ok" : "text-err"}>
                    exit: {exec.returncode}
                  </span>
                  {exec.timeout_hit && <span className="text-err">TIMEOUT</span>}
                </div>
                <div>
                  <div className="text-amber/70">stdout:</div>
                  <pre className="bg-bg border border-zinc-800 p-3 whitespace-pre-wrap text-white">{exec.stdout || "(vazio)"}</pre>
                </div>
                {exec.stderr && (
                  <div>
                    <div className="text-err/70">stderr:</div>
                    <pre className="bg-bg border border-err/30 p-3 whitespace-pre-wrap text-err">{exec.stderr}</pre>
                  </div>
                )}
              </div>
            )}
            {out && (
              <pre data-testid="code-output" className="whitespace-pre-wrap text-white border-l-2 border-amber pl-3">
                {out}
              </pre>
            )}
            {!loading && !out && !exec && <div className="text-zinc-600">Aguardando.</div>}
          </div>
        </div>
      </div>

      {mode.id === "execute" && (
        <div className="panel p-3 text-xs text-zinc-500">
          <span className="text-amber tracking-widest uppercase text-[10px]">// SANDBOX</span> Subprocess com timeout 8s, módulos perigosos bloqueados (subprocess/socket/ctypes/shutil), sem acesso ao /app.
        </div>
      )}
    </div>
  );
}
