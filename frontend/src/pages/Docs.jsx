import React from "react";
import { Book } from "@phosphor-icons/react";

const SECTIONS = [
  {
    title: "0. Visão geral da MAVIS v4.3",
    body: `MAVIS / Sexta-feira é uma IA pessoal completa com 23 áreas funcionais:

  IA & Cérebro: Chat Neural, Agent Mode (autônomo), Memória Curta, Memória Longa, Lembretes, Vision
  Produtividade: Code Lab, Document Tools, Research, Knowledge Base, Workflows, Productivity, Finance
  Operacional: Banco de Rotas, Relatórios, Analytics Dashboard, Auto Resumo Semanal
  Integrações: Google Hub (Calendar/Gmail/Drive), WhatsApp, FieldControl (desktop)
  Sistema: Skills, Logs Stream, Comandos Personalizados, Configuração, Docs

Tecnologias: Gemini 2.5 Flash (cérebro + visão), Edge TTS (voz pt-BR), Vosk/Web Speech API (STT),
openWakeWord, PyAutoGUI, Playwright, APScheduler, mss (screenshot), psutil, pypdf, FastAPI,
React + Recharts, Tailwind, MongoDB.`,
  },
  {
    title: "1. Como rodar o painel web (este painel)",
    body: `O painel já está rodando neste container, mantido pelo supervisor:

  sudo supervisorctl status
  sudo supervisorctl restart backend
  sudo supervisorctl restart frontend

Backend: FastAPI :8001 · Frontend: React :3000 · Mongo: localhost:27017
Logs: tail -n 200 /var/log/supervisor/backend.err.log`,
  },
  {
    title: "2. Como rodar a MAVIS desktop (voz, microfone, RPA)",
    body: `No seu PC:

  pip install -r requirements.txt
  playwright install chromium
  python sexta-feira.py

Pré-requisitos:
  - Python 3.10+
  - PortAudio: Linux 'sudo apt install portaudio19-dev'; macOS 'brew install portaudio'
  - Microfone e alto-falantes ativos
  - credenciais.json do Google (veja seção 5) — opcional`,
  },
  {
    title: "3. Comandos de voz suportados",
    body: `SISTEMA: "qual a bateria", "uso de CPU", "RAM", "trava o PC"
COMPUTADOR: "abre Chrome", "fecha Spotify", "tira print"
VISÃO: "olha a tela", "o que tem na tela"
GOOGLE: "minha agenda hoje", "agenda da semana", "marca reunião X", "tenho email"
WHATSAPP: "mensagens não lidas", "manda mensagem pro Pedro: ..."
MEMÓRIA: "lembra disso: X", "me lembra de Y amanhã às 8h", "quais meus lembretes"
MÍDIA: "play música", "pausa", "próxima música"
INFORMAÇÃO: "notícias", "manchetes", "clima hoje", "vai chover"
ROTAS LEGADAS: "aprender rotas", "atualizar planilha", "gerar relatório"
CUSTOM: cadastre em /commands (regex → resposta instantânea)`,
  },
  {
    title: "4. Agent Mode (NOVO v4.3) — Autônomo",
    body: `Acesse /agent. Dê uma meta complexa, a MAVIS:

  1. Planeja com Gemini quais ferramentas chamar (até 6 passos)
  2. Executa cada uma sequencialmente
  3. Sintetiza resposta final usando os outputs

Tem 21 ferramentas: calendar_today, calendar_week, gmail_summary, gmail_unread, weather,
news_headlines, web_search, analytics_kpis, analytics_weekly, analytics_monthly, list_reports,
search_routes, system_info, list_facts, list_reminders, knowledge_ask, summarize_text,
forex, add_reminder, add_note, no_op.

Exemplos prontos no botões da página.`,
  },
  {
    title: "5. Como configurar TUDO pelo painel",
    body: `Configuração → Editor .ENV: 15 campos editáveis (chave Gemini, voz, personalidade,
  km/L, R$/L, FieldControl, WhatsApp, hora auto-weekly, etc). Sensíveis mascarados.
Configuração → Personalidade: corporativa | casual | sarcástica
Configuração → Voz: 5+ vozes neurais Edge TTS testáveis
Configuração → Google Credenciais: upload de credenciais.json
Comandos: cadastre regex → resposta personalizada (instantâneo, sem custo Gemini)
Workflows: builder visual de sequências
Knowledge Base: upload PDFs e pergunte
Productivity: Pomodoro, Notes, Todos
Analytics: KPIs/gráficos automáticos dos relatórios`,
  },
  {
    title: "6. Habilitar Google APIs (Calendar/Gmail/Drive/Sheets)",
    body: `1. console.cloud.google.com → criar projeto "MAVIS"
2. APIs e Serviços → Biblioteca → habilitar:
     Google Calendar API · Gmail API · Google Drive API · Google Sheets API
3. Tela de consentimento OAuth → External → preencha
     Test users: ADICIONE SEU EMAIL (senão Google bloqueia)
4. Credenciais → ID do cliente OAuth → Aplicativo para computador → criar
5. Download JSON
6. Painel → Configuração → Google Credenciais → CARREGAR credenciais.json
7. Rode 'python sexta-feira.py' no PC uma vez → consentimento OAuth
8. Token salvo em google_token.json

Escopos: calendar (RW), gmail.modify, gmail.send, drive.readonly, spreadsheets`,
  },
  {
    title: "7. Resumo Semanal Automático",
    body: `Toda SEXTA às 18h (configurável: MAVIS_AUTO_WEEKLY_HOUR no .env), MAVIS:

1. Lê estatísticas da semana via analytics
2. Gemini gera resumo executivo narrativo
3. Salva como relatório "AUTO YYYY-Sxx"
4. Aparece em Relatórios + nos gráficos do Analytics

Desligar: .env → MAVIS_AUTO_WEEKLY=0
Forçar agora: botão "RESUMO SEMANAL AGORA" na página Relatórios
ou POST /api/reports/auto-weekly`,
  },
  {
    title: "8. Analytics Dashboard",
    body: `Página /analytics extrai automaticamente dos seus relatórios + 267 rotas KM:

  - Total KM, dias úteis, médias dia/semana
  - Litros estimados, R$ combustível (configurável km/L e R$/L)
  - Bar chart KM por semana (12 semanas)
  - Pie chart tipos de atividade (preventivas, atendimentos, entregas, trocas)
  - Bar chart + cards mensais clicáveis (modal com detalhe dia-a-dia)
  - Mapa de calor por dia da semana
  - Top 10 destinos + Top 8 equipamentos
  - Line chart KM diário (30 dias)

Sem usar quota LLM — parser regex inteligente confronta texto com lista de unidades do banco.`,
  },
  {
    title: "9. Modo Proativo (desktop)",
    body: `Em .env: MAVIS_PROATIVO=1
Loop em background que avisa por voz:
- Lembretes vencidos
- Bateria <20% sem carregador
- Próxima reunião do Calendar em 15 min

Customizar em mavis/skills/proactive.py`,
  },
  {
    title: "10. Importar relatórios antigos em massa",
    body: `POST /api/reports/import:
  { "items": [{ "periodo": "DD/MM/YYYY a DD/MM/YYYY", "conteudo_relatorio": "..." }, ...] }

Ou via página Relatórios → ADICIONAR (texto manual).
Quanto mais relatórios, mais ricos ficam os gráficos do Analytics.`,
  },
  {
    title: "11. Code Lab / Document Tools / Research / Knowledge",
    body: `Code Lab (/code): gerar, explicar, revisar, refatorar, converter, debug, executar Python
  em sandbox (subprocess + timeout 8s + bloqueio de subprocess/socket/ctypes/shutil).

Document Tools (/document): resumir (3 modos), traduzir (7 idiomas), reescrever (5 tons),
  pontos-chave, sentimento, compor email.

Research (/research): MAVIS gera 4 subqueries → busca web cada uma → sintetiza dossier
  executivo com fontes.

Knowledge Base (/knowledge): upload PDF/TXT/MD → chunking ~220 palavras (pypdf) → busca
  keyword → top-6 chunks → Gemini sintetiza com citações [fonte #chunk].`,
  },
  {
    title: "12. Workflows + Productivity + Finance",
    body: `Workflows (/workflows): builder visual de macros. 12 actions, interpolação {{label}}
  entre passos. Histórico de execuções.

Productivity (/productivity): Pomodoro com timer real (15/25/45/60min) + log persistente +
  stats 7d. Quick Notes com tags. Todos com 3 prioridades.

Finance (/finance): cotações sem API key (USD/EUR/GBP/BTC/ETH via awesomeapi + Bitcoin
  CoinGecko). Simulador empréstimo Price + juros compostos com aporte mensal.`,
  },
  {
    title: "13. Backup & Restore",
    body: `Tudo em JSON na raiz /app/:
  banco_de_dados.json, banco_relatorios.json, memoria_mavis.json, long_memory.json,
  reminders.json, todos.json, quick_notes.json, workflows.json, custom_commands.json,
  pomodoro_log.json, workflow_runs.json

Backup: zip esses arquivos. Restore: cole de volta + reinicie backend.
.env tem backup automático em .env.bak a cada save pelo painel.`,
  },
  {
    title: "14. Solução de problemas",
    body: `❌ Google "app not verified": adicione seu email em Test users da OAuth consent screen
❌ portaudio.h not found: Linux 'sudo apt install portaudio19-dev'
❌ TTS retorna 403: 'pip install -U edge-tts' (>= 7.0)
❌ Gemini "Rate limit": free tier = 5 req/min, aguarde 60s
❌ WhatsApp não abre: 'playwright install chromium' + escanear QR uma vez
❌ Painel mostra OFFLINE: verifique 'sudo supervisorctl status' e logs
❌ Voz não toca no browser: permitir áudio do site no Chrome/Firefox
❌ Agent Mode plano vazio: Gemini retornou JSON inválido — tente meta mais clara`,
  },
  {
    title: "15. Endpoints REST principais",
    body: `Health: GET /api/health · /api/status · /api/config (GET/PATCH)
Chat: POST /api/chat · /api/agent/run (autônomo) · /api/agent/tools
Voz: POST /api/tts · GET /api/tts/voices
Memória: /api/memory · /api/long-memory (CRUD)
Lembretes: /api/reminders (CRUD) · /api/reminders/natural
Rotas: /api/routes (CRUD)
Relatórios: /api/reports (CRUD) · /api/reports/import · /api/reports/auto-weekly
Analytics: /api/analytics/kpis · weekly · monthly · daily · heatmap · activities · month/{YYYY-MM}
Code Lab: /api/code/{generate,explain,review,refactor,convert,debug,execute}
Document: /api/doc/{summarize,translate,rewrite,key-points,sentiment,compose-email}
Research: POST /api/research
Knowledge: /api/knowledge/documents (CRUD + upload) · /api/knowledge/ask
Workflows: /api/workflows (CRUD) · /api/workflows/{id}/run · /api/workflows/runs
Finance: /api/finance/{forex,multi,crypto,loan,compound}
Productivity: /api/notes (CRUD) · /api/todos (CRUD+toggle) · /api/pomodoro/{log,stats}
Custom: /api/custom-commands (CRUD)
Config: /api/env/items · /api/env/update · /api/google/credentials (upload)
Vision: POST /api/vision/analyze (multipart)
Google: /api/google/{status,calendar/today,calendar/week,gmail/unread,gmail/send,drive/recent,drive/search}
Sistema: /api/system/info · /api/news · /api/weather · /api/skills
Logs: GET /api/logs · WebSocket /api/logs/stream`,
  },
];

