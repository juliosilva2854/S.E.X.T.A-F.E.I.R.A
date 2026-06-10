import React, { useEffect, useState } from "react";
import { api } from "../api";
import { toast } from "sonner";
import {
  ShareNetwork, Plus, Copy, Trash, Prohibit, ArrowCounterClockwise, Eye, Link as LinkIcon, X,
} from "@phosphor-icons/react";

export default function Share() {
  const [tokens, setTokens] = useState([]);
  const [label, setLabel] = useState("");
  const [maxFailures, setMaxFailures] = useState(5);
  const [busy, setBusy] = useState(false);
  const [justCreated, setJustCreated] = useState(null); // {id, token, url}

  const origin = window.location.origin;
  const buildUrl = (id, token) => `${origin}/p/analytics?s=${id}&t=${token}`;

  const load = async () => {
    try {
      const { data } = await api.get("/public-tokens");
      setTokens(Array.isArray(data) ? data : []);
    } catch { toast.error("Falha ao carregar links"); }
  };

  useEffect(() => { load(); }, []);

  const create = async () => {
    setBusy(true);
    try {
      const { data } = await api.post("/public-tokens", {
        label: label.trim(),
        max_failures: parseInt(maxFailures, 10) || 5,
      });
      const url = buildUrl(data.id, data.token);
      setJustCreated({ id: data.id, token: data.token, url });
      setLabel("");
      await load();
      toast.success("Link público gerado");
    } catch { toast.error("Falha ao gerar link"); }
    finally { setBusy(false); }
  };

  const copy = async (text) => {
    try { await navigator.clipboard.writeText(text); toast.success("Copiado!"); }
    catch { toast.error("Não foi possível copiar"); }
  };

  const revoke = async (id) => {
    try { await api.post(`/public-tokens/${id}/revoke`); toast.success("Link revogado"); load(); }
    catch { toast.error("Falha ao revogar"); }
  };
  const reactivate = async (id) => {
    try { await api.post(`/public-tokens/${id}/reactivate`); toast.success("Link reativado"); load(); }
    catch { toast.error("Falha ao reativar"); }
  };
  const del = async (id) => {
    try { await api.delete(`/public-tokens/${id}`); toast.success("Link removido"); load(); }
    catch { toast.error("Falha ao remover"); }
  };

  return (
    <div className="min-h-screen bg-[#050505] noise p-4 md:p-8" data-testid="share-page">
      <div className="max-w-[1100px] mx-auto space-y-6">
        <div>
          <h1 className="font-display text-2xl md:text-3xl font-bold tracking-tight text-gray-50 flex items-center gap-2">
            <ShareNetwork size={26} weight="fill" className="text-amber-500" /> Compartilhar
          </h1>
          <p className="text-amber-500 text-[10px] md:text-xs tracking-[0.2em] uppercase font-bold mt-0.5">
            // links públicos da página Analytics · somente leitura
          </p>
        </div>

        {/* GERAR */}
        <div className="bg-[#0A0A0A] border border-[#27272A] rounded-lg p-5 md:p-6">
          <div className="flex flex-wrap items-end gap-4">
            <div className="flex flex-col flex-1 min-w-[200px]">
              <label className="text-[10px] uppercase tracking-widest text-gray-500 mb-1">Rótulo (opcional)</label>
              <input data-testid="share-label-input" value={label} onChange={(e) => setLabel(e.target.value)}
                placeholder="ex: Gestor ToLife"
                className="bg-[#050505] border border-[#27272A] text-gray-200 text-sm rounded px-3 py-2 focus:border-amber-500 focus:outline-none" />
            </div>
            <div className="flex flex-col">
              <label className="text-[10px] uppercase tracking-widest text-gray-500 mb-1">Expira após (tentativas)</label>
              <input data-testid="share-maxfailures-input" type="number" min="1" max="50" value={maxFailures}
                onChange={(e) => setMaxFailures(e.target.value)}
                className="w-40 bg-[#050505] border border-[#27272A] text-gray-200 text-sm rounded px-3 py-2 focus:border-amber-500 focus:outline-none" />
            </div>
            <button onClick={create} disabled={busy} data-testid="share-generate-button"
              className="inline-flex items-center gap-2 bg-amber-500 text-[#050505] hover:bg-amber-400 disabled:opacity-50 font-bold uppercase tracking-wider text-xs px-5 py-2.5 rounded transition-colors">
              <Plus size={15} weight="bold" /> {busy ? "Gerando…" : "Gerar link"}
            </button>
          </div>

          {justCreated && (
            <div data-testid="share-created-box"
              className="mt-5 border border-emerald-500/40 bg-emerald-500/5 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-emerald-400 text-[11px] uppercase tracking-widest font-bold flex items-center gap-2">
                  <LinkIcon size={14} weight="bold" /> Link gerado — copie agora (o token não será exibido de novo)
                </span>
                <button onClick={() => setJustCreated(null)} className="text-gray-500 hover:text-amber-500"><X size={16} weight="bold" /></button>
              </div>
              <div className="flex items-center gap-2">
                <input readOnly value={justCreated.url} data-testid="share-created-url"
                  className="flex-1 bg-[#050505] border border-[#27272A] text-gray-300 text-xs rounded px-3 py-2 font-mono" />
                <button onClick={() => copy(justCreated.url)} data-testid="share-copy-url"
                  className="inline-flex items-center gap-1.5 bg-emerald-500 text-[#052e16] hover:bg-emerald-400 font-bold uppercase tracking-wider text-xs px-3 py-2 rounded transition-colors">
                  <Copy size={14} weight="bold" /> Copiar
                </button>
              </div>
            </div>
          )}
        </div>

        {/* LISTA */}
        <div className="bg-[#0A0A0A] border border-[#27272A] rounded-lg overflow-hidden">
          <div className="px-5 py-3 border-b border-[#27272A] text-amber-500 text-xs uppercase tracking-[0.2em] font-bold">
            Links ativos / revogados
          </div>
          {tokens.length === 0 && (
            <div className="p-8 text-center text-gray-600 text-sm">Nenhum link gerado ainda.</div>
          )}
          <div className="divide-y divide-[#27272A]">
            {tokens.map((t) => (
              <div key={t.id} data-testid={`share-row-${t.id}`}
                className="px-5 py-4 flex flex-wrap items-center justify-between gap-3">
                <div className="min-w-[200px]">
                  <div className="text-gray-200 text-sm font-bold flex items-center gap-2">
                    {t.label || <span className="text-gray-500 italic">sem rótulo</span>}
                    {t.revoked
                      ? <span className="text-[9px] uppercase tracking-wider text-red-400 border border-red-500/40 rounded px-1.5 py-0.5">revogado</span>
                      : <span className="text-[9px] uppercase tracking-wider text-emerald-400 border border-emerald-500/40 rounded px-1.5 py-0.5">ativo</span>}
                  </div>
                  <div className="text-gray-600 text-[11px] font-mono mt-1">
                    id {t.id} · <Eye size={11} className="inline" /> {t.views} views · falhas {t.failures}/{t.max_failures}
                    {t.last_access ? ` · último: ${new Date(t.last_access).toLocaleString("pt-BR")}` : ""}
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {t.revoked
                    ? <button onClick={() => reactivate(t.id)} data-testid={`share-reactivate-${t.id}`}
                        className="inline-flex items-center gap-1.5 border border-emerald-500/50 text-emerald-400 hover:bg-emerald-500/10 font-bold uppercase tracking-wider text-[11px] px-3 py-1.5 rounded transition-colors">
                        <ArrowCounterClockwise size={13} weight="bold" /> Reativar
                      </button>
                    : <button onClick={() => revoke(t.id)} data-testid={`share-revoke-${t.id}`}
                        className="inline-flex items-center gap-1.5 border border-amber-500/50 text-amber-400 hover:bg-amber-500/10 font-bold uppercase tracking-wider text-[11px] px-3 py-1.5 rounded transition-colors">
                        <Prohibit size={13} weight="bold" /> Revogar
                      </button>}
                  <button onClick={() => del(t.id)} data-testid={`share-delete-${t.id}`}
                    className="inline-flex items-center gap-1.5 border border-[#27272A] text-gray-400 hover:border-red-500/50 hover:text-red-400 font-bold uppercase tracking-wider text-[11px] px-3 py-1.5 rounded transition-colors">
                    <Trash size={13} weight="bold" /> Excluir
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-[#0A0A0A] border border-[#27272A] rounded-lg p-4 text-xs text-gray-500 leading-relaxed">
          <span className="text-amber-500 tracking-[0.2em] uppercase text-[10px] font-bold">// como funciona</span>{" "}
          O link abre uma versão <b className="text-gray-300">somente leitura</b> da página Analytics (visualizar e exportar CSV/Excel/PDF, sem editar nada).
          Por segurança, o token é guardado apenas como hash e <b className="text-gray-300">expira automaticamente</b> após o número de tentativas inválidas configurado — basta gerar e compartilhar um novo.
        </div>
      </div>
    </div>
  );
}
