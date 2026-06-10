# Credenciais de Teste — MAVIS

> O painel agora tem AUTENTICAÇÃO MISTA, aplicada SOMENTE quando `IS_CLOUD=true` (nuvem).
> Quando `IS_CLOUD=false` (execução local no PC) o painel é totalmente aberto, sem login.

## Flag de ambiente (backend/.env)
- `IS_CLOUD=false` → local, sem login (default no preview/dev).
- `IS_CLOUD=true`  → nuvem, exige login no painel admin.

## Login do painel (apenas quando IS_CLOUD=true)
- **Login por senha**: campo "Senha do painel" → `ADMIN_PASSWORD=fVcuKJmpJ6_TbyF3`
- **Login Google (OAuth NATIVO — credenciais próprias, ZERO Emergent)**: troca de código direto com `oauth2.googleapis.com`.
  - `GOOGLE_CLIENT_ID` (a definir) + `GOOGLE_CLIENT_SECRET` em `backend/.env`.
  - Redirect URI dinâmico: `window.location.origin + /auth/google` (precisa estar registrado no Google Cloud Console).
  - Allowlist de e-mails. Seed inicial: `julio.silva2854@gmail.com`. Gerida via `GET/POST/DELETE /api/allowed-emails` ou painel `/access`.
- Sessão: cookie httpOnly `session_token` (7 dias) OU header `Authorization: Bearer <session_token>`.

## Google Cloud Console (OAuth client do usuário)
- Domínio de produção: `https://ia.sconnecta.com.br`
- Authorized JavaScript origins: `https://ia.sconnecta.com.br`, `https://mavis-cloud.preview.emergentagent.com`
- Authorized redirect URIs: `https://ia.sconnecta.com.br/auth/google`, `https://mavis-cloud.preview.emergentagent.com/auth/google`

## Publicação local → nuvem
- Endpoint `POST /api/publish` protegido por header `X-Publish-Key`.
- `PUBLISH_KEY=AyCwjongfdwJsyjEw7gKKC2I9D1NGSxo`
- App local envia dados após cada sync de Google Sheets (se `CLOUD_PUBLISH_URL` + `PUBLISH_KEY` configurados).

## Página pública (Analytics) — somente leitura
- Rota `/p/analytics?s=<id>&t=<token>` (sempre pública, mesmo na nuvem).
- Tokens guardados só como hash em `public_tokens.json` (gitignored).

## Para testar o gate em cloud mode
- Setar `IS_CLOUD=true` no backend/.env e reiniciar o backend.
- Criar sessão de teste via mongosh (ver /app/auth_testing.md) ou login por senha.
- DB_NAME real = `sexta_feira` (NÃO `test_database`).