export default function Docs() {
  return (
    <div className="p-6 space-y-4 max-w-5xl">
      <div>
        <h1 className="font-display text-3xl">Documentação</h1>
        <p className="text-zinc-500 text-xs tracking-widest uppercase mt-1">
          // MANUAL OPERACIONAL · COMANDOS · CONFIGURAÇÃO
        </p>
      </div>

      {SECTIONS.map((s, i) => (
        <div key={i} className="panel">
          <div className="panel-header">
            <span className="flex items-center gap-2">
              <Book size={12} className="text-amber" /> {s.title}
            </span>
          </div>
          <pre className="p-5 whitespace-pre-wrap text-sm leading-relaxed text-zinc-200 font-mono">
            {s.body}
          </pre>
        </div>
      ))}

      <div className="panel p-4 text-[11px] text-zinc-500">
        <span className="text-amber tracking-widest uppercase">// SOBRE</span> MAVIS / Sexta-feira v4.3 — IA pessoal modular construída sobre Gemini 2.5 Flash, Edge TTS, Vosk, openWakeWord, Playwright, Google APIs e psutil. Painel web React + FastAPI. App desktop em Python. 23 páginas, ~80 endpoints REST + WebSocket. Agent Mode autônomo com 21 ferramentas. Open source no seu PC.
      </div>
    </div>
  );
}
