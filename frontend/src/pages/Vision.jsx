import React, { useRef, useState } from "react";
import { API } from "../api";
import { Eye, Upload, ImageSquare } from "@phosphor-icons/react";
import { toast } from "sonner";

export default function Vision() {
  const [preview, setPreview] = useState(null);
  const [file, setFile] = useState(null);
  const [instruction, setInstruction] = useState("Descreva o que está nesta imagem com detalhes técnicos.");
  const [result, setResult] = useState("");
  const [loading, setLoading] = useState(false);
  const inputRef = useRef(null);

  const onPick = (e) => {
    const f = e.target.files?.[0];
    if (!f) return;
    setFile(f);
    setPreview(URL.createObjectURL(f));
    setResult("");
  };

  const onPaste = (e) => {
    const item = [...(e.clipboardData?.items || [])].find((it) => it.type.startsWith("image/"));
    if (!item) return;
    const f = item.getAsFile();
    setFile(f);
    setPreview(URL.createObjectURL(f));
    setResult("");
    toast.success("Imagem colada");
  };

  const analyze = async () => {
    if (!file) return toast.error("Anexe uma imagem");
    setLoading(true);
    setResult("");
    try {
      const fd = new FormData();
      fd.append("file", file);
      fd.append("instruction", instruction);
      const res = await fetch(`${API}/vision/analyze`, { method: "POST", body: fd });
      if (!res.ok) throw new Error("falhou");
      const data = await res.json();
      setResult(data.description || "(sem retorno)");
    } catch (e) {
      toast.error("Falha na análise");
    } finally { setLoading(false); }
  };

  return (
    <div className="p-6 space-y-4" onPaste={onPaste}>
      <div className="flex items-end justify-between">
        <div>
          <h1 className="font-display text-3xl">Visão Computacional</h1>
          <p className="text-zinc-500 text-xs tracking-widest uppercase mt-1">
            // GEMINI VISION · MULTIMODAL · MANDE PRINTSCREEN
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="panel">
          <div className="panel-header">ENTRADA</div>
          <div className="p-5 space-y-4">
            <div
              className="border-2 border-dashed border-zinc-800 hover:border-amber p-8 flex flex-col items-center justify-center cursor-pointer min-h-[260px]"
              onClick={() => inputRef.current?.click()}
              data-testid="vision-dropzone"
            >
              {preview ? (
                <img src={preview} alt="preview" className="max-h-64 object-contain" />
              ) : (
                <>
                  <ImageSquare size={48} className="text-amber/40 mb-2" />
                  <div className="text-zinc-500 text-sm">Clique para anexar ou Ctrl+V para colar imagem</div>
                </>
              )}
              <input
                ref={inputRef}
                type="file"
                accept="image/*"
                hidden
                onChange={onPick}
                data-testid="vision-file-input"
              />
            </div>
            <div>
              <label className="text-[10px] tracking-widest uppercase text-zinc-500">Instrução para a MAVIS</label>
              <textarea
                data-testid="vision-instruction"
                value={instruction}
                onChange={(e) => setInstruction(e.target.value)}
                rows={3}
                className="w-full bg-bg border border-zinc-800 focus:border-amber px-3 py-2 outline-none font-mono text-sm resize-none"
              />
            </div>
            <button
              onClick={analyze}
              disabled={!file || loading}
              data-testid="analyze-btn"
              className="btn-amber inline-flex items-center gap-2 disabled:opacity-40"
            >
              <Eye size={16} weight="fill" /> {loading ? "ANALISANDO..." : "ANALISAR"}
            </button>
          </div>
        </div>

        <div className="panel">
          <div className="panel-header">RESULTADO</div>
          <div className="p-5 font-mono text-sm min-h-[260px]">
            {loading && <div className="text-zinc-500 blink-caret">processando</div>}
            {!loading && !result && (
              <div className="text-zinc-600">Aguardando análise.</div>
            )}
            {result && (
              <div data-testid="vision-result" className="border-l-2 border-amber pl-3 whitespace-pre-wrap text-white">
                {result}
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="panel p-4 text-xs text-zinc-500 leading-relaxed">
        <div className="text-amber text-[11px] tracking-widest uppercase mb-1">// DICA</div>
        No app desktop (sexta-feira.py), diga "<span className="text-white">olha a tela</span>" ou "<span className="text-white">o que tem na tela</span>" e a MAVIS captura screenshot automaticamente. Aqui no painel você pode mandar qualquer imagem (print, foto de equipamento, planilha) — útil pra analisar telas remotas.
      </div>
    </div>
  );
}
