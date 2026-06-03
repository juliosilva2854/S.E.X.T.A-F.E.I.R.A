# S.E.X.T.A - F.E.I.R.A (MAVIS) — Personal AI Assistant

## Problema Original
Sistema de IA pessoal em Python já existente (J.A.R.V.I.S.-like) com voz neural, reconhecimento de voz Vosk, integração WhatsApp Web, RPA FieldControl/Playwright, Google Sheets, banco de rotas KM.

Pedido evoluiu em 3 fases:
- v2.0: análise completa + Painel Web + correção de bugs
- v3.0: IA "extremamente avançada" — manipulação do computador, leitura de tela, ecossistema Google completo, WhatsApp bidirecional, conversa estável, lembretes, modo proativo, vision computacional, wake word, personalidade configurável

## Arquitetura Final (v3.0)

### Pacote compartilhado `/app/mavis/`
- `mavis/core/brain.py` — Cérebro Gemini 2.5-flash, multimodal (text+image), smart_extract para parse JSON estruturado, 3 personalidades (corporativa/casual/sarcastica), tratamento de rate-limit
- `mavis/core/long_memory.py` — Fatos persistentes sobre o operador (categorias: pessoal, preferência, trabalho, contato, lugar, agenda, outro)
- `mavis/core/reminders.py` — Lembretes/alarmes
- `mavis/core/router.py` — Roteamento de intenções via regex (40+ patterns: sistema, computador, visão, whatsapp, google, mídia, notícias, clima, memória, rotas)
- `mavis/core/storage.py` — Escrita atômica de JSON
- `mavis/core/paths.py` — Caminhos centrais (lê do .env)

### Skills
- `skills/computer.py` — PyAutoGUI (type, click, hotkey, open/close app, lock, shutdown, media keys, clipboard)
- `skills/vision.py` — Captura screenshot (mss) + análise via Gemini Vision
- `skills/system_info.py` — psutil (bateria, CPU, RAM, disco)
- `skills/google_auth.py` — OAuth2 compartilhado (Calendar, Gmail, Drive, Sheets)
- `skills/google_calendar.py` — Listar agenda hoje/semana, criar evento, frase falável
- `skills/google_gmail.py` — Listar não-lidos, ler, marcar como lido, enviar, resumir
- `skills/google_drive.py` — Buscar arquivos, listar recentes
- `skills/whatsapp.py` — Playwright (ler não-lidos, enviar mensagem)
- `skills/scheduler.py` — APScheduler background (lembretes)
- `skills/proactive.py` — Loop que dispara avisos: lembretes vencidos, bateria <20%, reunião em 15min
- `skills/wake_word.py` — openWakeWord (modelo padrão `hey_jarvis_v0.1`, ou custom)
- `skills/news_weather.py` — Manchetes RSS (G1/UOL/Tecmundo) + Open-Meteo (sem API key)

### Backend FastAPI (`/app/backend/server.py`)
~40 endpoints organizados:
- **Health/Status/Config**: `/health`, `/status`, `/config` (GET/PATCH personality)
- **Chat**: `/chat` (intent routing + skill execution + brain response)
- **Vision**: `/vision/analyze` (multipart upload)
- **TTS**: `/tts`, `/tts/voices`
- **Memória curta**: `/memory` (GET/DELETE)
- **Memória longa**: `/long-memory` (CRUD)
- **Lembretes**: `/reminders` (CRUD), `/reminders/natural` (LLM parse), `/reminders/{id}/done`
- **Rotas**: `/routes` (CRUD)
- **Relatórios**: `/reports` (CRUD)
- **Google**: `/google/status`, `/google/calendar/today`, `/google/calendar/week`, `/google/gmail/unread`, `/google/gmail/message/{id}`, `/google/gmail/send`, `/google/drive/recent`, `/google/drive/search`
- **Skills**: `/skills`, `/system/info`, `/news`, `/weather`
- **Comandos**: `/commands/execute`
- **Logs**: `/logs`, `/logs/stream` (WebSocket)

