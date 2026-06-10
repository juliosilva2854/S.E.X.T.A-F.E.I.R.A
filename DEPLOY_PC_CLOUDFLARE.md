# 🖥️➡️🌐 Deixar a MAVIS no ar a partir do SEU PC (Cloudflare Tunnel)

Roda o painel no seu próprio computador e publica em **https://ia.sconnecta.com.br**
**sem abrir portas no roteador, sem IP fixo e com HTTPS automático** — usando o
**Cloudflare Tunnel** (grátis, e NÃO é Emergent).

> Por que dá certo no mesmo PC: o `sexta-feira.py` (voz/WAHA) usa o MAVIS **em processo**,
> não pela API HTTP. Então proteger o painel com login **não atrapalha** a automação de desktop.

Requisitos: **Docker Desktop** (você já usa para o WAHA) + conta **Cloudflare grátis**.

---

## 1) Coloque o domínio no Cloudflare (1x)
1. Crie conta grátis em https://dash.cloudflare.com e clique **Add a site** → `sconnecta.com.br`.
2. O Cloudflare importa seus registros DNS atuais — **confira se e-mail/site existentes vieram** (recrie se faltar).
3. No seu registrador, **troque os nameservers** pelos 2 que o Cloudflare indicar. (Propaga em minutos/horas.)

> Não quer mover o domínio inteiro? Veja a alternativa por *port forwarding* no fim (mais trabalhosa).

## 2) Crie o Túnel
1. Cloudflare → **Zero Trust** → **Networks → Tunnels** → **Create a tunnel** → tipo **Cloudflared** → dê um nome (ex: `mavis`).
2. Copie o **Connector token** (string longa). Guarde.
3. Em **Public Hostnames** → **Add a public hostname**:
   - Subdomain: `ia`  |  Domain: `sconnecta.com.br`
   - Service: **HTTP**  →  URL: `web:8080`
   - Salve.

## 3) Configure e suba o PAINEL (no seu PC, dentro da pasta `deploy`)
Este painel Docker é só o **dashboard protegido**. Seu app nativo (voz, WAHA, planilha)
continua rodando normalmente e **envia os dados** para ele.
```bash
cp backend.env.example backend.env
# edite backend.env: troque ADMIN_PASSWORD (senha forte) e defina PUBLISH_KEY (openssl rand -hex 24)
```
Crie um arquivo **`.env`** ao lado do compose com o token do túnel:
```
TUNNEL_TOKEN=cole_aqui_o_connector_token
```
Suba:
```bash
docker compose -f docker-compose.pc.yml up -d --build
```
Em ~1 min: **https://ia.sconnecta.com.br** → tela de login. (Localmente também responde em `http://localhost:8080`.)

## 3.1) Ligue o envio de dados do app NATIVO → painel
No `backend/.env` do seu app nativo (o de sempre, `IS_CLOUD=false`), adicione:
```
CLOUD_PUBLISH_URL=http://localhost:8080
PUBLISH_KEY=<a MESMA chave que você pôs no deploy/backend.env>
```
Reinicie o backend nativo. A cada sync da planilha (manual ou auto), os dados vão pro painel.
Para forçar agora: `curl -X POST http://localhost:8001/api/publish/now`

## 4) Google Cloud (1x)
No seu OAuth client **Web**:
- Redirect URI: `https://ia.sconnecta.com.br/auth/google`
- JavaScript origin: `https://ia.sconnecta.com.br`
- Tela de consentimento → Usuários de teste: `julio.silva2854@gmail.com`

---

## Observações
- O PC precisa ficar **ligado** para o painel responder (é ele o servidor).
- Atualizar: `docker compose -f docker-compose.pc.yml up -d --build`
- Logs: `docker compose -f docker-compose.pc.yml logs -f`
- Arquitetura: app **nativo** (IS_CLOUD=false, faz tudo) → publica → painel **Docker** (IS_CLOUD=true, só mostra, protegido por login). Os dois rodam no mesmo PC.
- Página pública de Analytics: `https://ia.sconnecta.com.br/p/analytics?s=...&t=...` (gere em **Compartilhar**).

## Alternativa SEM Cloudflare (port forwarding) — só se não puder mover o DNS
1. DNS: registro A `ia` → seu IP público (precisa de **IP fixo** ou **DDNS**).
2. Roteador: encaminhar portas **80** e **443** para o IP local do PC.
3. Suba o `docker-compose.yml` (variante VPS, com Caddy fazendo HTTPS):
   `docker compose up -d --build`
> Riscos: muitos provedores bloqueiam a porta 80 residencial, e expõe seu PC direto à internet.
> O Cloudflare Tunnel é mais seguro e simples.
