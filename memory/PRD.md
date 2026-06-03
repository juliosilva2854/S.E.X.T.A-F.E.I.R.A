# S.E.X.T.A - F.E.I.R.A (MAVIS) — Personal AI Assistant v4.0

## Visão Geral
IA pessoal multifacetada operada via voz (desktop) e painel web. Evolução em 4 fases:
- v1: codebase original (Python desktop com Vosk + Gemini + Edge TTS + Playwright FieldControl/WhatsApp + Sheets)
- v2: Painel Web FastAPI + React (chat, rotas, relatórios, memória, vozes)
- v3: IA Agentic (multimodal vision, Google ecosystem completo, memória longa, lembretes, scheduler, modo proativo, wake word, 3 personalidades, smart_extract, sistema info)
- **v4 (atual): Hub de Produtividade Completa** — Code Lab, Document Tools, Research/Dossier, Workflows automatizados, Knowledge Base com RAG, Productivity (Pomodoro/Notes/Todos), Finance (cotações + calculadora)

## Arquitetura

### Pacote `/app/mavis/` (compartilhado desktop + web)
```
mavis/
├── core/
│   ├── brain.py            # Gemini 2.5-flash + multimodal + smart_extract + personalidades
│   ├── long_memory.py      # Fatos persistentes do operador
│   ├── reminders.py        # Lembretes
│   ├── router.py           # Intent matching (40+ regex)
│   ├── storage.py          # Escrita atômica
│   └── paths.py
└── skills/
    ├── computer.py         # PyAutoGUI (desktop)
    ├── vision.py           # mss + Gemini Vision
    ├── system_info.py      # psutil
    ├── google_auth.py      # OAuth2 shared
    ├── google_calendar.py
    ├── google_gmail.py
    ├── google_drive.py
    ├── whatsapp.py         # Playwright (desktop)
    ├── scheduler.py        # APScheduler
    ├── proactive.py        # Loop proativo
    ├── wake_word.py        # openWakeWord (desktop)
    ├── news_weather.py     # RSS + Open-Meteo
    ├── code_assistant.py   # Gerar/explicar/revisar/refatorar/converter/debug código
    ├── python_sandbox.py   # Executor Python isolado (subprocess + bloqueia subprocess/socket/ctypes/shutil)
    ├── document_tools.py   # Resumir/traduzir/reescrever/sentimento/email
    ├── research.py         # Dossier multi-step (subqueries → web → síntese)
    ├── finance.py          # Forex (awesomeapi) + Crypto (CoinGecko) + Loan/Compound calculator
    ├── productivity.py     # Quick Notes + Todos + Pomodoro log
    ├── workflows.py        # Macros (steps com {{label}} interpolation)
    └── knowledge.py        # KB: PDF/TXT chunking + keyword search + Gemini synthesis
```

### Backend FastAPI (`/app/backend/server.py`) — ~70 endpoints

**Core / IA**
- `/api/health`, `/api/status`, `/api/config` (GET/PATCH personalidade)
- `/api/chat` — intent routing + skill execution + brain
- `/api/vision/analyze` — upload + Gemini Vision
- `/api/tts`, `/api/tts/voices` — Edge TTS
- `/api/memory` (curta), `/api/long-memory` (longa CRUD)
- `/api/reminders` + `/api/reminders/natural` (LLM parse) + scheduler
- `/api/research` — dossier
- `/api/logs` + WebSocket stream

**Code Lab**
- `/api/code/generate|explain|review|refactor|convert|debug` (Gemini)
- `/api/code/execute` — sandbox Python (timeout 8s, módulos bloqueados)

**Document Tools**
- `/api/doc/summarize|translate|rewrite|key-points|sentiment|compose-email`

**Finance** (sem API key)
- `/api/finance/forex`, `/api/finance/multi`, `/api/finance/crypto` (CoinGecko)
- `/api/finance/loan` (Price), `/api/finance/compound` (juros compostos com aporte)

**Productivity**
- `/api/notes`, `/api/todos` (CRUD), `/api/pomodoro/log`, `/api/pomodoro/stats`

