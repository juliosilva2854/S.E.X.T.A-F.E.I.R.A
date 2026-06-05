# REVISÃO DE CÓDIGO — Mavis / Sexta-feira

> Revisão completa do codebase realizada em 05/06/2026.
> Escopo: backend FastAPI (1.724 LOC), pacote `mavis/` (8.151 LOC Python total),
> frontend React (5.315 LOC JS/JSX), scripts de execução local e arquivos de dados.

## TL;DR

O codebase está em **boa forma**. Não há vulnerabilidades graves, secrets vazados,
`eval/exec`, `bare except`, `datetime.utcnow` ou imports duplicados. Toda a base está
**lintada (ruff e ESLint passando 100%)**. Os pontos de atenção encontrados são em sua
maioria de **manutenibilidade** (arquivos grandes, oportunidades de extração) e
**hardening** (validações finas, paginação, índices).

| Categoria | Itens | Status |
|---|---|---|
| 🔴 Críticos | 0 | — |
| 🟠 Importantes | 4 | 2 corrigidos · 2 backlog |
| 🟡 Manutenibilidade | 6 | backlog |
| ✅ Bem feito | 12 | — |

---

## 🟠 Importantes

### 1. (✅ Corrigido) Erros de lint pré-existentes
- `mavis/skills/analytics.py:403` — variável `l` ambígua (E741). Renomeada para `loc`.
- `mavis/skills/whatsapp.py:85-86` — `if X: Y` em uma linha (E701). Quebrado em múltiplas linhas.
- `mavis/skills/analytics.py` (novo) — re-import de `Optional` dentro de função. Removido.

Resultado: **ruff + ESLint 100% limpos em todo o codebase**.

### 2. (✅ Corrigido) Frontend chama URL preview quando rodando local
Bug encontrado e corrigido na sessão anterior: `scripts/preparar.bat` agora cria
`frontend/.env.production.local` apontando para `http://localhost:8001` antes do
`yarn build`. Sem isso, o painel local ficava batendo no servidor hospedado.

### 3. (Backlog) `WhatsApp` skill desktop não usa `whatsapp_favorites`
`mavis/skills/whatsapp.py::send_message()` aceita só `contact: str`. A skill chamadora
(no `sexta-feira.py` e em `auto_report._try_send_whatsapp`) já passa o nome resolvido pelo
favorito (correto), mas a função em si não conhece o conceito de favorito. Está OK
funcionalmente — ressalva é só de modelagem (acoplamento via string).

**Recomendado**: aceitar opcional `favorite_id` direto, fazendo a resolução interna.
Não é bug, é design.

### 4. (Backlog) `Analytics.jsx` (852 linhas) — extrair subcomponentes
Já mapeado no PRD. Recomendado extrair:
- `KpiGrid` (cards de KPI)
- `HeatmapMap` (Leaflet + heat layer)
- `FilterPanel` (data início/fim/unidade/combustível)
- `MonthlyDetailModal`
- `PdfFieldsModal` (novo, já isolado como `FieldGroup`)
- `ShareWhatsAppModal` (novo)

Isso não é bug — funciona perfeito. Mas dificulta manutenção.

---

## 🟡 Manutenibilidade / oportunidades

### 5. `backend/server.py` (1.724 linhas) — split por domínio
Crescimento orgânico OK, mas chegou no limite saudável. Sugiro dividir em routers:
- `routers/chat.py` (chat, agent, tts)
- `routers/analytics.py` (kpis, weekly, monthly, export, auto-report, auto-monthly)
- `routers/whatsapp.py` (favorites, send)
- `routers/google.py`
- `routers/reports.py`
- `routers/config.py`

Cada um inclui no `api = APIRouter()` e fica fácil de testar.

### 6. `mavis/skills/analytics.py` — duplicação entre `kpis()` e `kpis_filtered()`
A função `kpis()` é praticamente um caso especial de `kpis_filtered()` sem filtros.
Hoje há duas implementações com o mesmo corpo. Sugerido manter só `kpis_filtered()`
e fazer `kpis()` chamar `kpis_filtered("", "", "")`. Mesma coisa para `weekly_series`/
`weekly_filtered` e `activity_distribution`/`activity_filtered`.

