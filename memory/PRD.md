# S.E.X.T.A - F.E.I.R.A (MAVIS) — Status / PRD

## Pedido do usuário
Assistente pessoal full-stack (React + FastAPI + MongoDB) de Julio Cesar, técnico de campo
da ToLife em UPAs/AMAs/hospitais na Grande São Paulo.

## Stack
- Backend: FastAPI (1.724 LOC) + MongoDB + Gemini 2.5 Flash + APScheduler + edge-tts
- Frontend: React CRA (5.315 LOC) + Tailwind + Recharts + Leaflet vanilla + @phosphor-icons/react
- Pacote `mavis/` (8.151 LOC Python total): core (brain, router, long_memory, reminders, storage)
  + 30+ skills (agent, analytics, computer, vision, whatsapp, google_*, code_assistant,
  document_tools, research, knowledge, finance, productivity, workflows, etc.)
- Desktop loop voz: `sexta-feira.py` (wake word + Vosk PT-BR + edge-tts ThalitaNeural)
- Dados: 267 rotas KM + 5 relatórios + 20 unidades geolocalizadas + favoritos WhatsApp

## URL preview atual
https://mavis-cloud.preview.emergentagent.com

## O que foi feito

### 10/06/2026 (parte 5) — Google OAuth NATIVO (zero Emergent) + painel Acesso
- **Removida a dependência da Emergent no login Google.** Agora é OAuth 2.0 nativo (Authorization Code): o backend troca o `code` direto em `oauth2.googleapis.com/token` e lê o e-mail em `googleapis.com/oauth2/v2/userinfo`. Credenciais próprias do usuário em `backend/.env` (`GOOGLE_CLIENT_ID`/`GOOGLE_CLIENT_SECRET`, client Web do projeto `mavis-system`). Redirect dinâmico `window.location.origin + /auth/google`. `/api/auth/config` expõe `google_enabled` + `google_client_id`.
- **Frontend**: `Login.jsx` monta a URL de consentimento do Google (scope `openid email profile`, `state` p/ CSRF); rota `/auth/google` (`AuthCallback`) troca o code via `POST /api/auth/google {code, redirect_uri}`. Botão Google só aparece se `google_enabled`.
- **Painel "Acesso"** (`/access`, item na sidebar): gerencia a allowlist de e-mails Google (add/remove) e mostra "Últimos acessos" (`GET /api/users`, campo `last_login` gravado em cada login). Aviso visual quando em modo local.
- Verificado: Google retorna a tela de consentimento correta para `ia.sconnecta.com.br` e o preview (redirect URIs OK). Login por senha segue 100% independente.


- **Flag `IS_CLOUD`** (`backend/.env`): `false`=local (painel 100% aberto, sem login — automação desktop intacta); `true`=nuvem (painel admin exige login). Default `false`.
- **Guard condicional** (`cloud_auth_guard` middleware em `server.py`): quando `IS_CLOUD=true`, todo `/api/*` exige sessão, EXCETO prefixos livres `/api/auth/`, `/api/public/` (token de leitura) e `/api/publish` (X-Publish-Key). `/p/analytics` continua público.
- **Auth mista** (Emergent Managed Google Auth + senha): endpoints `GET /api/auth/config`, `POST /api/auth/google` (valida allowlist), `POST /api/auth/password` (ADMIN_PASSWORD, compare_digest), `GET /api/auth/me`, `POST /api/auth/logout`. Sessão em Mongo (`user_sessions`, cookie httpOnly 7d ou Bearer). Usuários em `users` (user_id UUID, projeção `{_id:0}`).
- **Allowlist de e-mails Google**: `GET/POST/DELETE /api/allowed-emails` (Mongo `allowed_emails`). Seed automático de `SEED_ADMIN_EMAIL=julio.silva2854@gmail.com` no startup. Julio pode adicionar/remover e-mails.
- **Publish local→nuvem**: `POST /api/publish` (protegido por `X-Publish-Key`) grava `banco_de_dados/banco_relatorios/sheets_cache/geocode_cache`. `_publish_to_cloud()` envia esses arquivos para `CLOUD_PUBLISH_URL` após cada sync do Google Sheets (`/api/sheets/sync` + auto-sync). `POST /api/publish/now` dispara manualmente. Usuário fará deploy fora da Emergent (domínio próprio) → setar `CLOUD_PUBLISH_URL` no app local e `IS_CLOUD=true` no deploy.
- **Frontend**: `AuthProvider`+`ProtectedRoute` (`src/auth/AuthContext.jsx`), página `/login` (Google + senha), `AuthCallback` (troca `session_id` do fragmento), botão Sair no rodapé da sidebar (só na nuvem). `api.js` com `withCredentials:true`. CORS com `allow_origin_regex` p/ credenciais.
- **Testes**: `backend/tests/test_mixed_auth.py` (13/13 ✅) + Playwright (login/dashboard/logout/public-gate ✅). Relatório `test_reports/iteration_1.json`. Zero bugs.