**Workflows**
- `/api/workflows` (CRUD), `/api/workflows/{id}/run`, `/api/workflows/runs`

**Knowledge Base**
- `/api/knowledge/documents` (CRUD + upload PDF/TXT/MD), `/api/knowledge/ask` (RAG)

**Google Ecosystem**
- `/api/google/status`, `/api/google/calendar/{today|week}`, `/api/google/gmail/{unread|message|send}`, `/api/google/drive/{recent|search}`

**Sistema / Skills**
- `/api/skills`, `/api/system/info`, `/api/news`, `/api/weather`

**Rotas / Relatórios**
- `/api/routes` (CRUD), `/api/reports` (CRUD)

**Comandos**
- `/api/commands/execute`

### Frontend React — 19 páginas com tema "Tactical Command Center"

1. Overview (hero + stats + logs live + relatórios recentes)
2. **Chat Neural** (TTS browser + Web Speech ditado)
3. **Code Lab** (7 modos: gerar/explicar/revisar/refatorar/converter/debug/executar)
4. **Document Tools** (6 abas: resumir/traduzir/reescrever/pontos/sentimento/email)
5. **Research** (dossier multi-step com subqueries + fontes)
6. **Knowledge Base** (upload + Q&A com citações de fonte)
7. **Workflows** (builder com steps + {{label}} + histórico)
8. **Productivity** (Pomodoro timer + Quick Notes + Todos)
9. **Finance** (5 cotações + calculadora empréstimo + juros compostos + bitcoin)
10. **Visão** (upload imagem + Gemini Vision)
11. Banco de Rotas (CRUD 267 rotas)
12. Relatórios (preview + criar manual)
13. Memória Curta
14. Memória Longa (fatos por categoria)
15. Lembretes (CRUD + criação por frase natural)
16. **Google Hub** (status OAuth + agenda + emails + drive + instruções inline)
17. Skills (catálogo + telemetria CPU/RAM/Disco/Clima + manchetes)
18. Logs Stream (WebSocket)
19. Configuração (3 personalidades + 5 vozes testáveis)

### Desktop (`/app/sexta-feira.py`)
Loop voz: STT → router.match_intent → execute_skill_local OU brain.chat_text → TTS → fala. Modo proativo background, re-agenda lembretes pendentes no startup, mantém compat com rotinas.py legacy.

## Implementado nesta sessão (v4.2 — Configurabilidade Total + Auto Weekly, 2026-06-03)
- **Editor `.env` via UI** (`/api/env/items`, `/api/env/update`): 15 chaves editáveis com whitelist, sensíveis mascaradas com toggle de visualização, backup automático em `.env.bak` antes de cada save
- **Upload `credenciais.json` via UI** (`/api/google/credentials`) — não precisa mais SSH; valida JSON OAuth
- **Comandos personalizados** (`/api/custom-commands` CRUD + nova página `/commands`): regex → resposta instantânea, AVALIADOS antes do cérebro (zero latência, zero custo Gemini); 3 exemplos prontos
- **Import em massa de relatórios** (`/api/reports/import`) — payload `{items: [...]}` para popular histórico de uma vez
- **Auto resumo semanal**: APScheduler cron `day_of_week=fri, hour=18` (configurável via `MAVIS_AUTO_WEEKLY_HOUR`); Gemini gera texto narrativo + métricas; persiste em banco_relatorios com periodo "AUTO YYYY-Sxx"; botão "RESUMO SEMANAL AGORA" na página Relatórios pra disparar manualmente
- **Página Docs in-app** (`/docs`) — 10 seções: setup painel, setup desktop, comandos de voz, config pelo painel, Google Cloud passo-a-passo, auto-weekly, modo proativo, import em massa, backup/restore, troubleshooting
- **Default km/L = 10** (gasolina urbana SP, mais realista que 12)
- **Sidebar agora com 22 itens** (Comandos + Docs adicionados)

## Configuráveis pela UI (Settings)
- Chave Gemini, Modelo Gemini, Nome IA, Voz neural, Pause threshold, Personalidade, Modo Proativo (1/0), Auto-weekly (1/0), Hora do auto-weekly, km/L do veículo, R$/L combustível, FieldControl email/senha, WhatsApp número/grupo, Planilha Google.

