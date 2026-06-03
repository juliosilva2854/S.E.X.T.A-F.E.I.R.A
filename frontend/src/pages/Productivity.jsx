import React, { useEffect, useState, useRef } from "react";
import { api } from "../api";
import { Plus, Trash, Check, Timer, Note, ListChecks, Play, Pause, ArrowsClockwise } from "@phosphor-icons/react";
import { toast } from "sonner";

export default function Productivity() {
  const [notes, setNotes] = useState([]);
  const [todos, setTodos] = useState([]);
  const [stats, setStats] = useState(null);
  const [noteForm, setNoteForm] = useState({ text: "", tag: "" });
  const [todoForm, setTodoForm] = useState({ text: "", priority: 1 });

  // Pomodoro state
  const [duration, setDuration] = useState(25);
  const [pomoLabel, setPomoLabel] = useState("");
  const [secondsLeft, setSecondsLeft] = useState(25 * 60);
  const [running, setRunning] = useState(false);
  const tickRef = useRef(null);

  const loadAll = async () => {
    try {
      const [n, t, s] = await Promise.all([
        api.get("/notes"), api.get("/todos"), api.get("/pomodoro/stats?days=7"),
      ]);
      setNotes(n.data || []); setTodos(t.data || []); setStats(s.data);
    } catch {}
  };
  useEffect(() => { loadAll(); }, []);

  // Pomodoro tick
  useEffect(() => {
    if (!running) {
      if (tickRef.current) clearInterval(tickRef.current);
      return;
    }
    tickRef.current = setInterval(() => {
      setSecondsLeft((s) => {
        if (s <= 1) {
          clearInterval(tickRef.current);
          setRunning(false);
          api.post("/pomodoro/log", { minutes: duration, label: pomoLabel }).then(loadAll);
          toast.success("Pomodoro concluído!");
          try { new Audio("data:audio/wav;base64,UklGRl9vT19XQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQAAAAA=").play(); } catch {}
          return duration * 60;
        }
        return s - 1;
      });
    }, 1000);
    return () => clearInterval(tickRef.current);
  }, [running, duration, pomoLabel]);

  const start = () => { setSecondsLeft(duration * 60); setRunning(true); };
  const pauseR = () => setRunning(false);
  const resetT = () => { setRunning(false); setSecondsLeft(duration * 60); };

  const mm = String(Math.floor(secondsLeft / 60)).padStart(2, "0");
  const ss = String(secondsLeft % 60).padStart(2, "0");

  const addNote = async () => {
    if (!noteForm.text.trim()) return;
    await api.post("/notes", noteForm);
    setNoteForm({ text: "", tag: "" });
    loadAll();
  };

  const delNote = async (id) => { await api.delete(`/notes/${id}`); loadAll(); };

  const addTodo = async () => {
    if (!todoForm.text.trim()) return;
    await api.post("/todos", todoForm);
    setTodoForm({ text: "", priority: 1 });
    loadAll();
  };

  const toggleTodo = async (id) => { await api.post(`/todos/${id}/toggle`); loadAll(); };
  const delTodo = async (id) => { await api.delete(`/todos/${id}`); loadAll(); };

  return (
    <div className="p-6 space-y-4">
      <div>
        <h1 className="font-display text-3xl">Productivity</h1>
        <p className="text-zinc-500 text-xs tracking-widest uppercase mt-1">
          // POMODORO · QUICK NOTES · TO-DO LIST
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* POMODORO */}
        <div className="panel">
          <div className="panel-header"><span className="flex items-center gap-2"><Timer size={14} /> POMODORO</span></div>
          <div className="p-5 space-y-4 text-center">
            <div data-testid="pomo-timer" className="font-display font-light text-7xl text-amber leading-none">
              {mm}:{ss}
            </div>
            <input
              data-testid="pomo-label"
              value={pomoLabel}
              onChange={(e) => setPomoLabel(e.target.value)}
              placeholder="rótulo da sessão (ex: refatorar relatórios)"
              className="w-full bg-bg border border-zinc-800 focus:border-amber px-3 py-2 outline-none font-mono text-xs"
            />
            <div className="flex justify-center gap-2 items-center">
              <select value={duration} onChange={(e) => { setDuration(parseInt(e.target.value, 10)); setSecondsLeft(parseInt(e.target.value, 10) * 60); }}
                      className="bg-bg border border-zinc-800 focus:border-amber px-3 py-2 font-mono text-xs">
                <option value={15}>15 min</option>
                <option value={25}>25 min</option>
                <option value={45}>45 min</option>
                <option value={60}>60 min</option>
              </select>
              {!running ? (
                <button onClick={start} className="btn-amber inline-flex items-center gap-2" data-testid="pomo-start">
                  <Play size={14} weight="fill" /> INICIAR
                </button>
              ) : (
                <button onClick={pauseR} className="btn-ghost inline-flex items-center gap-2" data-testid="pomo-pause">
                  <Pause size={14} /> PAUSAR
                </button>
              )}
              <button onClick={resetT} className="btn-ghost p-2" data-testid="pomo-reset"><ArrowsClockwise size={14} /></button>
            </div>
            {stats && (
              <div className="text-xs text-zinc-500 border-t border-zinc-800 pt-3 grid grid-cols-3 gap-2">
                <div><div className="font-display text-2xl text-amber">{stats.sessions}</div>sessões 7d</div>
                <div><div className="font-display text-2xl text-amber">{stats.total_hours}h</div>tempo total</div>
                <div><div className="font-display text-2xl text-amber">{Object.keys(stats.by_day || {}).length}</div>dias</div>
              </div>
            )}
          </div>
        </div>

        {/* TODOS */}
        <div className="panel">
          <div className="panel-header"><span className="flex items-center gap-2"><ListChecks size={14} /> TO-DOS</span><span className="text-zinc-500">{todos.filter(t => !t.done).length} pendentes</span></div>
          <div className="p-4 space-y-3">
            <div className="flex gap-2">
              <input
                data-testid="todo-input"
                value={todoForm.text}
                onChange={(e) => setTodoForm({ ...todoForm, text: e.target.value })}
                onKeyDown={(e) => e.key === "Enter" && addTodo()}
                placeholder="nova tarefa..."
                className="flex-1 bg-bg border border-zinc-800 focus:border-amber px-3 py-2 outline-none font-mono text-sm"
              />
              <select value={todoForm.priority} onChange={(e) => setTodoForm({ ...todoForm, priority: parseInt(e.target.value, 10) })}
                      className="bg-bg border border-zinc-800 focus:border-amber px-2 font-mono text-xs">
                <option value={3}>P1</option>
                <option value={2}>P2</option>
                <option value={1}>P3</option>
              </select>
              <button onClick={addTodo} className="btn-amber p-2" data-testid="todo-add"><Plus size={14} /></button>
            </div>
            <div className="space-y-1 font-mono text-sm max-h-72 overflow-auto">
              {todos.length === 0 && <div className="text-zinc-600 text-center py-2 text-xs">vazia</div>}
              {todos.map((t) => (
                <div key={t.id} data-testid={`todo-${t.id}`}
                     className={`flex items-center gap-2 border-l-2 pl-2 py-1 ${
                       t.done ? "border-zinc-700 opacity-50" : t.priority === 3 ? "border-err" : t.priority === 2 ? "border-amber" : "border-zinc-600"
                     }`}>
                  <button onClick={() => toggleTodo(t.id)} className={`w-4 h-4 border ${t.done ? "border-ok bg-ok/20" : "border-zinc-600"}`}>
                    {t.done && <Check size={10} className="text-ok mx-auto" />}
                  </button>
                  <span className={`flex-1 ${t.done ? "line-through text-zinc-500" : "text-white"}`}>{t.text}</span>
                  <button onClick={() => delTodo(t.id)} className="text-zinc-600 hover:text-err"><Trash size={12} /></button>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* NOTES */}
        <div className="panel">
          <div className="panel-header"><span className="flex items-center gap-2"><Note size={14} /> QUICK NOTES</span><span className="text-zinc-500">{notes.length}</span></div>
          <div className="p-4 space-y-3">
            <textarea
              data-testid="note-input"
              value={noteForm.text}
              onChange={(e) => setNoteForm({ ...noteForm, text: e.target.value })}
              rows={2}
              placeholder="anotação rápida..."
              className="w-full bg-bg border border-zinc-800 focus:border-amber px-3 py-2 outline-none font-mono text-xs resize-none"
            />
            <div className="flex gap-2">
              <input
                value={noteForm.tag}
                onChange={(e) => setNoteForm({ ...noteForm, tag: e.target.value })}
                placeholder="tag (opcional)"
                className="flex-1 bg-bg border border-zinc-800 focus:border-amber px-3 py-2 outline-none font-mono text-xs"
              />
              <button onClick={addNote} className="btn-amber inline-flex items-center gap-2" data-testid="note-add">
                <Plus size={14} /> SALVAR
              </button>
            </div>
            <div className="space-y-2 max-h-72 overflow-auto">
              {notes.length === 0 && <div className="text-zinc-600 text-center py-2 text-xs">vazia</div>}
              {notes.map((n) => (
                <div key={n.id} data-testid={`note-${n.id}`} className="border-l-2 border-amber pl-3 py-1 group">
                  <div className="flex items-start justify-between gap-2">
                    <div className="text-sm text-white whitespace-pre-wrap flex-1">{n.text}</div>
                    <button onClick={() => delNote(n.id)} className="text-zinc-600 hover:text-err opacity-0 group-hover:opacity-100"><Trash size={12} /></button>
                  </div>
                  {n.tag && <div className="text-[10px] text-amber tracking-widest uppercase mt-1">#{n.tag}</div>}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