### 10/06/2026 (parte 3) — Segurança do repo + Página Analytics pública (token)
- **Segurança / GitHub**: removidos do working tree `backend/.env.env.bak` (continha CHAVE_GEMINI real + senha FieldControl) e `frontend/.env.production.local`. Redigidas credenciais em `.emergent/summary.txt` e `memory/test_credentials.md`. `.gitignore` reforçado (`*.bak`, `.env.*`, `*.env.*`, `public_tokens.json`, `sheets_cache.json`). Corrigido bug do `env_manager` que gerava `.env.env.bak` (agora `.env.bak`). NOTA: a chave Gemini exposta ainda vive no HISTÓRICO do git → usuário deve ROTACIONAR a chave (AI Studio) e trocar a senha FieldControl.
- **Página pública Analytics (somente leitura + extração)**: nova skill `mavis/skills/public_access.py` (tokens guardados como hash SHA-256, brute-force: revoga após N tentativas inválidas). Endpoints: `GET /api/public/validate`, `GET /api/public/analytics/all`, `/month/{m}`, `/export` (csv/xlsx/pdf), admin `GET/POST/DELETE /api/public-tokens` + `/revoke` + `/reactivate`. Store em `public_tokens.json` (gitignored).
- **Frontend**: nova rota pública `/p/analytics?s=<id>&t=<token>` (fora do Layout, sem sidebar, badge SOMENTE LEITURA, filtros, KPIs, mapa de calor, gráficos, export). Nova página admin `/share` ("Compartilhar" na sidebar) para gerar/copiar URL/revogar/reativar/excluir links. Token exibido uma única vez na criação.
- **Validação `iniciar_tudo.bat`**: revisado estaticamente — cadeia `preparar.bat → iniciar_oculto.vbs` + `docker-compose.yml` (serviço waha) conferem. Não executável no container Linux (é batch Windows). Caveats: `npx serve` baixa o pacote na 1ª execução (precisa de internet); senha do dashboard WAHA está no docker-compose.
- **Fix ambiente**: recriados `backend/.env` e `frontend/.env` (sumiram no fork) + `DANGEROUSLY_DISABLE_HOST_CHECK=true` (resolveu "Invalid Host header").

### 10/06/2026 (parte 2) — Backlog: auto-sync Sheets + refactor Analytics
- **P3 Auto-sync diário do Google Sheets**: APScheduler agenda `google_sheets.sync_all()` em horário configurável (default 7h). Endpoints `GET /api/sheets/autosync` + `POST /api/sheets/autosync/toggle?enabled=true&hour=7` (persiste em `.env` via `env_manager` + aplica em memória sem restart). UI: badge `AUTO-SYNC: 7h/OFF` clicável no header do Analytics.
- **P1 Refactor Analytics.jsx em subcomponentes**:
  - Novo `/app/frontend/src/components/analytics/widgets.jsx` (98 LOC) — exporta `KPI`, `Panel`, `Field`, `ExportBtn`, `FieldGroup`
  - Novo `/app/frontend/src/components/analytics/KpiGrid.jsx` (43 LOC) — encapsula os 2 grids de KPI (10 cards: KM total, dias, médias, litros, custo, preventivas, atendimentos, entregas, trocas)
  - `Analytics.jsx`: **934 → 853 LOC** (≈9% redução); todos os widgets reutilizáveis em outras telas
