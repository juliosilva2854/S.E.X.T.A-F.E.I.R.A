# 🚀 Deploy da MAVIS na NUVEM (seu domínio, ZERO Emergent)

Este guia sobe **só o painel/dashboard** (Analytics + login) em `https://ia.sconnecta.com.br`,
num servidor seu, com HTTPS automático. As automações de desktop (WAHA, Playwright, voz)
continuam rodando **só no seu PC** — a nuvem recebe os dados via publicação automática.

Stack do deploy: **Docker Compose** → MongoDB + Backend (FastAPI) + Caddy (serve o React e faz HTTPS).

---

## 0) O que você precisa
- Um **servidor Linux com IP público** (qualquer VPS: Hetzner, DigitalOcean, Contabo, Oracle Cloud, AWS Lightsail, etc.).
- **Docker** e **Docker Compose** instalados no servidor.
- O domínio **`ia.sconnecta.com.br`** apontando (DNS tipo **A**) para o **IP do servidor**.
- Portas **80** e **443** liberadas no firewall.

> Não tem servidor ainda? Crie uma VPS Ubuntu 22.04 (1–2 GB RAM já bastam) e instale o Docker:
> ```bash
> curl -fsSL https://get.docker.com | sh
> ```

---

## 1) DNS (no seu provedor do domínio sconnecta.com.br)
Crie um registro:
```
Tipo: A   |  Nome: ia   |  Valor: <IP_DO_SEU_SERVIDOR>   |  TTL: automático
```
Aguarde propagar (geralmente minutos). Teste: `ping ia.sconnecta.com.br` deve mostrar o IP.

---

## 2) Suba o código no servidor
Copie o projeto para o servidor (via `git clone`, `scp` ou "Save to GitHub" + clone). Depois:
```bash
cd /caminho/do/projeto/deploy
cp backend.env.example backend.env
nano backend.env        # ajuste ADMIN_PASSWORD e PUBLISH_KEY (gere com: openssl rand -hex 24)
```
> Os valores de `GOOGLE_CLIENT_ID/SECRET` já vêm preenchidos. `IS_CLOUD=true` já está setado.

---

## 3) Suba os containers
```bash
docker compose up -d --build
```
O Caddy emite o certificado HTTPS sozinho na 1ª subida (precisa do DNS já apontando).
Acompanhe os logs:
```bash
docker compose logs -f
```
Pronto: acesse **https://ia.sconnecta.com.br** → tela de login (Google + senha).

---

## 4) Google Cloud (uma vez)
No seu OAuth **client Web** (Google Cloud → Credenciais), confirme que estão lá:
- **Authorized redirect URIs:** `https://ia.sconnecta.com.br/auth/google`
- **Authorized JavaScript origins:** `https://ia.sconnecta.com.br`
- **Tela de permissão OAuth → Usuários de teste:** adicione `julio.silva2854@gmail.com`
  (ou publique o app em "Production").

---

## 5) Ligar o envio automático LOCAL → NUVEM
No **seu PC** (app local), edite `backend/.env` e adicione:
```
CLOUD_PUBLISH_URL=https://ia.sconnecta.com.br
PUBLISH_KEY=<a MESMA chave que você pôs no backend.env da nuvem>
```
Reinicie o backend local. A partir daí, **toda sincronização do Google Sheets** (manual ou
o auto-sync diário) envia os dados para a nuvem automaticamente. Para forçar agora:
```bash
curl -X POST http://localhost:8001/api/publish/now
```

---

## 6) Gestão de acesso (no painel da nuvem)
Menu lateral **Acesso** (`/access`):
- Autorizar/remover e-mails Google.
- Ver "Últimos acessos" e **Encerrar sessões** de um usuário.

---

## Manutenção
```bash
docker compose pull && docker compose up -d --build   # atualizar
docker compose down                                   # parar
docker compose logs -f backend                        # logs do backend
```
Dados persistem nos volumes `mongo_data` (sessões/allowlist) e `mavis_data` (JSON do Analytics).

## Solução de problemas
- **HTTPS não emite:** confira DNS apontando e portas 80/443 abertas. `docker compose logs web`.
- **Login Google "Acesso bloqueado":** adicione seu e-mail em "Usuários de teste" (passo 4).
- **`redirect_uri_mismatch`:** a URL de redirect no Google Cloud deve ser EXATAMENTE `https://ia.sconnecta.com.br/auth/google`.
- **Analytics vazio:** rode a publicação do PC (passo 5).
