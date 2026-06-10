import React from "react";
import { Routes, Route, Navigate, useLocation } from "react-router-dom";
import { Toaster } from "sonner";
import Layout from "./components/Layout";
import Overview from "./pages/Overview";
import Chat from "./pages/Chat";
import RoutesPage from "./pages/RoutesPage";
import Reports from "./pages/Reports";
import Memory from "./pages/Memory";
import Logs from "./pages/Logs";
import Settings from "./pages/Settings";
import LongMemory from "./pages/LongMemory";
import Reminders from "./pages/Reminders";
import GoogleHub from "./pages/GoogleHub";
import Vision from "./pages/Vision";
import Skills from "./pages/Skills";
import CodeLab from "./pages/CodeLab";
import DocumentTools from "./pages/DocumentTools";
import Research from "./pages/Research";
import Finance from "./pages/Finance";
import Productivity from "./pages/Productivity";
import Knowledge from "./pages/Knowledge";
import Workflows from "./pages/Workflows";
import Analytics from "./pages/Analytics";
import Commands from "./pages/Commands";
import Docs from "./pages/Docs";
import Agent from "./pages/Agent";
import Whatsapp from "./pages/Whatsapp";
import Share from "./pages/Share";
import Access from "./pages/Access";
import PublicAnalytics from "./pages/PublicAnalytics";
import Login from "./pages/Login";
import AuthCallback from "./pages/AuthCallback";
import { AuthProvider, ProtectedRoute } from "./auth/AuthContext";

function AppRouter() {
  const location = useLocation();
  // Volta do OAuth (session_id no fragmento) — processa ANTES das rotas protegidas
  if (location.hash?.includes("session_id=")) {
    return <AuthCallback />;
  }
  return (
    <Routes>
      <Route path="/p/analytics" element={<PublicAnalytics />} />
      <Route path="/login" element={<Login />} />
      <Route
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route path="/" element={<Overview />} />
        <Route path="/agent" element={<Agent />} />
        <Route path="/analytics" element={<Analytics />} />
        <Route path="/commands" element={<Commands />} />
        <Route path="/docs" element={<Docs />} />
        <Route path="/chat" element={<Chat />} />
        <Route path="/code" element={<CodeLab />} />
        <Route path="/document" element={<DocumentTools />} />
        <Route path="/research" element={<Research />} />
        <Route path="/knowledge" element={<Knowledge />} />
        <Route path="/workflows" element={<Workflows />} />
        <Route path="/productivity" element={<Productivity />} />
        <Route path="/finance" element={<Finance />} />
        <Route path="/vision" element={<Vision />} />
        <Route path="/routes" element={<RoutesPage />} />
        <Route path="/reports" element={<Reports />} />
        <Route path="/memory" element={<Memory />} />
        <Route path="/long-memory" element={<LongMemory />} />
        <Route path="/reminders" element={<Reminders />} />
        <Route path="/google" element={<GoogleHub />} />
        <Route path="/whatsapp" element={<Whatsapp />} />
        <Route path="/share" element={<Share />} />
        <Route path="/access" element={<Access />} />
        <Route path="/skills" element={<Skills />} />
        <Route path="/logs" element={<Logs />} />
        <Route path="/settings" element={<Settings />} />
        <Route path="*" element={<Navigate to="/" />} />
      </Route>
    </Routes>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <Toaster
        theme="dark"
        position="bottom-right"
        toastOptions={{
          style: {
            background: "#121212",
            border: "1px solid #27272A",
            color: "#fff",
            borderRadius: 0,
            fontFamily: "JetBrains Mono, monospace",
          },
        }}
      />
      <AppRouter />
    </AuthProvider>
  );
}
