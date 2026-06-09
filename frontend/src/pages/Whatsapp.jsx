import React, { useEffect, useState } from "react";
import { api } from "../api";
import { Plus, Trash, WhatsappLogo, X, PaperPlaneTilt, Copy } from "@phosphor-icons/react";
import { toast } from "sonner";

export default function Whatsapp() {
  const [list, setList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);
  const [form, setForm] = useState({ nome: "", tipo: "grupo", display_name: "" });

  const [showSend, setShowSend] = useState(false);
  const [sendForm, setSendForm] = useState({ favorite_id: "", message: "" });
  const [sending, setSending] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const { data } = await api.get("/whatsapp/favorites");
      setList(data || []);
    } catch {
      toast.error("Falha ao carregar favoritos");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const add = async () => {
    if (!form.nome.trim()) {
      toast.error("Informe o nome exato do contato/grupo");
      return;
    }
    try {
      await api.post("/whatsapp/favorites", form);
      toast.success("Favorito adicionado");
      setForm({ nome: "", tipo: "grupo", display_name: "" });
      setShowAdd(false);
      load();
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Falha ao adicionar");
    }
  };

  const remove = async (id) => {
    if (!window.confirm("Remover este favorito?")) return;
    try {
      await api.delete(`/whatsapp/favorites/${id}`);
      toast.success("Removido");
      load();
    } catch {
      toast.error("Falha ao remover");
    }
  };

  const send = async () => {
    if (!sendForm.favorite_id) { toast.error("Selecione um destino"); return; }
    if (!sendForm.message.trim()) { toast.error("Mensagem vazia"); return; }
    setSending(true);
    try {
      // Faz o pedido diretamente para o novo backend Python (que comunica com o WAHA)
      const { data } = await api.post("/whatsapp/send", sendForm);

      if (data.sent || data.ok) {
        toast.success(`Enviado com sucesso!`);
        setShowSend(false);
        setSendForm({ favorite_id: "", message: "" });
      } else {
        toast.error(data.error || data.message || "Falha no envio");
      }
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Falha ao enviar");
    } finally {
      setSending(false);
    }
  };

  const copyNome = (nome) => {
    navigator.clipboard.writeText(nome);
    toast.success("Nome copiado");
  };

  return (
    <div className="p-6 space-y-6 max-w-6xl">
      <div className="flex items-end justify-between flex-wrap gap-3">
        <div>
          <h1 className="font-display text-3xl flex items-center gap-3">
            <WhatsappLogo size={28} weight="fill" className="text-amber" />
            WhatsApp
          </h1>
          <p className="text-zinc-500 text-xs tracking-widest uppercase mt-1">
            // {list.length} CONTATOS / GRUPOS FAVORITOS · USE NOS RESUMOS E ENVIOS MANUAIS
          </p>
        </div>
        <div className="flex gap-2">
          <button
            data-testid="whatsapp-quick-send-btn"
            onClick={() => setShowSend(true)}
            className="btn-ghost inline-flex items-center gap-2"
            disabled={list.length === 0}
            title={list.length === 0 ? "Cadastre um favorito primeiro" : ""}
          >
            <PaperPlaneTilt size={14} weight="fill" /> ENVIO RÁPIDO
          </button>
          <button
            data-testid="whatsapp-add-favorite-btn"
            onClick={() => setShowAdd(true)}
            className="btn-amber inline-flex items-center gap-2"
          >
            <Plus size={16} weight="bold" /> ADICIONAR
          </button>
        </div>
      </div>

      <div className="panel p-5">
        <div className="text-xs text-zinc-500 leading-relaxed mb-4">
          <p className="mb-1">
            <span className="text-amber">// COMO FUNCIONA:</span> cadastre aqui os contatos
            e grupos que você usa para receber resumos. O <b>nome</b> deve bater EXATAMENTE
            com o que aparece na busca do WhatsApp Web. Os favoritos aparecerão no dropdown
            de destino nos resumos semanal/mensal e no botão "Compartilhar" do Analytics.
          </p>
          <p>
            <span className="text-amber">// BACKGROUND API:</span> o sistema agora utiliza
            o WAHA em segundo plano. Os envios são instantâneos e invisíveis.
          </p>
        </div>

        {loading ? (
          <div className="text-zinc-500 text-sm">Carregando…</div>
        ) : list.length === 0 ? (
          <div data-testid="whatsapp-empty" className="text-zinc-500 text-sm">
            Nenhum favorito ainda. Clique em <b>ADICIONAR</b> para começar.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {list.map((f) => (
              <div
                key={f.id}
                data-testid={`whatsapp-favorite-${f.id}`}
                className="border border-zinc-800 hover:border-amber/50 transition-colors rounded p-4 flex flex-col gap-2"
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1 min-w-0">
                    <div className="font-mono text-amber text-[11px] tracking-widest uppercase mb-1">
                      {f.tipo === "grupo" ? "GRUPO" : "CONTATO"}
                    </div>
                    <div className="font-display text-base truncate" title={f.display_name}>
                      {f.display_name}
                    </div>
                    <div className="text-xs text-zinc-500 truncate font-mono" title={f.nome}>
                      {f.nome}
                    </div>
                  </div>
                  <div className="flex flex-col gap-1">
                    <button
                      data-testid={`whatsapp-copy-${f.id}`}
                      onClick={() => copyNome(f.nome)}
                      className="text-zinc-400 hover:text-amber"
                      title="Copiar nome"
                    >
                      <Copy size={14} />
                    </button>
                    <button
                      data-testid={`whatsapp-remove-${f.id}`}
                      onClick={() => remove(f.id)}
                      className="text-zinc-400 hover:text-err"
                      title="Remover"
                    >
                      <Trash size={14} />
                    </button>
                  </div>
                </div>
                <button
                  data-testid={`whatsapp-send-to-${f.id}`}
                  onClick={() => { setSendForm({ favorite_id: f.id, message: "" }); setShowSend(true); }}
                  className="btn-ghost text-[10px] inline-flex items-center justify-center gap-1.5 py-1.5"
                >
                  <PaperPlaneTilt size={12} weight="fill" /> ENVIAR MENSAGEM
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* MODAL ADD */}
      {showAdd && (
        <div className="fixed inset-0 bg-black/80 z-50 flex items-center justify-center p-6">
          <div className="panel w-full max-w-md p-6 space-y-4">
            <div className="flex justify-between items-center">
              <h3 className="font-display text-xl">Novo favorito</h3>
              <button onClick={() => setShowAdd(false)} className="text-zinc-500 hover:text-amber">
                <X size={18} />
              </button>
            </div>
            <div>
              <label className="text-[10px] uppercase tracking-widest text-zinc-500 mb-1 block">
                Nome exato no WhatsApp *
              </label>
              <input
                data-testid="whatsapp-form-nome"
                value={form.nome}
                onChange={(e) => setForm({ ...form, nome: e.target.value })}
                placeholder="Ex: Resumos - ToLife"
                className="w-full bg-bg border border-zinc-800 focus:border-amber px-3 py-2 outline-none font-mono text-sm"
              />
              <p className="text-[10px] text-zinc-600 mt-1">
                Deve bater exatamente com o que aparece na busca do WhatsApp Web.
              </p>
            </div>
            <div>
              <label className="text-[10px] uppercase tracking-widest text-zinc-500 mb-1 block">
                Tipo
              </label>
              <select
                data-testid="whatsapp-form-tipo"
                value={form.tipo}
                onChange={(e) => setForm({ ...form, tipo: e.target.value })}
                className="w-full bg-bg border border-zinc-800 focus:border-amber px-3 py-2 outline-none font-mono text-sm"
              >
                <option value="grupo">Grupo</option>
                <option value="contato">Contato</option>
              </select>
            </div>
            <div>
              <label className="text-[10px] uppercase tracking-widest text-zinc-500 mb-1 block">
                Apelido (opcional)
              </label>
              <input
                data-testid="whatsapp-form-display"
                value={form.display_name}
                onChange={(e) => setForm({ ...form, display_name: e.target.value })}
                placeholder="Ex: Chefe João"
                className="w-full bg-bg border border-zinc-800 focus:border-amber px-3 py-2 outline-none font-mono text-sm"
              />
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <button onClick={() => setShowAdd(false)} className="btn-ghost">CANCELAR</button>
              <button data-testid="whatsapp-save-favorite-btn" onClick={add} className="btn-amber">
                SALVAR
              </button>
            </div>
          </div>
        </div>
      )}

      {/* MODAL ENVIO RÁPIDO */}
      {showSend && (
        <div className="fixed inset-0 bg-black/80 z-50 flex items-center justify-center p-6">
          <div className="panel w-full max-w-lg p-6 space-y-4">
            <div className="flex justify-between items-center">
              <h3 className="font-display text-xl">Envio rápido</h3>
              <button onClick={() => setShowSend(false)} className="text-zinc-500 hover:text-amber">
                <X size={18} />
              </button>
            </div>
            <div>
              <label className="text-[10px] uppercase tracking-widest text-zinc-500 mb-1 block">
                Destino *
              </label>
              <select
                data-testid="whatsapp-send-destino"
                value={sendForm.favorite_id}
                onChange={(e) => setSendForm({ ...sendForm, favorite_id: e.target.value })}
                className="w-full bg-bg border border-zinc-800 focus:border-amber px-3 py-2 outline-none font-mono text-sm"
              >
                <option value="">— escolha um favorito —</option>
                {list.map((f) => (
                  <option key={f.id} value={f.id}>
                    [{f.tipo}] {f.display_name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-[10px] uppercase tracking-widest text-zinc-500 mb-1 block">
                Mensagem *
              </label>
              <textarea
                data-testid="whatsapp-send-message"
                value={sendForm.message}
                onChange={(e) => setSendForm({ ...sendForm, message: e.target.value })}
                rows={8}
                placeholder="Digite a mensagem..."
                className="w-full bg-bg border border-zinc-800 focus:border-amber px-3 py-2 outline-none font-mono text-sm resize-none"
              />
            </div>
            <div className="flex justify-end gap-2">
              <button onClick={() => setShowSend(false)} className="btn-ghost">CANCELAR</button>
              <button
                data-testid="whatsapp-send-now-btn"
                onClick={send}
                disabled={sending}
                className="btn-amber inline-flex items-center gap-2"
              >
                <PaperPlaneTilt size={14} weight="fill" />
                {sending ? "ENVIANDO…" : "ENVIAR"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}