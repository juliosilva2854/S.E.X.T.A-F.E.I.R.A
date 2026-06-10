import React, { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Lightning } from "@phosphor-icons/react";
import { api } from "../api";
import { useAuth } from "../auth/AuthContext";

// Callback do Google OAuth NATIVO. O Google redireciona para {origin}/auth/google?code=...&state=...
// REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
export default function AuthCallback() {
  const navigate = useNavigate();
  const { setUser } = useAuth();
  const processed = useRef(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (processed.current) return;
    processed.current = true;

    const params = new URLSearchParams(window.location.search);
    const code = params.get("code");
    const state = params.get("state");
    const oauthErr = params.get("error");

    if (oauthErr) { setError(`Google: ${oauthErr}`); setTimeout(() => navigate("/login", { replace: true }), 2500); return; }
    if (!code) { navigate("/login", { replace: true }); return; }
    if (state && sessionStorage.getItem("oauth_state") && state !== sessionStorage.getItem("oauth_state")) {
      setError("Estado inválido (proteção CSRF). Tente novamente.");
      setTimeout(() => navigate("/login", { replace: true }), 2500);
      return;
    }
    sessionStorage.removeItem("oauth_state");

    (async () => {
      try {
        const redirectUri = window.location.origin + "/auth/google";
        const { data } = await api.post("/auth/google", { code, redirect_uri: redirectUri });
        setUser(data.user);
        window.history.replaceState(null, "", "/");
        navigate("/", { replace: true });
      } catch (err) {
        setError(err?.response?.data?.detail || "Falha ao autenticar com o Google.");
        setTimeout(() => navigate("/login", { replace: true }), 3000);
      }
    })();
    // eslint-disable-next-line
  }, []);

  return (
    <div data-testid="auth-callback" className="min-h-screen bg-[#050505] noise flex items-center justify-center p-4">
      <div className="text-center">
        <Lightning size={26} weight="fill" className="text-amber-500 mx-auto animate-pulse" />
        {!error ? (
          <p className="mt-4 font-mono text-xs tracking-[0.3em] uppercase text-amber-500">Autenticando…</p>
        ) : (
          <p data-testid="auth-callback-error" className="mt-4 font-mono text-xs text-red-400 max-w-sm">{error}</p>
        )}
      </div>
    </div>
  );
}
