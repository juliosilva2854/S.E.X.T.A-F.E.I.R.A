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
https://repo-analyzer-243.preview.emergentagent.com

## O que foi feito

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
- **Restrições**: `pydantic-core==2.23.4`, `tzlocal/pytz`, cache geocoding, Leaflet vanilla (não react-leaflet)
- **Desktop-only** (precisa DESKTOP_MODE=1): RPA Field Control, envio automático WhatsApp via Playwright

## Backlog
- P1: Refatorar `Analytics.jsx` (852 linhas) em subcomponentes (KpiGrid, HeatmapMap, FilterPanel, PdfFieldsModal, ShareModal)
- P2: Split do `server.py` (1.724 LOC) em `routers/{chat,analytics,whatsapp,google,reports,config}.py`
- P2: Unificar `kpis()` / `kpis_filtered()` (duplicação histórica)
- P3: Migrar `banco_relatorios.json` para Mongo (paginação + busca textual)
- P3: Treinar wake-word custom "sexta-feira" no openwakeword
- P3: Testes pytest para `monthly_macro()` e `auto_report.generate_monthly()`
