# S.E.X.T.A - F.E.I.R.A (MAVIS) — Personal AI Assistant

## Problema Original
Sistema de IA pessoal em Python já existente (J.A.R.V.I.S.-like) com voz neural, reconhecimento de voz Vosk, integração WhatsApp Web, RPA FieldControl/Playwright, Google Sheets, banco de rotas KM. Usuário pediu análise completa, melhorias gerais, correção de bugs e construção de um Painel Web de controle.

## Arquitetura

### Camada Desktop (Python — local na máquina do usuário)
- `sexta-feira.py` — loop principal voz (Vosk STT + Edge TTS + Gemini)
- `relatorios.py` — RPA Playwright extrai dados do FieldControl + envia resumos via WhatsApp Web
- `planilhas.py` — preenche KM faltante em planilha Google Sheets
- `rotinas.py` — roteador de comandos (sites, protocolos, relatórios)
- `aprender_rotas.py` — popula banco_de_dados.json a partir de planilha
- `config.py` — centraliza configs (lê de backend/.env)

### Camada Web (Painel de Controle — Container Emergent)
- **Backend** `/app/backend/server.py` — FastAPI exposing:
  - `/api/health`, `/api/status`, `/api/config`
  - `/api/chat` (Gemini 2.5-flash via google-genai usando chave do usuário)
  - `/api/tts` + `/api/tts/voices` (Edge TTS — Thalita Neural pt-BR, gratuito)
  - `/api/memory` (GET/DELETE) — sincronizado com memoria_mavis.json
  - `/api/routes` (GET/POST/PUT/DELETE) — sincronizado com banco_de_dados.json
  - `/api/reports` (GET/POST/DELETE) — sincronizado com banco_relatorios.json
  - `/api/logs` + WebSocket `/api/logs/stream` — feed em tempo real
  - `/api/commands/execute` — orquestrador (operações RPA pesadas continuam no desktop)

- **Frontend** `/app/frontend` React + Tailwind — tema "Tactical Command Center" (JARVIS-style industrial brutalist):
  - Overview (hero + stats + logs live + relatórios)
  - Chat Neural (com TTS no browser e Web Speech API ditado por voz)
  - Banco de Rotas (CRUD com busca)
  - Relatórios (lista, preview, copiar, criar manual)
  - Memória (visualização e limpeza)
  - Logs Stream (WebSocket em tempo real)
  - Configuração (vozes Edge TTS testáveis + status do sistema)

### Compartilhamento Desktop ↔ Web
Os três arquivos JSON (`memoria_mavis.json`, `banco_de_dados.json`, `banco_relatorios.json`) ficam em `/app` e são lidos/escritos pelos dois lados de forma atômica (`*.tmp` + `os.replace`).

## Persona / Operador
Júlio Cesar — usuário corporativo (engenharia/manutenção ToLife). Quer um JARVIS pessoal eficiente, voz feminina premium, tom corporativo, sem emojis.

## Decisões Chave
- Mantida chave Gemini própria do usuário (Gemini 2.5 Flash) — sem Emergent LLM Key.
- Edge TTS Thalita Neural (pt-BR) — voz neural gratuita, sem custo extra.
- Sem autenticação no painel (uso pessoal, escolha do usuário).
- Credenciais removidas dos `.py` hardcoded → movidas para `backend/.env`.
- `config.py` central lê do `.env` (compatibilidade com módulos desktop).

## Implementado nesta sessão (2026-06-03)
- Backend FastAPI completo (15 endpoints) — `server.py`
- Frontend React (7 páginas + layout) — Tactical Command Center theme
- Refatoração `config.py` para usar `python-dotenv` + `os.environ`
- Refatoração `config_exemplo.py` (template seguro)
- `.gitignore` com proteção de credenciais e cache do WhatsApp
- TTS Edge atualizado para v7.2.8 (corrige erro 403 da v6)
- Saneamento de `memoria_mavis.json` (removeu 6 tags `[ESPERAR]` residuais)
- Future flags do React Router v7 (suprime warnings)
- Testing agent: 19/19 backend + frontend integrado 100% verde

## Roadmap / Backlog
- **P1**: WebSocket bidirecional para enviar comandos do painel ao desktop em tempo real (hoje os RPAs rodam apenas no desktop por exigirem `credenciais.json` Google + navegador visual).
- **P1**: PWA / mobile responsive — operar o painel pelo celular.
- **P2**: Sistema de tags para relatórios + busca textual full-text.
- **P2**: Gráfico de KM rodados por semana (já temos os dados nos relatórios).
- **P2**: Autenticação simples (PIN) caso o painel seja exposto fora do localhost.
- **P3**: Exportar memória/relatórios para PDF.
- **P3**: Integração com agenda Google (já tem oauth2client).

## Como Rodar
- Backend e Frontend: gerenciados por supervisor (`sudo supervisorctl status`).
- Desktop: `python3 sexta-feira.py` na máquina do usuário (precisa de PortAudio/microfone).
