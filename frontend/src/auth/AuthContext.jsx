import React, { createContext, useContext, useEffect, useState, useCallback } from "react";
import { Lightning } from "@phosphor-icons/react";
import { api } from "../api";

const AuthCtx = createContext(null);
export const useAuth = () => useContext(AuthCtx);

export function AuthProvider({ children }) {
  const [isCloud, setIsCloud] = useState(null);
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const checkAuth = useCallback(async () => {
    setLoading(true);
    try {
      const { data: cfg } = await api.get("/auth/config");
      setIsCloud(cfg.is_cloud);
      if (!cfg.is_cloud) {
        setUser({ email: "local", name: "Local", auth: "local" });
        return;
      }
      const { data: me } = await api.get("/auth/me");
      setUser(me);
    } catch (e) {
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    // Volta de OAuth: deixa o AuthCallback trocar o session_id antes de checar /me
    if (window.location.hash?.includes("session_id=")) {
      setLoading(false);
      return;
    }
    checkAuth();
  }, [checkAuth]);

  const logout = async () => {
    try { await api.post("/auth/logout"); } catch (e) { /* noop */ }
    setUser(null);
    window.location.href = "/login";
  };

  return (
    <AuthCtx.Provider value={{ isCloud, user, loading, setUser, checkAuth, logout }}>
      {children}
    </AuthCtx.Provider>
  );
}

function LoaderScreen() {
  return (
    <div data-testid="auth-loading" className="h-screen w-screen flex items-center justify-center bg-[#050505]">
      <div className="flex items-center gap-3 text-amber-500 animate-pulse">
        <Lightning size={22} weight="fill" />
        <span className="font-mono text-xs tracking-[0.3em] uppercase">Verificando acesso…</span>
      </div>
    </div>
  );
}

export function ProtectedRoute({ children }) {
  const { isCloud, user, loading } = useAuth();
  if (loading || isCloud === null) return <LoaderScreen />;
  if (isCloud && !user) {
    window.location.replace("/login");
    return <LoaderScreen />;
  }
  return children;
}
