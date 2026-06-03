import React, { useEffect, useState } from "react";
import { api } from "../api";
import { Trash } from "@phosphor-icons/react";
import { toast } from "sonner";

export default function Memory() {
  const [items, setItems] = useState([]);

  const load = () => api.get("/memory").then(({ data }) => setItems(data || []));
  useEffect(() => { load(); }, []);

  const clear = async () => {
    if (!window.confirm("Apagar TODA a memória de conversa?")) return;
    await api.delete("/memory");
    toast.success("Memória apagada");
    load();
  };

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-end justify-between">
        <div>
          <h1 className="font-display text-3xl">Memória de Conversas</h1>
          <p className="text-zinc-500 text-xs tracking-widest uppercase mt-1">
            // {items.length} ENTRADAS RETIDAS NO CÉREBRO
          </p>
        </div>
        <button
          data-testid="memory-clear-btn"
          onClick={clear}
          className="btn-ghost inline-flex items-center gap-2 hover:border-err hover:text-err"
        >
          <Trash size={16} /> APAGAR TUDO
        </button>
      </div>

      <div className="panel p-4 font-mono text-sm space-y-2 max-h-[70vh] overflow-auto">
        {items.length === 0 && (
          <div className="text-zinc-600 text-center py-10">
            Memória vazia. Inicie um diálogo no Chat Neural.
          </div>
        )}
        {items.map((m, i) => {
          const isUser = m.role === "Usuário";
          return (
            <div
              key={i}
              data-testid={`memory-entry-${i}`}
              className={`border-l-2 pl-3 py-1 ${isUser ? "border-zinc-600" : "border-amber"}`}
            >
              <div
                className={`text-[10px] tracking-widest uppercase ${
                  isUser ? "text-zinc-500" : "text-amber"
                }`}
              >
                {isUser ? "USR >" : "SYS // MAVIS"}
              </div>
              <div className={`whitespace-pre-wrap ${isUser ? "text-zinc-300" : "text-white"}`}>
                {m.texto}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
