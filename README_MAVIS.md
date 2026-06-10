# MAVIS / SEXTA-FEIRA v4.3 — Manual Completo

IA pessoal modular: voz neural, visão computacional, controle do PC, Google ecosystem,
WhatsApp, lembretes, memória persistente, code lab, document tools, research, knowledge
base, workflows, productivity, finance, analytics dashboard, **agent mode autônomo**.

---

## 1. Arquitetura

| Camada | Onde roda | Função |
|---|---|---|
| **App Desktop** (`sexta-feira.py`) | Seu PC | Voz, microfone, controle mouse/teclado, tela, todas as skills |
| **Painel Web** (FastAPI + React) | Container ou seu PC | Dashboard, chat, todas as ferramentas, configuração |
| **Pacote `mavis/`** | Compartilhado | 20+ módulos · core + skills |

Arquivos JSON em `/app/` são fonte única (lidos por ambos os lados): `banco_de_dados.json`,
`banco_relatorios.json`, `memoria_mavis.json`, `long_memory.json`, `reminders.json`,
`todos.json`, `quick_notes.json`, `workflows.json`, `custom_commands.json`,
`pomodoro_log.json`, `workflow_runs.json`, `kb_index.json`.

## 2. Instalação no PC

```bash
git clone <repo> mavis && cd mavis
pip install -r requirements.txt
playwright install chromium
python sexta-feira.py
```

**Pré-requisitos**:
- Python 3.10+
- PortAudio: Linux `sudo apt install portaudio19-dev` · macOS `brew install portaudio`
- Chrome instalado (WhatsApp/FieldControl via Playwright)
- credenciais.json do Google (opcional, veja §5)

## 3. Configuração — backend/.env

Editável pelo painel em **Configuração → Editor .ENV** (18 campos):

```
CHAVE_GEMINI=AIzaSy...
GEMINI_MODEL=gemini-2.5-flash
NOME_IA=Sexta-feira
VOZ_SINTETIZADOR=pt-BR-ThalitaNeural
PAUSE_THRESHOLD=1.0
MAVIS_PERSONALITY=corporativa     # corporativa | casual | sarcastica
MAVIS_PROATIVO=1
MAVIS_AUTO_WEEKLY=1               # auto resumo toda sexta
MAVIS_AUTO_WEEKLY_HOUR=18
MAVIS_KM_PER_LITER=10
MAVIS_FUEL_COST=5.89
FIELDCONTROL_EMAIL=...
FIELDCONTROL_SENHA=...
WHATSAPP_NUMERO=5511...
WHATSAPP_GRUPO=...
PLANILHA_NOME=...
WAHA_URL=http://localhost:3001    # WhatsApp HTTP API (devlikeapro/waha)
WAHA_API_KEY=mavis123             # X-Api-Key dos requests
WAHA_SESSION=default              # nome da sessão WhatsApp
```

Backup automático em `.env.bak` antes de cada save pelo painel.

## 4. Páginas do Painel (24 áreas)

| Rota | Função |
|---|---|
| `/` | Overview com KPIs, logs live, últimos relatórios |
| `/agent` | **Agent Mode** — meta autônoma com 21 ferramentas |
| `/analytics` | Dashboard de KM, custo combustível, mapa de calor, top destinos |
| `/chat` | Chat com Gemini + TTS browser + ditado por voz |
| `/commands` | Comandos personalizados (regex → resposta instantânea) |
| `/code` | Code Lab — gerar/explicar/revisar/refatorar/converter/debug/executar Python |
| `/document` | Resumir, traduzir, reescrever, sentimento, compor email |
| `/research` | Dossier multi-step (subqueries → web → síntese) |
| `/knowledge` | Knowledge Base (upload PDF/TXT/MD + Q&A com fontes) |
| `/workflows` | Macros visuais com interpolação `{{label}}` |
| `/productivity` | Pomodoro + Quick Notes + Todos |
| `/finance` | Cotações (USD/EUR/BTC) + calc empréstimo + juros compostos |
| `/vision` | Upload de imagem → análise Gemini Vision |
| `/routes` | CRUD do banco de 267 rotas KM |
| `/reports` | CRUD de relatórios + auto-weekly + import em massa |
| `/memory` | Memória curta de conversa |
| `/long-memory` | Fatos persistentes por categoria |
| `/reminders` | Lembretes + criação por linguagem natural |
| `/google` | Status OAuth + agenda + emails + drive |
| `/skills` | Catálogo + telemetria CPU/RAM/disco/clima + manchetes |
| `/logs` | Stream em tempo real (WebSocket) |
| `/docs` | Esta documentação dentro do app |
| `/settings` | Editor .env + personalidade + voz + upload credenciais.json |

