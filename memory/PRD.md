# S.E.X.T.A - F.E.I.R.A (MAVIS) — Status / PRD

## Pedido do usuário
Assistente pessoal full-stack (React + FastAPI + MongoDB) de um técnico de campo de uma
operadora de saúde (visita UPAs/AMAs/hospitais na Grande São Paulo).
Tarefa atual: **Página de Analytics** com mapa de calor geográfico e exportação (CSV/Excel/PDF).
Redesign premium (tema escuro + âmbar, estilo "terminal/control room"), garantindo que
**todas as unidades** sempre apareçam no mapa.

## Stack
- Backend: FastAPI (porta 8001), MongoDB local, Gemini 2.5 Flash (chat — requer CHAVE_GEMINI), APScheduler, edge-tts
- Frontend: React CRA (porta 3000), Tailwind, Recharts, **Leaflet + leaflet.heat** (vanilla, via callback ref), @phosphor-icons/react
- Dados: arquivos JSON em /app (banco_de_dados.json = 267 rotas, banco_relatorios.json = 5 relatórios) + cache de geocoding

## URL de acesso (preview)
https://chat-system-core.preview.emergentagent.com  → página: /analytics

## O que foi feito

### 03/06/2026 — Setup inicial
- Criados backend/.env e frontend/.env; supervisor RUNNING; /api/health, /api/status, /api/chat validados.

### 03/06/2026 — Analytics (Mapa de calor + Exportação) ✅ CONCLUÍDO E TESTADO
- **Correções de ambiente (fork)**: recriados `backend/.env` e `frontend/.env` (perdidos no fork);
  corrigido `pydantic-core` para **2.23.4** (estava 2.46.4, incompatível com pydantic 2.9.2);
  instalado `tzlocal==5.2` + `pytz` (faltavam, quebravam o APScheduler). requirements.txt re-congelado.
- **Backend** (`server.py`): novos endpoints `GET /api/analytics/{map-data, export, unidades}`;
  `kpis`, `weekly`, `activities` agora aceitam filtros `start`/`end`/`unidade`.
  `export?format=csv|xlsx|pdf` retorna arquivo com Content-Disposition.
- **Geocoding** (`geocoding.py`): lookup remoto melhorado (múltiplas variações: nome completo →
  bairro sem prefixo de unidade → "bairro X") + viewbox da Grande SP; seed manual para 3 unidades
  que o Nominatim não resolve. **Resultado: 20/20 unidades geolocalizadas, 0 unresolved.**
  Cache em `/app/geocode_cache.json` (totalmente populado; respeita rate-limit Nominatim).
- **Frontend** (`Analytics.jsx`): reescrita completa seguindo `design_guidelines.json` —
  header glass, painel de filtros, KPI cards, mapa de calor Leaflet (CARTO dark + heat âmbar + marcadores),
  gráficos Recharts, heatmap por dia da semana, top destinos/equipamentos, botões de export, modal mensal.
  Carga resiliente (Promise.allSettled) + mapa em fetch separado. `loadAll(override)`/`filterQS(extra, override)`
  aceitam override explícito de filtros (correção de stale-closure no "Limpar").
- **Testes**: 16/16 pytest backend (`/app/backend/tests/test_analytics.py`) + E2E frontend via testing agent
  (iteration_3 e iteration_4). Bug do "Limpar" encontrado e corrigido (iteration_4: VERIFICADO, sem issues).

## Observações importantes
- **CHAVE_GEMINI está VAZIA** (perdida no fork). O Analytics NÃO precisa de LLM e funciona 100%.
  O chat/IA só voltará quando o usuário fornecer a chave Gemini. Header mostra "OFFLINE" por isso.
- **Restrições**: NÃO alterar `pydantic-core==2.23.4` nem `tzlocal/pytz`. Manter cache de geocoding.
- react-leaflet@5 é incompatível com React 18 → usamos **Leaflet vanilla** diretamente (não react-leaflet).

### 03/06/2026 — Restauração do .env + Compartilhamento WhatsApp ✅
- **`.env` corrigido** com os valores reais do usuário: `DB_NAME=sexta_feira` (estava errado),
  **CHAVE_GEMINI** restaurada (chat/IA ATIVO — validado), voz `pt-BR-ThalitaNeural`,
  personalidade `corporativa`, Field Control e WhatsApp.
- **Melhoria — "Compartilhar relatório no WhatsApp"**:
  - Backend: `GET /api/analytics/resumo` gera um resumo executivo em texto (KM, combustível,
    atividades, top destinos) pronto para WhatsApp; aceita filtros + `titulo`.
  - Frontend: botão verde "COMPARTILHAR" no header e botão no modal mensal → gera o resumo,
    baixa o PDF do período e abre `wa.me` com a mensagem pronta (usuário escolhe o grupo
    "Resumos - ToLife" e anexa o PDF). Funciona em qualquer ambiente (não depende do desktop).
  - Testes: 18/18 pytest backend (inclui resumo) passando.
- **Guia criado**: `/app/COMO_RODAR_EM_BACKGROUND.md` (NSSM / Agendador / Docker) para o item
  P1 de execução em background (que é deploy local — RPA/WhatsApp auto são desktop-only).

## Backlog / Próximos passos
- P1: Pedir ao usuário a CHAVE_GEMINI para reativar o chat/IA.
- P1: Execução em background (Docker Compose / serviço Windows / PWA / Electron).
- P2: Refatorar `Analytics.jsx` (506 linhas) em subcomponentes (KpiGrid, HeatmapMap, FilterPanel, MonthlyChart).
- P2: Persistir/seed mais coordenadas de unidades para reduzir dependência do Nominatim.