- **`env_manager` expandido**: whitelist agora cobre `WAHA_URL/API_KEY/SESSION` + `MAVIS_SHEETS_AUTOSYNC[_HOUR]`. Alias `update_env = update` para compat.
- **Chave Gemini atualizada**: usuário forneceu `AQ.Ab8RN6JYKR16RXkawCujSDzORmf4DKfPsPGIs4NpQIRZi82x8w` — formato OAuth/Vertex AI, **não é API key padrão Gemini** (deveria ser `AIzaSy...`). Endpoint Gemini retorna 401 UNAUTHENTICATED. Aplicada no `.env` mas precisa ser substituída.

### 10/06/2026 — Chat executa comandos + Google Sheets como fonte do Analytics
- **Chat Neural EXECUTA** comandos operacionais ao invés de só responder:
  - "sincroniza/sync planilha" → `mavis.skills.google_sheets.sync_all()` (manual, on-demand)
  - "atualizar planilha" / "preencher quilometragem" → `planilhas.preencher_km_faltantes()`
  - "aprender rotas" / "estudar rotas" → `aprender_rotas.treinar_mavis()`
  - "gerar relatório" / "resumo da semana" → `relatorios.gerar_resumo()` (DESKTOP_ONLY — Playwright)
  - Comando desktop-only num host sem `credenciais.json` retorna `{desktop_only: True}` para o cérebro avisar
- **Google Sheets vira fonte primária do Analytics**:
  - Nova skill `mavis/skills/google_sheets.py` autentica em 2 níveis (OAuth do usuário → Service Account legada)
  - `sync_all()` varre TODAS as abas mensais da planilha "Planilha KM - Julio Cesar MTFL" (ID `1BkA...Sbhn4`), extrai Data/Origem/Destino/Tipo/Ticket/KM e salva em `sheets_cache.json`
  - `analytics.py::_flat_days_smart()` agora usa o cache do Sheets quando existir (estruturado, confiável) e cai pros relatórios narrativos JSON como fallback
  - "Tipo Visita" da planilha é normalizada pras atividades antigas (Preventiva → manutencao_preventiva, etc)
- **Novos endpoints**: `GET /api/sheets/status`, `POST /api/sheets/sync`, `GET /api/sheets/rows`
- **UI Analytics**: botão "SINCRONIZAR PLANILHA" (verde) no header + label "FONTE:" indicando se dados vêm do Sheets ou dos relatórios JSON
- **Router expandido**: regex de `route.legacy` agora cobre `sincronizar planilha`, `sync sheets`, `puxar planilha`, `resumo da semana`, `relatório mensal`
- **Dependências**: `gspread==6.2.1` e `oauth2client==4.1.3` adicionados ao `requirements.txt`

### 09/06/2026 — Migração WhatsApp para WAHA + Script único
- **WAHA é a API oficial agora** (Playwright aposentado). `mavis/skills/whatsapp.py` lê
  `WAHA_URL`, `WAHA_API_KEY`, `WAHA_SESSION` do `.env`; bug do `formatar_numero` ausente
  em `send_file()` corrigido.
- **Removido gate `DESKTOP_MODE=1`** em `auto_report.py` (semanal + mensal). Envios
  de WhatsApp do painel funcionam tanto local quanto hospedado.
- **Novos endpoints**: `GET /api/whatsapp/status` e `GET /api/whatsapp/unread`.
- **UI**: badge live do status WAHA (verde/vermelho) + botão "atualizar" na página `/whatsapp`.
- **Bug fix Analytics.jsx**: removido código órfão de `wa.me` que quebrava o build após
  refatoração WAHA do commit `f0542f9`.
- **Script único `scripts/iniciar_tudo.bat`**: orquestra Docker Desktop + container WAHA
  (`docker compose up -d waha`) + MongoDB + backend (uvicorn :8001) + frontend (serve :3000)
  + `sexta-feira.py` (loop de voz/wake-word), tudo em background via VBS atualizado.
  `scripts/parar_tudo.bat` agora também para o container WAHA e o processo `sexta-feira.py`.

### 03/06/2026 — Analytics + Restauração .env
- Página `/analytics` completa (KPIs, mapa de calor Leaflet, CSV/XLSX/PDF, filtros, modal mensal,
  botão Compartilhar WhatsApp). 18 testes pytest backend passando.