### 7. `relatorios.py` e `rotinas.py` (raiz do repo) — legado
São o **código original pré-MAVIS** (Playwright + gspread). Ainda funcionam e
ainda são usados pelo `sexta-feira.py` (loop voz desktop) via `route.legacy`.
**NÃO REMOVER** sem antes garantir que o RPA do FieldControl foi migrado para
`mavis/skills/`. Sugiro adicionar comentário no topo desses arquivos sinalizando
"LEGADO — usado pelo loop desktop legado".

### 8. Banco de relatórios em arquivo JSON
`banco_relatorios.json` cresce indefinidamente. Cada relatório tem ~5-10KB.
Em 5 anos pode ficar grande demais para `read_json` carregar tudo na RAM
em cada request. Sugerido: paginação no endpoint `/api/reports?limit=...&offset=...`
ou migração para Mongo (`db.relatorios.find()`).

### 9. Frontend usa Web Speech API (Chrome/Edge only)
`WakeWord.jsx` usa `webkitSpeechRecognition`, que não funciona em Firefox/Safari.
Já existe fallback `setSupported(false)` que desabilita o botão. OK funcionalmente.
Sugerido: tooltip explicando o motivo no estado desabilitado (já existe — bom).

### 10. Wake-word desktop (`mavis/skills/wake_word.py`) usa "hey_jarvis" default
O modelo `hey_jarvis_v0.1` do openwakeword não responde a "sexta-feira" naturalmente.
Para treinar um modelo custom, ver
[openWakeWord training](https://github.com/dscripka/openWakeWord#training-new-models).
Por enquanto, no PC o usuário precisa dizer "hey jarvis" (ou trocar `WAKE_WORD_MODEL`
no .env para outro modelo do catálogo do openwakeword).

**Não é bug** — é restrição da biblioteca. Documentar no `COMO_RODAR_EM_BACKGROUND.md`.

---

## ✅ Pontos bem feitos

1. **Storage atômico**: `mavis/core/storage.py` usa `write_to_tmp + os.replace()` — não perde dados em crash.
2. **Skills isoladas**: cada skill é um módulo independente, importação lazy onde possível.
3. **Frontend modular**: 24 páginas em `pages/`, Layout com sidebar única, `api.js` centralizado.
4. **Hot reload preservado**: backend usa watchfiles, frontend CRA — restart só em .env/deps.
5. **Validação no Pydantic**: todos os endpoints com body usam `BaseModel` (FastAPI valida).
6. **CORS configurado via .env**: `CORS_ORIGINS=*` em dev, restringível em prod.
7. **Cache de geocoding**: 20/20 unidades resolvidas, respeita rate-limit do Nominatim.
8. **Scheduler unificado**: APScheduler com `tzlocal` configurado para America/Sao_Paulo.
9. **Logs em buffer + WebSocket**: stream em tempo real no painel via `/api/logs/stream`.
10. **Path traversal safe**: `auto_report.report_path()` usa `os.path.basename()` ao montar `REPORTS_DIR / filename`.
11. **Fallbacks para LLM offline**: `_fallback_summary` e `_fallback_monthly` garantem que o resumo nunca trava se Gemini indisponível.
12. **Logs estruturados**: `push_log()` com `level`, `source`, `message` — fácil filtrar no painel `/logs`.

---

## ❌ NÃO encontrado (verificação de segurança/qualidade)

- **0** uso de `eval()` ou `exec()`
- **0** `bare except:` (todos `except Exception:` ou específicos)
- **0** `datetime.utcnow()` (todos `datetime.now(timezone.utc)`)
- **0** secrets hardcoded (todas as chaves vêm de `.env`)
- **0** `console.log` deixado no frontend
- **0** uso de `react-leaflet` (incompatível com React 18 — usamos Leaflet vanilla)
- **0** imports duplicados (`from x import x, x`)
- **0** path traversal vulnerável
- **0** sync calls bloqueantes (`time.sleep`) em endpoints async
- **0** input sem validação Pydantic

---

## 📋 Próximas ações sugeridas (em ordem de prioridade)

1. **P1**: Refatorar `Analytics.jsx` em subcomponentes (#4). Reduz tempo de re-render
   em filtragens e facilita testes.
2. **P2**: Split do `server.py` em `backend/routers/*.py` (#5). Melhora navegação e
   isola escopos de teste.
3. **P3**: Migrar relatórios para Mongo (#8). Habilita paginação real e busca textual.
4. **P3**: Documentar treinamento de wake-word custom "sexta-feira" no openwakeword (#10).
5. **P3**: Adicionar testes para `monthly_macro()` e `auto_report.generate_monthly()`
   (já existem 18 testes pytest para o resto do analytics).
