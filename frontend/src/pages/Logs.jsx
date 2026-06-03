import React, { useEffect, useRef, useState } from "react";
import { api, WS_URL } from "../api";
import { Pulse, ArrowDown } from "@phosphor-icons/react";

export default function Logs() {
  const [logs, setLogs] = useState([]);
  const [autoscroll, setAutoscroll] = useState(true);
  const [connected, setConnected] = useState(false);
  const scrollRef = useRef(null);

  useEffect(() => {
    api.get("/logs?limit=200").then(({ data }) => setLogs(data || []));
    let ws;
    try {
      ws = new WebSocket(WS_URL);
      ws.onopen = () => setConnected(true);
      ws.onclose = () => setConnected(false);
      ws.onerror = () => setConnected(false);
      ws.onmessage = (ev) => {
        const e = JSON.parse(ev.data);
        setLogs((cur) => {
          if (cur.find((x) => x.id === e.id)) return cur;
          const next = [...cur, e];
          return next.slice(-500);
        });
      };
    } catch (e) {}
    return () => ws && ws.close();
  }, []);

  useEffect(() => {
    if (autoscroll && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs, autoscroll]);

  const color = (lv) =>
    lv === "ERROR" ? "text-err" : lv === "WARN" ? "text-warn" : "text-amber/80";

  return (
    <div className="p-6 space-y-4 h-full flex flex-col">
      <div className="flex items-end justify-between">
        <div>
          <h1 className="font-display text-3xl">Logs Stream</h1>
          <p className="text-zinc-500 text-xs tracking-widest uppercase mt-1">
            // SISTEMA EM TEMPO REAL
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 text-[11px] tracking-widest uppercase">
            <Pulse size={12} className={connected ? "text-ok animate-pulse" : "text-err"} />
            <span className={connected ? "text-ok" : "text-err"}>
              {connected ? "STREAM // LIVE" : "STREAM // OFFLINE"}
            </span>
          </div>
          <button
            data-testid="toggle-autoscroll"
            onClick={() => setAutoscroll((a) => !a)}
            className={`btn-ghost inline-flex items-center gap-2 ${
              autoscroll ? "border-amber text-amber" : ""
            }`}
          >
            <ArrowDown size={14} /> AUTO-SCROLL: {autoscroll ? "ON" : "OFF"}
          </button>
        </div>
      </div>

      <div
        data-testid="logs-stream"
        ref={scrollRef}
        className="panel flex-1 overflow-auto p-4 font-mono text-[12px] leading-relaxed bg-black"
      >
        {logs.length === 0 && (
          <div className="text-zinc-600 blink-caret">aguardando eventos</div>
        )}
        {logs.map((l) => (
          <div key={l.id} className="flex gap-3">
            <span className="text-zinc-600">{(l.ts || "").slice(11, 19)}</span>
            <span className={color(l.level)}>[{l.level}]</span>
            <span className="text-zinc-500">{l.source}</span>
            <span className="text-white">{l.message}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
