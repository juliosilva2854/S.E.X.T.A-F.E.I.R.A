import React, { useEffect, useState } from "react";
import { api } from "../api";
import { toast } from "sonner";
import {
  ShieldCheck, Plus, Trash, EnvelopeSimple, UserCircle, GoogleLogo, Lock, Clock, SignOut,
} from "@phosphor-icons/react";
import { useAuth } from "../auth/AuthContext";

function fmt(dt) {
  if (!dt) return "—";
  try { return new Date(dt).toLocaleString("pt-BR"); } catch { return "—"; }
}

export default function Access() {
  const { isCloud } = useAuth();
  const [emails, setEmails] = useState([]);
  const [users, setUsers] = useState([]);
  const [newEmail, setNewEmail] = useState("");
  const [busy, setBusy] = useState(false);

  const load = async () => {
    try {
      const [{ data: em }, { data: us }] = await Promise.all([
        api.get("/allowed-emails"),
        api.get("/users"),
      ]);
      setEmails(Array.isArray(em) ? em : []);
      setUsers(Array.isArray(us) ? us : []);
    } catch { toast.error("Falha ao carregar dados de acesso"); }
  };

  useEffect(() => { load(); }, []);

  const addEmail = async () => {
    const email = newEmail.trim().toLowerCase();
    if (!email || !email.includes("@")) { toast.error("E-mail inválido"); return; }
    setBusy(true);
    try {
      await api.post("/allowed-emails", { email });
      setNewEmail("");
      await load();
      toast.success("E-mail autorizado");
    } catch (e) { toast.error(e?.response?.data?.detail || "Falha ao adicionar"); }
    finally { setBusy(false); }
  };

  const removeEmail = async (email) => {
    try {
      await api.delete(`/allowed-emails/${encodeURIComponent(email)}`);
      await load();
      toast.success("E-mail removido");
    } catch { toast.error("Falha ao remover"); }
  };

  const logoutAll = async (userId, name) => {
    try {
      const { data } = await api.post(`/users/${encodeURIComponent(userId)}/logout`);
      await load();
      toast.success(`${data.revoked} sessão(ões) encerrada(s) de ${name}`);
    } catch { toast.error("Falha ao encerrar sessões"); }
  };

  return (
    <div className="min-h-screen bg-[#050505] noise p-4 md:p-8" data-testid="access-page">
      <div className="max-w-[1100px] mx-auto space-y-6">
        <div>
          <h1 className="font-display text-2xl md:text-3xl font-bold tracking-tight text-gray-50 flex items-center gap-2">
            <ShieldCheck size={26} weight="fill" className="text-amber-500" /> Acesso
          </h1>
          <p className="text-amber-500 text-[10px] md:text-xs tracking-[0.2em] uppercase font-bold mt-0.5">
            // quem pode entrar no painel · login por Google + senha
          </p>
        </div>

        {!isCloud && (
          <div data-testid="access-local-warning"
            className="bg-amber-500/5 border border-amber-500/30 rounded-lg p-4 text-xs text-amber-300/90 leading-relaxed">
            <b className="text-amber-400">Modo local ativo (IS_CLOUD=false).</b> O painel está aberto aqui no PC, sem login.
            As regras abaixo passam a valer automaticamente quando o app rodar na nuvem (IS_CLOUD=true). Você pode configurar a allowlist desde já.
          </div>
        )}

        {/* ALLOWLIST */}
        <div className="bg-[#0A0A0A] border border-[#27272A] rounded-lg p-5 md:p-6">
          <div className="text-amber-500 text-xs uppercase tracking-[0.2em] font-bold mb-4 flex items-center gap-2">
            <GoogleLogo size={15} weight="bold" /> E-mails Google autorizados
          </div>
          <div className="flex flex-wrap items-end gap-3">
            <div className="flex flex-col flex-1 min-w-[220px]">
              <label className="text-[10px] uppercase tracking-widest text-gray-500 mb-1">Adicionar e-mail</label>
              <input data-testid="access-email-input" value={newEmail} type="email"
                onChange={(e) => setNewEmail(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && addEmail()}
                placeholder="exemplo@gmail.com"
                className="bg-[#050505] border border-[#27272A] text-gray-200 text-sm rounded px-3 py-2 focus:border-amber-500 focus:outline-none" />
            </div>
            <button onClick={addEmail} disabled={busy} data-testid="access-add-email-button"
              className="inline-flex items-center gap-2 bg-amber-500 text-[#050505] hover:bg-amber-400 disabled:opacity-50 font-bold uppercase tracking-wider text-xs px-5 py-2.5 rounded transition-colors">
              <Plus size={15} weight="bold" /> Autorizar
            </button>
          </div>

          <div className="mt-5 divide-y divide-[#27272A] border border-[#27272A] rounded">
            {emails.length === 0 && (
              <div className="p-6 text-center text-gray-600 text-sm">Nenhum e-mail autorizado.</div>
            )}
            {emails.map((e) => (
              <div key={e.email} data-testid={`access-email-row-${e.email}`}
                className="px-4 py-3 flex items-center justify-between gap-3">
                <div className="flex items-center gap-2.5 min-w-0">
                  <EnvelopeSimple size={16} className="text-amber-500 shrink-0" />
                  <span className="text-gray-200 text-sm truncate">{e.email}</span>
                </div>
                <button onClick={() => removeEmail(e.email)} data-testid={`access-remove-email-${e.email}`}
                  className="inline-flex items-center gap-1.5 border border-[#27272A] text-gray-400 hover:border-red-500/50 hover:text-red-400 font-bold uppercase tracking-wider text-[11px] px-3 py-1.5 rounded transition-colors shrink-0">
                  <Trash size={13} weight="bold" /> Remover
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* USUÁRIOS / ÚLTIMOS ACESSOS */}
        <div className="bg-[#0A0A0A] border border-[#27272A] rounded-lg overflow-hidden">
          <div className="px-5 py-3 border-b border-[#27272A] text-amber-500 text-xs uppercase tracking-[0.2em] font-bold flex items-center gap-2">
            <Clock size={15} weight="bold" /> Últimos acessos
          </div>
          {users.length === 0 && (
            <div className="p-8 text-center text-gray-600 text-sm">Ninguém entrou ainda.</div>
          )}
          <div className="divide-y divide-[#27272A]">
            {users.map((u) => (
              <div key={u.user_id} data-testid={`access-user-row-${u.user_id}`}
                className="px-5 py-4 flex flex-wrap items-center justify-between gap-3">
                <div className="flex items-center gap-3 min-w-0">
                  <UserCircle size={26} className="text-gray-600 shrink-0" />
                  <div className="min-w-0">
                    <div className="text-gray-200 text-sm font-bold truncate flex items-center gap-2">
                      {u.name || u.email}
                      <span className="text-[9px] uppercase tracking-wider text-gray-400 border border-[#27272A] rounded px-1.5 py-0.5 inline-flex items-center gap-1">
                        {u.auth === "google" ? <GoogleLogo size={10} weight="bold" /> : <Lock size={10} weight="bold" />}
                        {u.auth}
                      </span>
                    </div>
                    <div className="text-gray-600 text-[11px] font-mono mt-0.5 truncate">{u.email}</div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-[10px] uppercase tracking-widest text-gray-500">Último acesso</div>
                  <div className="text-amber-400 text-xs font-mono">{fmt(u.last_login)}</div>
                  <button onClick={() => logoutAll(u.user_id, u.name || u.email)}
                    data-testid={`access-logout-all-${u.user_id}`}
                    className="mt-2 inline-flex items-center gap-1.5 border border-[#27272A] text-gray-400 hover:border-red-500/50 hover:text-red-400 font-bold uppercase tracking-wider text-[10px] px-2.5 py-1.5 rounded transition-colors">
                    <SignOut size={12} weight="bold" /> Encerrar sessões
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
