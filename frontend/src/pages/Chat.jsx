import React, { useEffect, useRef, useState } from "react";
import { api, API } from "../api";
import { PaperPlaneRight, SpeakerHigh, SpeakerSlash, Trash, Microphone, MicrophoneSlash } from "@phosphor-icons/react";
import { toast } from "sonner";

export default function Chat() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [speak, setSpeak] = useState(true);
  const [listening, setListening] = useState(false);
  const audioRef = useRef(null);
  const recognitionRef = useRef(null);
  const scrollRef = useRef(null);

  // Carrega histórico
  useEffect(() => {
    api.get("/memory").then(({ data }) => {
      setMessages(data || []);
    }).catch(() => {});
  }, []);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, loading]);

  // Web Speech API – reconhecimento de voz grátis no browser
  const initRecognition = () => {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) {
      toast.error("Seu browser não suporta reconhecimento de voz");
      return null;
    }
    const r = new SR();
    r.lang = "pt-BR";
    r.continuous = false;
    r.interimResults = false;
    r.onresult = (e) => {
      const text = e.results[0][0].transcript;
      setInput((cur) => (cur ? cur + " " : "") + text);
      setListening(false);
    };
    r.onerror = () => setListening(false);
    r.onend = () => setListening(false);
    return r;
  };

  const toggleListen = () => {
    if (listening) {
      recognitionRef.current?.stop();
      setListening(false);
      return;
    }
    const r = initRecognition();
    if (!r) return;
    recognitionRef.current = r;
    setListening(true);
    try { r.start(); } catch (e) { setListening(false); }
  };

  const playTts = async (text) => {
    if (!speak || !text?.trim()) return;
    try {
      const res = await fetch(`${API}/tts`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
      });
      if (!res.ok) throw new Error("TTS falhou");
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      if (audioRef.current) {
        audioRef.current.src = url;
        audioRef.current.play().catch(() => {});
      }
    } catch (e) {
      toast.error("Falha no sintetizador de voz");
    }
  };

  const send = async () => {
    const text = input.trim();
    if (!text || loading) return;
    setInput("");
    const novoUser = { role: "Usuário", texto: text };
    setMessages((m) => [...m, novoUser]);
    setLoading(true);
    try {
      const { data } = await api.post("/chat", { message: text });
      const novaIa = { role: "Sexta-feira", texto: data.reply };
      setMessages((m) => [...m, novaIa]);
      playTts(data.reply);
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Falha de comunicação com o cérebro");
    } finally {
      setLoading(false);
    }
  };

  const clearMemory = async () => {
    if (!window.confirm("Apagar toda a memória de conversa?")) return;
    await api.delete("/memory");
    setMessages([]);
    toast.success("Memória apagada");
  };

  return (
    <div className="h-full flex flex-col p-6 gap-4">
      <audio ref={audioRef} hidden />
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display text-3xl">Chat Neural</h1>
          <p className="text-zinc-500 text-xs tracking-widest uppercase mt-1">
            // CÉREBRO COGNITIVO GEMINI
          </p>
        </div>
        <div className="flex gap-2">
          <button
            data-testid="toggle-tts-btn"
            onClick={() => setSpeak((s) => !s)}
            className="btn-ghost inline-flex items-center gap-2"
            title="Falar respostas"
          >
            {speak ? <SpeakerHigh size={16} /> : <SpeakerSlash size={16} />}
            {speak ? "VOZ: ON" : "VOZ: OFF"}
          </button>
          <button
            data-testid="clear-memory-btn"
            onClick={clearMemory}
            className="btn-ghost inline-flex items-center gap-2"
          >
            <Trash size={16} /> LIMPAR
          </button>
        </div>
      </div>

      <div
        data-testid="chat-log"
        ref={scrollRef}
        className="panel flex-1 overflow-auto p-4 font-mono text-sm space-y-3"
      >
        {messages.length === 0 && (
          <div className="text-zinc-600 text-center mt-10">
            <span className="blink-caret">Aguardando comando do operador</span>
          </div>
        )}
        {messages.map((m, i) => {
          const isUser = m.role === "Usuário";
          return (
            <div key={i} className={`flex gap-3 ${isUser ? "justify-end" : ""}`}>
              {!isUser && (
                <div className="border-l-2 border-amber pl-3 flex-1 max-w-[80%]">
                  <div className="text-[10px] tracking-widest text-amber uppercase mb-1">
                    SYS // MAVIS
                  </div>
                  <div className="whitespace-pre-wrap text-white">{m.texto}</div>
                </div>
              )}
              {isUser && (
                <div className="border-r-2 border-zinc-600 pr-3 max-w-[80%] text-right">
                  <div className="text-[10px] tracking-widest text-zinc-500 uppercase mb-1">
                    USR &gt;
                  </div>
                  <div className="whitespace-pre-wrap text-zinc-300">{m.texto}</div>
                </div>
              )}
            </div>
          );
        })}
        {loading && (
          <div className="border-l-2 border-amber pl-3">
            <div className="text-[10px] tracking-widest text-amber uppercase mb-1">SYS // MAVIS</div>
            <div className="text-zinc-500 blink-caret">analisando</div>
          </div>
        )}
      </div>

      <div className="panel p-3">
        <div className="flex items-center gap-2">
          <span className="text-amber font-mono text-xs tracking-widest">MAVIS //</span>
          <input
            data-testid="chat-input"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && send()}
            placeholder="digite seu comando, senhor..."
            className="flex-1 bg-transparent outline-none font-mono text-sm placeholder-zinc-600 text-white"
            disabled={loading}
          />
          <button
            data-testid="mic-btn"
            onClick={toggleListen}
            className={`btn-ghost inline-flex items-center gap-2 ${
              listening ? "border-amber text-amber animate-pulse" : ""
            }`}
            title="Ditar por voz"
          >
            {listening ? <MicrophoneSlash size={16} /> : <Microphone size={16} />}
          </button>
          <button
            data-testid="send-btn"
            onClick={send}
            disabled={loading || !input.trim()}
            className="btn-amber inline-flex items-center gap-2 disabled:opacity-40"
          >
            <PaperPlaneRight size={16} weight="fill" /> ENVIAR
          </button>
        </div>
      </div>
    </div>
  );
}
