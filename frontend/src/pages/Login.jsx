import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Lightning, GoogleLogo, Lock, SignIn } from "@phosphor-icons/react";
import { api } from "../api";
import { useAuth } from "../auth/AuthContext";

export default function Login() {
  const navigate = useNavigate();
  const { setUser } = useAuth();
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const googleLogin = () => {
    // REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
    const redirectUrl = window.location.origin + "/";
    window.location.href = `https://auth.emergentagent.com/?redirect=${encodeURIComponent(redirectUrl)}`;
  };

  const passwordLogin = async (e) => {
    e?.preventDefault();
    if (!password) { setError("Informe a senha."); return; }
    setBusy(true); setError("");
    try {
      const { data } = await api.post("/auth/password", { password });
      setUser(data.user);
      navigate("/", { replace: true });
    } catch (err) {
      setError(err?.response?.data?.detail || "Falha no login.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#050505] noise flex items-center justify-center p-4">
      <div data-testid="login-card" className="w-full max-w-md bg-[#0A0A0A] border border-[#27272A] rounded-lg p-8">
        <div className="flex items-center gap-3 mb-1">
          <Lightning size={24} weight="fill" className="text-amber-500" />
          <h1 className="font-display text-2xl font-bold tracking-[0.15em] text-gray-50">
            S.E.X.T.A — F.E.I.R.A
          </h1>
        </div>
        <p className="text-amber-500 text-[10px] tracking-[0.2em] uppercase font-bold mb-7">
          // painel restrito · autenticação obrigatória
        </p>

        <button
          data-testid="login-google-button"
          onClick={googleLogin}
          className="w-full inline-flex items-center justify-center gap-2 bg-white text-[#050505] hover:bg-gray-200 font-bold uppercase tracking-wider text-xs px-4 py-3 rounded transition-colors"
        >
          <GoogleLogo size={18} weight="bold" /> Entrar com Google
        </button>

        <div className="flex items-center gap-3 my-6">
          <div className="flex-1 h-px bg-[#27272A]" />
          <span className="text-gray-600 text-[10px] uppercase tracking-widest">ou senha</span>
          <div className="flex-1 h-px bg-[#27272A]" />
        </div>

        <form onSubmit={passwordLogin}>
          <label className="text-[10px] uppercase tracking-widest text-gray-500 mb-1 block">Senha do painel</label>
          <div className="relative">
            <Lock size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-600" />
            <input
              data-testid="login-password-input"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              className="w-full bg-[#050505] border border-[#27272A] text-gray-200 text-sm rounded pl-9 pr-3 py-2.5 focus:border-amber-500 focus:outline-none transition-colors"
            />
          </div>
          {error && (
            <p data-testid="login-error" className="text-red-400 text-xs mt-3 font-mono">{error}</p>
          )}
          <button
            data-testid="login-password-submit"
            type="submit"
            disabled={busy}
            className="mt-5 w-full inline-flex items-center justify-center gap-2 bg-amber-500 text-[#050505] hover:bg-amber-400 disabled:opacity-50 font-bold uppercase tracking-wider text-xs px-4 py-2.5 rounded transition-colors"
          >
            <SignIn size={15} weight="bold" /> {busy ? "Entrando…" : "Entrar"}
          </button>
        </form>
      </div>
    </div>
  );
}
