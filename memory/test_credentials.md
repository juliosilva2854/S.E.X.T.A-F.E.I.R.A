# Credenciais de Teste — MAVIS

> Este painel NÃO possui login de usuário (uso pessoal local/preview).
> Segredos reais ficam APENAS em `backend/.env` (fora do Git, via .gitignore).

## Painel
- Sem autenticação. Acesso direto pela URL do preview.

## Página pública (Analytics) — somente leitura
- Gerada em runtime na página "Compartilhar" (`/share`).
- A URL contém `?s=<id>&t=<token>`. O token expira após N tentativas inválidas.
- Backend: tokens guardados só como hash em `public_tokens.json` (gitignored).

## Variáveis sensíveis (ver `backend/.env` — NÃO versionar)
- CHAVE_GEMINI, FIELDCONTROL_EMAIL, FIELDCONTROL_SENHA, WHATSAPP_NUMERO, WAHA_API_KEY
