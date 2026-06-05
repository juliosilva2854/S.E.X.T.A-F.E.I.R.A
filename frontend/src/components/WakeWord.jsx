import React, { useEffect, useRef, useState } from "react";
import { api, API } from "../api";
import { Microphone, MicrophoneSlash, Waveform, X } from "@phosphor-icons/react";
import { toast } from "sonner";

// Palavras de ativação (normalizadas, sem acento)
const WAKE_TOKENS = ["sexta-feira", "sexta feira", "sextafeira", "sexta"];

const normalize = (s) =>
  (s || "").toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "").trim();

export default function WakeWord() {
  const [enabled, setEnabled] = useState(false);
  const [mode, setMode] = useState("off"); // off | listening | command | thinking
  const [lastCmd, setLastCmd] = useState("");
  const [lastReply, setLastReply] = useState("");
  const [supported, setSupported] = useState(true);

  const recRef = useRef(null);
  const runningRef = useRef(false);
  const modeRef = useRef("off");
  const enabledRef = useRef(false);
  const audioRef = useRef(null);

  const setModeBoth = (m) => { modeRef.current = m; setMode(m); };

  useEffect(() => {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) setSupported(false);
  }, []);

  const beep = (freq = 880) => {
    try {
      const Ctx = window.AudioContext || window.webkitAudioContext;
      const ctx = new Ctx();
      const o = ctx.createOscillator(); const g = ctx.createGain();
      o.connect(g); g.connect(ctx.destination);
      o.frequency.value = freq; g.gain.value = 0.06;
      o.start(); o.stop(ctx.currentTime + 0.12);
      o.onended = () => ctx.close();
    } catch { /* ignore */ }
  };

  const startRec = () => {
    if (runningRef.current || !enabledRef.current) return;
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) return;
    const r = new SR();
    r.lang = "pt-BR";
    r.continuous = false;
    r.interimResults = false;
    r.onresult = (e) => {
      const text = e.results[e.results.length - 1][0].transcript || "";
      handleTranscript(text);
    };
    r.onerror = (e) => {
      runningRef.current = false;
      if (e.error === "not-allowed" || e.error === "service-not-allowed") {
        toast.error("Permita o microfone para usar a wake-word");
        stopWake();
      }
    };
    r.onend = () => {
      runningRef.current = false;
      // reinicia a escuta enquanto ativo e não estiver pensando
      if (enabledRef.current && modeRef.current !== "thinking") {
        setTimeout(() => startRec(), 250);
      }
    };
    recRef.current = r;
    try { r.start(); runningRef.current = true; } catch { runningRef.current = false; }
  };

  const stopRec = () => {
    try { recRef.current?.stop(); } catch { /* ignore */ }
    runningRef.current = false;
  };

  const handleTranscript = (text) => {
    const norm = normalize(text);
    if (!norm) return;

    if (modeRef.current === "command") {
      processCommand(text);
      return;
    }
    // modo listening: procura a wake-word
    for (const tok of WAKE_TOKENS) {
      const idx = norm.indexOf(tok);
      if (idx >= 0) {
        const rest = text.slice(idx + tok.length).replace(/^[\s,!.?-]+/, "").trim();
        beep(990);
        if (rest) { processCommand(rest); }
        else { setModeBoth("command"); toast("Sexta-feira ouvindo… fale o comando"); }
        return;
      }
    }
  };

  const processCommand = async (cmd) => {
    setLastCmd(cmd); setLastReply("");
    setModeBoth("thinking");
    stopRec();
    try {
      const { data } = await api.post("/chat", { message: cmd });
      const reply = data.reply || "";
      setLastReply(reply);
      await playTts(reply);
    } catch (e) {
      const msg = e?.response?.data?.detail || "Falha ao falar com o cérebro";
      setLastReply(msg);
      toast.error(msg);
    } finally {
      setModeBoth("listening");
      setTimeout(() => startRec(), 300);
    }
  };

  const playTts = (text) =>
    new Promise((resolve) => {
      if (!text?.trim()) return resolve();
      fetch(`${API}/tts`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
      })
        .then((res) => (res.ok ? res.blob() : Promise.reject()))
        .then((blob) => {
          const url = URL.createObjectURL(blob);
          if (!audioRef.current) return resolve();
          audioRef.current.src = url;
          audioRef.current.onended = () => resolve();
          audioRef.current.onerror = () => resolve();
          audioRef.current.play().catch(() => resolve());
        })
        .catch(() => resolve());
    });

  const startWake = () => {
    enabledRef.current = true;
    setEnabled(true);
    setModeBoth("listening");
    beep(660);
    startRec();
    toast.success('Wake-word ativa. Diga "Sexta-feira".');
  };

  const stopWake = () => {
    enabledRef.current = false;
    setEnabled(false);
    setModeBoth("off");
    stopRec();
  };

  const toggle = () => (enabled ? stopWake() : startWake());

  useEffect(() => () => { enabledRef.current = false; stopRec(); }, []);

  const statusText = {
    off: "Wake-word desligada",
    listening: 'Ouvindo… diga "Sexta-feira"',
    command: "Pode falar o comando…",
    thinking: "Processando…",
  }[mode];

  return (
    <>
      <audio ref={audioRef} hidden />
      <div className="fixed bottom-5 right-5 z-[3000] flex flex-col items-end gap-2">
        {enabled && (
          <div data-testid="wakeword-panel"
            className="w-72 bg-[#0A0A0A] border border-amber-500/40 rounded-lg shadow-[0_0_30px_rgba(245,158,11,0.12)] p-3 font-mono text-xs">
            <div className="flex items-center justify-between mb-2">
              <span className="text-amber-500 uppercase tracking-widest text-[10px] flex items-center gap-1.5">
                <Waveform size={13} weight="fill" className={mode === "listening" ? "animate-pulse" : ""} />
                Sexta-feira
              </span>
              <button data-testid="wakeword-close" onClick={stopWake} className="text-gray-500 hover:text-amber-500">
                <X size={14} weight="bold" />
              </button>
            </div>
            <div className="text-gray-400" data-testid="wakeword-status">{statusText}</div>
            {lastCmd && <div className="mt-2 text-gray-300"><span className="text-gray-600">você:</span> {lastCmd}</div>}
            {lastReply && <div className="mt-1 text-amber-200 whitespace-pre-wrap max-h-32 overflow-auto"><span className="text-gray-600">IA:</span> {lastReply}</div>}
          </div>
        )}
        <button data-testid="wakeword-toggle" onClick={toggle} disabled={!supported}
          title={supported ? "Ativar wake-word" : "Navegador sem suporte a voz (use Chrome/Edge)"}
          className={`w-14 h-14 rounded-full flex items-center justify-center shadow-lg transition-colors disabled:opacity-40 ${
            enabled
              ? "bg-amber-500 text-[#050505] " + (mode === "thinking" ? "animate-spin-slow" : "animate-pulse")
              : "bg-[#141414] border border-[#27272A] text-amber-500 hover:border-amber-500"
          }`}>
          {enabled ? <Microphone size={22} weight="fill" /> : <MicrophoneSlash size={22} weight="regular" />}
        </button>
      </div>
    </>
  );
}
