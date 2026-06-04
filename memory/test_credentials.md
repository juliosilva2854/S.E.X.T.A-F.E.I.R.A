# Sexta-feira (Mavis) — Test credentials

## App / Preview
- URL preview: https://route-insights-5.preview.emergentagent.com
- Página principal da tarefa: /analytics (PÚBLICA — sem login)

## Login Field Control (usado pelo RPA desktop — NÃO é login do app)
- Email: julio.bernardino@tolife.com.br
- Senha: JulioCesar701!

## Gemini / IA
- CHAVE_GEMINI configurada no backend/.env (chat/IA ATIVO).
- Modelo: gemini-2.5-flash

## MongoDB
- MONGO_URL=mongodb://localhost:27017
- DB_NAME=sexta_feira

## WhatsApp
- WHATSAPP_NUMERO=5511989442854
- WHATSAPP_GRUPO=Resumos - ToLife
- Envio automático = desktop-only (Playwright/web.whatsapp.com). No app hospedado usa-se o
  botão "Compartilhar" (link wa.me + download do PDF).
