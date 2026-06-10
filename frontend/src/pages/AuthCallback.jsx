import React, { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Lightning } from "@phosphor-icons/react";
import { api } from "../api";
import { useAuth } from "../auth/AuthContext";

export default function AuthCallback() {
  const navigate = useNavigate();
  const { setUser } = useAuth();
  const processed = useRef(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (processed.current) return;
    processed.current = true;

    const hash = window.location.hash || "";
    const sid = new URLSearchParams(hash.replace(/^#/, "")).get("session_id");
    if (!sid) { navigate("/login", { replace: true }); return; }

    (async () => {
      try {
        const { data } = await api.post("/auth/google", { session_id: sid });
        setUser(data.user);
        // limpa o fragmento e vai pro painel
        window.history.replaceState(null, "", "/");
        navigate("/", { replace: true });
      } catch (err) {
        setError(err?.response?.data?.detail || "Falha ao autenticar com o Google.");
        setTimeout(() => navigate("/login", { replace: true }), 2500);
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