## 5. Google Cloud Console — Passo-a-passo

1. **console.cloud.google.com → Novo projeto** "MAVIS"
2. **APIs e Serviços → Biblioteca** — habilitar:
   - Google Calendar API
   - Gmail API
   - Google Drive API
   - Google Sheets API
3. **Tela de consentimento OAuth → External**
   - Preencha nome do app, email
   - **Test users**: ADICIONE SEU EMAIL (crítico, senão Google bloqueia)
4. **Credenciais → + Criar credenciais → ID do cliente OAuth**
   - Tipo: **Aplicativo para computador**
   - Nome: "MAVIS Desktop"
   - **Download JSON**
5. **No painel → Configuração → Google Credenciais → CARREGAR credenciais.json**
6. Rode `python sexta-feira.py` uma vez no PC → navegador abrirá → consentimento → token salvo

**Escopos**: calendar (RW), gmail.modify+send, drive.readonly, spreadsheets

## 6. Comandos de Voz

| Categoria | Exemplos |
|---|---|
| Sistema | "qual a bateria", "uso de CPU", "RAM", "trava o PC" |
| Computador | "abre Chrome", "fecha Spotify", "tira print" |
| Visão | "olha a tela", "o que tem na tela" |
| Google | "minha agenda hoje", "marca reunião amanhã 14h", "tenho email" |
| WhatsApp | "mensagens não lidas", "manda mensagem pro Pedro: ..." |
| Memória | "lembra disso: X", "me lembra de Y amanhã às 8h" |
| Mídia | "play música", "pausa", "próxima música" |
| Info | "notícias", "manchetes", "clima hoje" |
| Legado | "aprender rotas", "atualizar planilha", "gerar relatório" |
| Custom | qualquer regex que você cadastrar em `/commands` |

## 7. Agent Mode (v4.3 NOVO)

`/agent`: dê uma meta complexa, a MAVIS planeja com Gemini, executa até 6 ferramentas
sequencialmente e sintetiza resposta final. **21 ferramentas disponíveis**:

`calendar_today`, `calendar_week`, `gmail_summary`, `gmail_unread`, `weather`,
`news_headlines`, `web_search`, `analytics_kpis`, `analytics_weekly`, `analytics_monthly`,
`list_reports`, `search_routes`, `system_info`, `list_facts`, `list_reminders`,
`knowledge_ask`, `summarize_text`, `forex`, `add_reminder`, `add_note`, `no_op`.

Exemplos prontos: "Faz um briefing executivo do meu dia", "Resume o que rodei essa semana",
"Investiga: equipamentos com maior taxa de falha em 2026".

## 8. Auto Resumo Semanal

Toda **sexta às 18h** (configurável via `MAVIS_AUTO_WEEKLY_HOUR`), MAVIS roda automaticamente:
1. Lê stats da semana via `analytics.weekly_series()`
2. Gemini gera texto narrativo executivo
3. Salva como relatório `"AUTO YYYY-Sxx"`

Forçar manualmente: **Relatórios → RESUMO SEMANAL AGORA** ou `POST /api/reports/auto-weekly`.

## 9. Endpoints REST (~80)