### Frontend React (12 páginas)
Tema "Tactical Command Center" (industrial brutalist, JARVIS-style):
1. **Overview** — Hero + stats (rotas, memórias, relatórios, status) + logs live + últimos relatórios
2. **Chat Neural** — Conversação com TTS no browser + ditado por Web Speech API
3. **Visão** — Upload de imagem + Gemini Vision
4. **Banco de Rotas** — CRUD com busca (267 rotas)
5. **Relatórios** — Lista, preview, copiar, criar manual
6. **Memória Curta** — Histórico de conversa
7. **Memória Longa** — Fatos persistentes agrupados por categoria
8. **Lembretes** — CRUD + criação por linguagem natural
9. **Google Hub** — Status OAuth + agenda + emails não-lidos + drive recentes + instruções inline do Cloud Console
10. **Skills** — Catálogo de skills + telemetria (CPU/RAM/Disco/Clima) + manchetes
11. **Logs Stream** — WebSocket tempo real
12. **Configuração** — 3 personalidades + 5 vozes Edge TTS testáveis

### App Desktop (`/app/sexta-feira.py`)
Loop: ouve voz → STT (Google) → router.match_intent → execute_skill_local OU brain.chat_text → TTS Edge → fala
- Re-agenda lembretes pendentes no startup
- Modo proativo em thread background
- Mantém compatibilidade com rotinas.py legacy (FieldControl)

### Documentação
- `README_MAVIS.md` — Setup completo, passo-a-passo Google Cloud Console (criar projeto → habilitar 4 APIs → consent screen → OAuth Desktop App → download credenciais.json → primeiro consentimento), lista de comandos de voz, estrutura de pastas, troubleshooting

## Persona / Operador
Júlio Cesar — usuário corporativo (engenharia/manutenção ToLife). Quer um JARVIS pessoal eficiente.

## Implementado nesta sessão (v3.0, 2026-06-03)
- 40+ endpoints novos no backend FastAPI
- 5 páginas novas no frontend
- Pacote modular `mavis/` (15 módulos)
- Cérebro com multimodal vision + smart_extract estruturado
- 3 personalidades alternáveis
- Memória de longo prazo (fatos)
- Lembretes com APScheduler + parser natural
- Sistema info (CPU/RAM/disco/bateria)
- Notícias RSS + clima Open-Meteo (zero API keys)
- Google ecosystem completo (Calendar/Gmail/Drive/Sheets)
- WhatsApp bidirecional via Playwright
- Wake word (openWakeWord)
- Modo proativo background
- sexta-feira.py refatorado para usar o pacote mavis
- README_MAVIS.md com passo-a-passo Cloud Console

## Testing
- **Iteration 1**: backend 19/19 + frontend 100%
- **Iteration 2**: backend 19/22 (3 falhas = rate limit Gemini free tier 5RPM, confirmadas funcionais com retry) + frontend 100% (todas 12 rotas)
- Hardening: smart_extract agora propaga `RATE_LIMIT` distintamente; endpoint `/reminders/natural` retorna HTTP 429 com mensagem clara

## Roadmap / Backlog
- **P1**: WebSocket bidirecional para acionar comandos do desktop pelo painel em tempo real
- **P1**: PWA / mobile responsive
- **P2**: Tags + busca full-text nos relatórios
- **P2**: Gráficos semanais (KM rodados, emails, eventos)
- **P2**: Treinar modelo wake word custom "sexta-feira" (openWakeWord)
- **P2**: PIN/auth simples se exposto fora do localhost
- **P3**: Spotify integration via OAuth (já tem media keys, mas Spotify Web API daria controle fino)
- **P3**: WhatsApp business API (mais robusto que Web Playwright)
- **P3**: Splitar `server.py` em routers separados por domínio quando ultrapassar 1500 LOC

## Como Rodar
- **Backend e Frontend**: gerenciados por supervisor (`sudo supervisorctl status`)
- **Desktop**: instalar `requirements.txt` (com PortAudio) + `playwright install chromium`, depois `python3 sexta-feira.py`
- **Google APIs**: seguir `README_MAVIS.md` seção 3