### 05/06/2026 — Restauração pós-fork + Opção B Windows
- `backend/.env` + `frontend/.env` recriados; supervisor ONLINE; Gemini conectado.
- 3 scripts Windows: `preparar.bat` (corrigido bug crítico do URL local), `iniciar_oculto.vbs`,
  `registrar_inicializacao.bat`. Guia `COMO_RODAR_EM_BACKGROUND.md` reescrito.

### 05/06/2026 — 5 features grandes ✅
1. **Wake-word no painel** (`<WakeWord />` plugado no Layout) + documentação do loop voz desktop
   (`sexta-feira.py`) com instruções para treinar wake-word custom "sexta-feira".
2. **WhatsApp favoritos**:
   - Nova skill `mavis/skills/whatsapp_favorites.py` (CRUD + `resolve_destination()`)
   - Endpoints `/api/whatsapp/favorites` (GET/POST/PATCH/DELETE) e `/api/whatsapp/send`
     (com `favorite_id` ou nome livre; modo desktop usa Playwright, modo hospedado retorna `wa.me`)
   - Página `/whatsapp` com listagem em cards, modal de adicionar, envio rápido, copy nome
3. **Resumo Mensal Macro**:
   - `analytics.monthly_macro(month)` com comparativo vs mês anterior, deltas %, top5 unidades,
     top3 equipamentos, tendência KM/semana, concentração top3
   - `auto_report.generate_monthly()` + narrativa Gemini focada em **OPERAÇÕES, não em
     KM/combustível** (regras explícitas no prompt)
   - PDF macro em `analytics_export.to_pdf_macro()` com tabela comparativa + insights
   - Agendamento dia 1º 8h (configurável) via APScheduler — testado: `next_run=2026-07-01 08:00`
   - Endpoints `/api/analytics/auto-monthly` GET/POST, `/run-now`, `/download/{filename}`,
     `/analytics/monthly-macro?month=YYYY-MM`
   - UI: botões "RESUMO MENSAL AGORA" + "AGENDAR MENSAL" no `/reports` com modal completo,
     listagem dos PDFs gerados, dropdown de destino padrão (favoritos)
4. **PDF com seleção de campos**:
   - `analytics_export.pdf_fields_catalog()` retorna catálogo (10 KPIs, 10 colunas, 4 seções)
   - `to_pdf(rows, kpis, filtro, fields=...)` aceita seleção
   - Endpoint `/api/analytics/pdf-fields` (catálogo) + `/api/analytics/export-pdf` (POST com
     seleção)
   - Modal em `Analytics.jsx` com 3 grupos de checkboxes (Indicadores/Colunas/Seções),
     "Restaurar padrão", contador X/Y, salva preferência no localStorage
   - Compartilhamento via modal com dropdown de favoritos (envio direto se DESKTOP_MODE=1,
     senão abre wa.me com destino selecionado)
5. **Revisão de código** (`/app/REVISAO.md`):
   - 0 vulnerabilidades (eval/exec, secrets, path traversal, datetime.utcnow, sync calls)
   - 3 erros de lint pré-existentes corrigidos (E741 ambíguo `l`, 2× E701 multi-statement)
   - Lint Python + JS: 100% limpo
   - 12 pontos bem feitos + 6 oportunidades de manutenibilidade no backlog

## Observações
- **CHAVE_GEMINI ATIVA** no preview · chat respondendo em ~1.7s
- **WAHA (devlikeapro/waha)** roda em container Docker na porta 3001 com sessão `default`
- **Restrições**: `pydantic-core==2.23.4`, `tzlocal/pytz`, cache geocoding, Leaflet vanilla (não react-leaflet)
- **Desktop-only**: RPA Field Control (Playwright legado em `relatorios.py`/`rotinas.py`). WhatsApp NÃO é mais desktop-only — vai 100% via WAHA.

## Backlog
- P1: Refatorar `Analytics.jsx` (852 linhas) em subcomponentes (KpiGrid, HeatmapMap, FilterPanel, PdfFieldsModal, ShareModal)
- P2: Split do `server.py` (1.724 LOC) em `routers/{chat,analytics,whatsapp,google,reports,config}.py`
- P2: Unificar `kpis()` / `kpis_filtered()` (duplicação histórica)
- P3: Migrar `banco_relatorios.json` para Mongo (paginação + busca textual)
- P3: Treinar wake-word custom "sexta-feira" no openwakeword
- P3: Testes pytest para `monthly_macro()` e `auto_report.generate_monthly()`
