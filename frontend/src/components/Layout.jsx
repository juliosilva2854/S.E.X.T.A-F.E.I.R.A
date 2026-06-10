import React, { useEffect, useState } from "react";
import { Outlet, NavLink, useLocation } from "react-router-dom";
import {
  Terminal,
  ChatCircle,
  MapPinLine,
  FileText,
  Brain,
  ListBullets,
  GearSix,
  Lightning,
  Eye,
  Clock,
  GoogleLogo,
  WhatsappLogo,
  Lightbulb,
  Code,
  Translate,
  MagnifyingGlass,
  BookOpen,
  Lightning as Bolt,
  Timer,
  CurrencyDollar,
  ChartBar,
  Command,
  Book,
  Robot,
  ShareNetwork,
} from "@phosphor-icons/react";
import { api } from "../api";
import WakeWord from "./WakeWord";
import { useAuth } from "../auth/AuthContext";
import { SignOut } from "@phosphor-icons/react";

const NAV = [
  { to: "/", label: "Overview", icon: Terminal, end: true },
  { to: "/agent", label: "Agent Mode", icon: Robot },
  { to: "/analytics", label: "Analytics", icon: ChartBar },
  { to: "/chat", label: "Chat Neural", icon: ChatCircle },
  { to: "/commands", label: "Comandos", icon: Command },
  { to: "/code", label: "Code Lab", icon: Code },
  { to: "/document", label: "Document Tools", icon: Translate },
  { to: "/research", label: "Research", icon: MagnifyingGlass },
  { to: "/knowledge", label: "Knowledge Base", icon: BookOpen },
  { to: "/workflows", label: "Workflows", icon: Bolt },
  { to: "/productivity", label: "Productivity", icon: Timer },
  { to: "/finance", label: "Finance", icon: CurrencyDollar },
  { to: "/vision", label: "Visão", icon: Eye },
  { to: "/routes", label: "Banco de Rotas", icon: MapPinLine },
  { to: "/reports", label: "Relatórios", icon: FileText },
  { to: "/memory", label: "Memória Curta", icon: Brain },
  { to: "/long-memory", label: "Memória Longa", icon: Lightbulb },
  { to: "/reminders", label: "Lembretes", icon: Clock },
  { to: "/google", label: "Google Hub", icon: GoogleLogo },
  { to: "/whatsapp", label: "WhatsApp", icon: WhatsappLogo },
  { to: "/share", label: "Compartilhar", icon: ShareNetwork },
  { to: "/skills", label: "Skills", icon: Lightning },
  { to: "/logs", label: "Logs Stream", icon: ListBullets },
  { to: "/docs", label: "Documentação", icon: Book },
  { to: "/settings", label: "Configuração", icon: GearSix },
];

function StatusPill({ status }) {
  const ok = !!status?.gemini_configurado;
  return (
    <div
      data-testid="status-pill"
      className="flex items-center gap-2 font-mono text-[11px] tracking-widest uppercase"
    >
      <span className={`w-2 h-2 ${ok ? "bg-ok" : "bg-err"} animate-blink`}></span>
      <span className={ok ? "text-ok" : "text-err"}>[{ok ? "ONLINE" : "OFFLINE"}]</span>
      <span className="text-zinc-500">//</span>
      <span className="text-zinc-400">{status?.modelo || "—"}</span>
      <span className="text-zinc-500">//</span>
      <span className={status?.google_ready ? "text-ok" : "text-zinc-500"}>
        GOOGLE: {status?.google_ready ? "LINKED" : "OFFLINE"}
      </span>
    </div>
  );
}

export default function Layout() {
  const [status, setStatus] = useState(null);
  const location = useLocation();
  const { isCloud, user, logout } = useAuth();

  useEffect(() => {
    let mounted = true;
    const fetchStatus = async () => {
      try {
        const { data } = await api.get("/status");
        if (mounted) setStatus(data);
      } catch (e) {}
    };
    fetchStatus();
    const t = setInterval(fetchStatus, 15000);
    return () => {
      mounted = false;
      clearInterval(t);
    };
  }, []);

  return (
    <div className="h-screen w-screen flex flex-col bg-bg text-white">
      <header
        data-testid="top-bar"
        className="h-14 border-b border-zinc-800 bg-bg flex items-center justify-between px-6 relative"
      >
        <div className="flex items-center gap-3">
          <Lightning size={22} weight="fill" className="text-amber" />
          <div className="font-display font-bold tracking-[0.3em] text-sm">
            S.E.X.T.A — F.E.I.R.A
          </div>
          <span className="text-zinc-600">//</span>
          <span className="font-mono text-xs text-zinc-500 tracking-widest uppercase">
            v3.0 // AGENTIC CORE
          </span>
        </div>
        <StatusPill status={status} />
      </header>

      <div className="flex flex-1 overflow-hidden">
        <aside
          data-testid="sidebar"
          className="w-56 border-r border-zinc-800 bg-bg flex flex-col"
        >
          <nav className="flex-1 py-2 overflow-y-auto">
            {NAV.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.to}
                  to={item.to}
                  end={item.end}
                  data-testid={`nav-${item.label
                    .toLowerCase()
                    .normalize("NFD")
                    .replace(/[\u0300-\u036f]/g, "")
                    .replace(/\s/g, "-")}`}
                  className={({ isActive }) =>
                    `flex items-center gap-3 px-5 py-2.5 border-l-2 font-mono text-[11px] tracking-widest uppercase transition-none ${
                      isActive
                        ? "border-amber bg-surface text-amber"
                        : "border-transparent text-zinc-500 hover:text-amber hover:bg-surface"
                    }`
                  }
                >
                  <Icon size={15} weight={location.pathname === item.to ? "fill" : "regular"} />
                  {item.label}
                </NavLink>
              );
            })}
          </nav>
          <div className="p-4 border-t border-zinc-800 text-[10px] text-zinc-600 font-mono leading-relaxed">
            <div>MAVIS // CORE</div>
            <div className="text-amber/70 mt-1">{status?.ia || "—"}</div>
            <div>FATOS: {status?.total_facts ?? 0}</div>
            <div>LEMBRETES: {status?.total_reminders ?? 0}</div>
            <div className="capitalize">PERSONA: {status?.personality || "—"}</div>
            {isCloud && (
              <button
                data-testid="logout-button"
                onClick={logout}
                className="mt-3 w-full inline-flex items-center justify-center gap-2 border border-zinc-700 text-zinc-400 hover:border-amber hover:text-amber px-3 py-2 rounded uppercase tracking-widest text-[10px] transition-colors"
              >
                <SignOut size={13} weight="bold" /> Sair{user?.email && user.email !== "local" ? ` · ${user.email}` : ""}
              </button>
            )}
          </div>
        </aside>

        <main data-testid="main-content" className="flex-1 overflow-auto grid-bg relative">
          <Outlet context={{ status }} />
        </main>
      </div>
      <WakeWord />
    </div>
  );
}