Ver seção 15 da página `/docs` no painel. Principais:
- Chat/Agent: `/api/chat`, `/api/agent/run`, `/api/agent/tools`
- Analytics: `/api/analytics/{kpis,weekly,monthly,daily,heatmap,activities,month/{YYYY-MM}}`
- Config: `/api/env/items`, `/api/env/update`, `/api/google/credentials` (upload)
- Reports: `/api/reports`, `/api/reports/import`, `/api/reports/auto-weekly`
- Code: `/api/code/{generate,explain,review,refactor,convert,debug,execute}`
- Doc: `/api/doc/{summarize,translate,rewrite,key-points,sentiment,compose-email}`
- Research/KB: `/api/research`, `/api/knowledge/{documents,ask}`
- Workflows: `/api/workflows`, `/api/workflows/{id}/run`
- Productivity: `/api/notes`, `/api/todos`, `/api/pomodoro/{log,stats}`
- Finance: `/api/finance/{forex,multi,crypto,loan,compound}`
- Custom Commands: `/api/custom-commands` CRUD
- Google: `/api/google/{status,calendar,gmail,drive}`
- Vision: `/api/vision/analyze` (multipart)
- Sistema: `/api/system/info`, `/api/news`, `/api/weather`, `/api/skills`
- Logs: `/api/logs`, WebSocket `/api/logs/stream`

## 10. Backup & Restore

Tudo em `/app/*.json`. Backup = zip. Restore = colar de volta + restart backend.
`.env.bak` é gerado automaticamente a cada save pelo painel.

## 11. Troubleshooting

| Sintoma | Solução |
|---|---|
| Google "app not verified" | Adicione seu email em Test users da OAuth consent screen |
| `portaudio.h not found` | Linux `sudo apt install portaudio19-dev` |
| TTS 403 | `pip install -U edge-tts` (>= 7.0) |
| Rate limit Gemini | Free tier 5 req/min, aguarde 60s |
| WAHA `OFFLINE` no painel | `docker compose up -d waha` e escaneie o QR em `http://localhost:3001` (dashboard `admin / ver docker-compose.yml`) |
| Painel OFFLINE | Verifique `sudo supervisorctl status` e logs |
| Voz não toca | Permitir áudio do site no browser |
| Agent plano vazio | Gemini retornou JSON inválido — meta mais clara |

## 13. WhatsApp via WAHA (NOVO em v4.4)

WhatsApp agora roda 100% por **WAHA** (devlikeapro/waha) em background — sem Playwright, sem janela aberta. Configurado em `docker-compose.yml`:

```bash
docker compose up -d waha          # sobe o container na porta 3001
# 1ª vez: abre http://localhost:3001, faz login admin/<senha do compose>,
#         clica "Start" na sessão default e escaneia o QR no celular
```

Endpoints do painel que falam com o WAHA:
- `GET  /api/whatsapp/status`     → estado da sessão (WORKING, STARTING, STOPPED…)
- `GET  /api/whatsapp/unread`     → chats com mensagens não-lidas
- `POST /api/whatsapp/send`       → envio de texto por nome/grupo/favorito
- `POST /api/analytics/export-pdf` (com `send_to_id`) → envia o PDF macro pelo WAHA

Variáveis em `backend/.env`: `WAHA_URL`, `WAHA_API_KEY`, `WAHA_SESSION`.

O envio dos **auto-resumos semanal e mensal** vai automaticamente pelo WAHA quando você marcar "send_whatsapp" no auto_report_config (não precisa mais de `DESKTOP_MODE=1`).

## 12. Estrutura de pastas

```
/app
├── mavis/
│   ├── core/         brain, long_memory, reminders, router, paths, storage
│   └── skills/       computer, vision, system_info, google_*, whatsapp,
│                     scheduler, proactive, wake_word, news_weather,
│                     code_assistant, python_sandbox, document_tools, research,
│                     finance, productivity, workflows, knowledge, analytics,
│                     env_manager, custom_commands, auto_report, agent
├── sexta-feira.py    Desktop loop voz
├── rotinas.py        Legado FieldControl/Relatórios/Planilhas
├── relatorios.py · planilhas.py · aprender_rotas.py
├── backend/          FastAPI server.py + .env
├── frontend/         React + Tailwind + Recharts
└── *.json            Estado persistente
```

---

Última atualização: Jun 2026 · MAVIS v4.3
