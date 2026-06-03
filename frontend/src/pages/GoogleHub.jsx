import React, { useEffect, useState } from "react";
import { api } from "../api";
import { Calendar, Envelope, FolderOpen, CheckCircle, XCircle, ArrowsClockwise } from "@phosphor-icons/react";
import { toast } from "sonner";

export default function GoogleHub() {
  const [status, setStatus] = useState(null);
  const [today, setToday] = useState([]);
  const [unread, setUnread] = useState([]);
  const [recent, setRecent] = useState([]);
  const [loading, setLoading] = useState(false);

  const reload = async () => {
    setLoading(true);
    try {
      const s = await api.get("/google/status").then((r) => r.data);
      setStatus(s);
      if (s.ready) {
        const [c, m, d] = await Promise.allSettled([
          api.get("/google/calendar/today"),
          api.get("/google/gmail/unread?max_results=10"),
          api.get("/google/drive/recent?limit=10"),
        ]);
        if (c.status === "fulfilled") setToday(c.value.data); else setToday([]);
        if (m.status === "fulfilled") setUnread(m.value.data); else setUnread([]);
        if (d.status === "fulfilled") setRecent(d.value.data); else setRecent([]);
      }
    } catch (e) {
      toast.error("Falha ao consultar Google");
    } finally { setLoading(false); }
  };

  useEffect(() => { reload(); }, []);

  if (!status) return <div className="p-6 text-zinc-500 blink-caret">consultando</div>;

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-end justify-between">
        <div>
          <h1 className="font-display text-3xl">Google Hub</h1>
          <p className="text-zinc-500 text-xs tracking-widest uppercase mt-1">
            // CALENDAR · GMAIL · DRIVE
          </p>
        </div>
        <button onClick={reload} className="btn-ghost inline-flex items-center gap-2"
                data-testid="google-refresh">
          <ArrowsClockwise size={14} className={loading ? "animate-spin" : ""} /> ATUALIZAR
        </button>
      </div>

      <div className="panel">
        <div className="panel-header">STATUS DA CONEXÃO</div>
        <div className="p-5 grid grid-cols-1 md:grid-cols-3 gap-4 text-sm font-mono">
          <Pill label="credenciais.json" ok={status.has_credenciais_json} />
          <Pill label="token autorizado" ok={status.has_token} />
          <Pill label="pronto para usar" ok={status.ready} />
        </div>
        {!status.ready && (
          <div className="border-t border-zinc-800 p-5 text-xs leading-relaxed text-zinc-400">
            <div className="text-amber tracking-widest uppercase text-[11px] mb-2">// COMO ATIVAR</div>
            <ol className="list-decimal pl-5 space-y-1">
              <li>Acesse <span className="text-amber">console.cloud.google.com</span> e crie/use um projeto.</li>
              <li>Habilite as APIs: <span className="text-white">Google Calendar API</span>, <span className="text-white">Gmail API</span>, <span className="text-white">Google Drive API</span>, <span className="text-white">Google Sheets API</span>.</li>
              <li>Em <b>OAuth consent screen</b>, configure External, adicione seu email como Test user.</li>
              <li>Em <b>Credenciais &gt; Criar &gt; OAuth client ID &gt; Desktop App</b>, baixe o JSON e salve como <span className="text-amber">{status.credenciais_path}</span>.</li>
              <li>Rode o app desktop (<span className="text-white">sexta-feira.py</span>) ou execute uma chamada — abrirá navegador pedindo consentimento. Pronto.</li>
            </ol>
            <div className="mt-3">Veja <span className="text-amber">README_MAVIS.md</span> para o passo-a-passo completo.</div>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="panel">
          <div className="panel-header"><span className="flex items-center gap-2"><Calendar size={14} /> AGENDA DE HOJE</span><span className="text-zinc-500">{today.length}</span></div>
          <div className="p-4 space-y-2 font-mono text-sm">
            {!status.ready && <div className="text-zinc-600 text-xs">Não conectado.</div>}
            {status.ready && today.length === 0 && <div className="text-zinc-600 text-xs">Agenda limpa hoje.</div>}
            {today.map((e) => (
              <div key={e.id} className="border-l-2 border-amber pl-3 py-1">
                <div className="text-white">{e.summary}</div>
                <div className="text-[10px] text-zinc-500 tracking-widest uppercase">
                  {(e.start || "").replace("T", " ").slice(0, 16)}
                  {e.location ? ` · ${e.location}` : ""}
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="panel">
          <div className="panel-header"><span className="flex items-center gap-2"><Envelope size={14} /> EMAILS NÃO LIDOS</span><span className="text-zinc-500">{unread.length}</span></div>
          <div className="p-4 space-y-2 font-mono text-sm">
            {!status.ready && <div className="text-zinc-600 text-xs">Não conectado.</div>}
            {status.ready && unread.length === 0 && <div className="text-zinc-600 text-xs">Caixa limpa.</div>}
            {unread.map((m) => (
              <div key={m.id} className="border-l-2 border-amber pl-3 py-1">
                <div className="text-white text-xs truncate">{m.subject}</div>
                <div className="text-[10px] text-zinc-500 tracking-widest">
                  {m.from?.split("<")[0]?.trim()}
                </div>
                <div className="text-[10px] text-zinc-600 line-clamp-2">{m.snippet}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="panel">
        <div className="panel-header"><span className="flex items-center gap-2"><FolderOpen size={14} /> DRIVE RECENTES</span><span className="text-zinc-500">{recent.length}</span></div>
        <div className="p-4 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2 font-mono text-xs">
          {!status.ready && <div className="text-zinc-600 col-span-3">Não conectado.</div>}
          {recent.map((f) => (
            <a key={f.id} href={f.webViewLink} target="_blank" rel="noreferrer"
               className="border border-zinc-800 hover:border-amber p-3">
              <div className="text-amber truncate">{f.name}</div>
              <div className="text-[10px] text-zinc-500 mt-1">{(f.modifiedTime || "").slice(0, 10)}</div>
            </a>
          ))}
        </div>
      </div>
    </div>
  );
}

function Pill({ label, ok }) {
  return (
    <div className={`border p-3 flex items-center gap-3 ${ok ? "border-ok" : "border-err/40"}`}>
      {ok ? <CheckCircle size={18} weight="fill" className="text-ok" /> :
            <XCircle size={18} weight="fill" className="text-err" />}
      <div>
        <div className="text-[10px] tracking-widest uppercase text-zinc-500">{label}</div>
        <div className={ok ? "text-ok" : "text-err"}>{ok ? "OK" : "PENDENTE"}</div>
      </div>
    </div>
  );
}