## Resultados do auto-weekly testado
- POST /api/reports/auto-weekly criou "AUTO 2026-S22" com texto Gemini narrativo + métricas (311 km, 13 visitas, 8 preventivas, 12 atendimentos)

## Implementado em sessão anterior (v4.1)
- **`mavis/skills/analytics.py`** — Parser inteligente sem custo LLM:
  - Detecta unidades visitadas por matching contra banco_de_dados.json (267 rotas → ~80 unidades únicas)
  - Anti-substring (UPA VILA MARIANA não duplica com VILA MARIANA)
  - Normalização de acentos (PA JARDIM MACEDÔNIA = PA JARDIM MACEDONIA)
  - Calcula KM diário encadeando CASA → loc1 → loc2 → ... → CASA via routes_km
  - Conta atividades por keywords (manutenção preventiva, atendimento técnico, entrega de insumos, troca, configuração)
  - Conta equipamentos (manguito, Trius, totem, teclado, glicosímetro, fonte, P.A, oxímetro, termômetro, impressora, bomba, fechadura, cabo)
- **8 endpoints** `/api/analytics/*`: kpis, weekly, monthly, daily, heatmap, activities, month/{YYYY-MM} (detalhe), parse-all
- **Página `/analytics`** com recharts:
  - 10 KPI cards (Total KM, Dias úteis, Médias dia/semana, Litros, R$ combustível, Preventivas/Atendimentos/Entregas/Trocas)
  - Bar chart KM por semana (12 semanas)
  - Pie chart Tipos de atividade
  - Bar chart KM por mês + Cards mensais clicáveis (com modal de detalhe)
  - Mapa de calor por dia da semana
  - Top 10 Destinos + Top 8 Equipamentos
  - Line chart KM diário (30 dias)
  - Modal de detalhe mensal: KPIs do mês + top unidades + equipamentos + rota detalhada de cada dia
  - Configuradores: R$/L e km/L (cálculo de custo combustível dinâmico)
- Dependência nova: `recharts` (gráficos React)

## Resultados sobre dados reais (4 relatórios → 20 dias úteis)
- 1556 km totais
- 77.8 km/dia médio · 389 km/semana
- R$ 763.74 em combustível estimado (5.89/L, 12 km/L)
- 40 manutenções preventivas, 22 atendimentos, 7 entregas, 18 trocas
- Top destino: UPA SANTO AMARO (5×)
- Top equipamento trocado: Manguito (11×)
- 8 novos módulos em `mavis/skills/`
- ~30 endpoints novos no backend
- 7 páginas novas no frontend (sidebar agora com 19 itens)
- Sandbox Python seguro (bloqueia subprocess/socket/ctypes/shutil; timeout 8s)
- Knowledge Base com PDF parsing (pypdf) + chunking + keyword retrieval + Gemini synthesis
- Workflow engine com state interpolation `{{label}}` entre steps
- Forex e crypto sem API key
- Validação: tudo passou via curl (factorial, loan, compound, sandbox-bloqueado-OK)

## Persona / Operador
Júlio Cesar — usuário corporativo (engenharia/manutenção ToLife)

## Roadmap / Backlog
- **P1**: WebSocket bidirecional painel→desktop pra disparar PyAutoGUI remotamente
- **P1**: Wake word custom "sexta-feira" treinado em openWakeWord
- **P1**: Embeddings real para Knowledge Base (atualmente keyword-based) usando text-embedding-004 do Google
- **P2**: PWA / mobile responsive
- **P2**: Workflows agendados (cron-like, hoje só on-demand)
- **P2**: Splittar server.py em routers por domínio (já passou 1000 LOC)
- **P3**: Spotify Web API OAuth
- **P3**: Integração Notion / Obsidian para Quick Notes

## Como Rodar
- Backend e Frontend: supervisor (auto)
- Desktop: `pip install -r requirements.txt && playwright install chromium && python3 sexta-feira.py`
- Google APIs: seguir README_MAVIS.md seção 3 (passo-a-passo Cloud Console)
