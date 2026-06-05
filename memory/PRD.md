# S.E.X.T.A - F.E.I.R.A (MAVIS) — Status / PRD

## Pedido do usuário
Assistente pessoal full-stack (React + FastAPI + MongoDB) de um técnico de campo de uma
operadora de saúde (visita UPAs/AMAs/hospitais na Grande São Paulo).

**Tarefa concluída em 05/06/2026**: restaurar o ambiente preview após o fork e finalizar a
**Opção B — Inicialização automática + janela oculta (Windows)** para rodar local em background.

## Stack
- Backend: FastAPI (porta 8001), MongoDB local, Gemini 2.5 Flash (chat — CHAVE_GEMINI ATIVA), APScheduler, edge-tts
- Frontend: React CRA (porta 3000), Tailwind, Recharts, **Leaflet + leaflet.heat** (vanilla, via callback ref), @phosphor-icons/react
- Dados: arquivos JSON em /app (banco_de_dados.json = 267 rotas, banco_relatorios.json = 5 relatórios) + cache de geocoding (20/20 unidades geolocalizadas)
- Desktop loop de voz: `sexta-feira.py` (wake word + Vosk PT-BR em `/app/model` + edge-tts ThalitaNeural)
- 30+ skills em `/app/mavis/` (core + skills: agent, analytics, computer, vision, whatsapp, google_*, code_assistant, document_tools, research, knowledge, finance, productivity, workflows, etc.)

## URL de acesso (preview atual)
https://5ad4471b-753a-4653-a0a4-dd5fdcb8a0a5.preview.emergentagent.com

## O que foi feito

### 03/06/2026 — Analytics + Restauração do .env (sessões anteriores)
- Página `/analytics` completa: KPIs, mapa de calor (Leaflet vanilla), exportação CSV/Excel/PDF,
  filtros, modal mensal, botão "Compartilhar" (wa.me + PDF download).
- 16+2/18 pytest backend passando; E2E frontend validado pelo testing agent (iteration_4).
- Bug "Limpar filtros" corrigido (stale-closure resolvido via override explícito em `loadAll`).

### 05/06/2026 — Restauração pós-fork + Opção B finalizada ✅
- `backend/.env` recriado com valores do usuário (CHAVE_GEMINI ativa, DB_NAME=sexta_feira,
  Field Control e WhatsApp do Julio).
- `frontend/.env` recriado: `REACT_APP_BACKEND_URL=https://5ad4471b-...preview.emergentagent.com`
  + `DANGEROUSLY_DISABLE_HOST_CHECK=true` (resolve "Invalid Host header" do CRA no preview).
- Supervisor: backend + frontend RUNNING; `/api/health` 200, `/api/status` retorna 267 rotas,
  30 memórias, 5 relatórios, gemini_configurado=true. Chat respondendo em ~1.7s.
- **Opção B (Windows local)** finalizada:
  - `scripts/preparar.bat` melhorado: valida `backend/.env`, cria `frontend/.env.production.local`
    apontando para `http://localhost:8001` antes do `yarn build` (correção crítica — sem isso o
    painel local ficava chamando a URL preview).
  - `scripts/iniciar_oculto.vbs` — lança Mongo + uvicorn :8001 + serve :3000 sem janela e abre browser.
  - `scripts/registrar_inicializacao.bat` — registra `schtasks /sc onlogon` para auto-start.
  - `COMO_RODAR_EM_BACKGROUND.md` reescrito: pré-requisitos, 4 passos da Opção B com comandos
    exatos, tabela de scripts, comandos de controle (`schtasks /run|/query|/delete`),
    troubleshooting (Mongo, portas ocupadas, build apontando para URL errada).

## Observações importantes
- **CHAVE_GEMINI ATIVA** no preview (chat/IA funcionando — header mostra `[ONLINE]`).
- **Restrições**: NÃO alterar `pydantic-core==2.23.4` nem `tzlocal/pytz`. Manter cache de geocoding.
- react-leaflet@5 incompatível com React 18 → usamos **Leaflet vanilla** (não react-leaflet).
- RPA Field Control + WhatsApp auto = desktop-only (Playwright headless=False) — só funciona
  na Opção B (com sessão Windows logada).

## Backlog / Próximos passos
- P1: Usuário rodar `scripts\preparar.bat` no Windows para testar o fluxo Opção B end-to-end.
- P2: Refatorar `Analytics.jsx` (506 linhas) em subcomponentes (KpiGrid, HeatmapMap, FilterPanel, MonthlyChart).
- P2: Persistir/seed mais coordenadas de unidades para reduzir dependência do Nominatim.
- P3: PWA offline para painel acessível sem internet em campo (cache de rotas + sync ao voltar online).
