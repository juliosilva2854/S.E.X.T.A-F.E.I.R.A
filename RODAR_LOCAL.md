# 🖥️ Rodar a MAVIS / Sexta-feira 100% local (fora do Emergent)

> Guia do zero: do código no GitHub até compartilhar o link da página pública.
> Foco em **Windows** (o projeto já tem scripts `.bat`). No fim há a nota para Linux/Mac.

---

## 0. Como o app é dividido (entenda antes)

| Peça | Porta | Para quê |
|---|---|---|
| **Backend** (FastAPI) | 8001 | API, Analytics, tokens públicos, chat |
| **Frontend** (React) | 3000 | O painel que você abre no navegador |
| **MongoDB** | 27017 | Banco (sessões/metadados) |

Os **dados de verdade** (rotas, relatórios) ficam em **arquivos JSON** na raiz do projeto.

---

## 1. O que você PRECISA instalar (uma vez)

- **Python 3.11+** (marque “Add Python to PATH” no instalador)
- **Node.js LTS** + **Yarn** (`npm install -g yarn`)
- **MongoDB Community Server** instalado **como serviço do Windows**
  - confira com: `sc query MongoDB`

### O que você NÃO precisa (opcional)
- **Docker Desktop + WAHA** → só se quiser **enviar WhatsApp** automático.
- **Chrome + Playwright** → só para o **RPA do FieldControl** (gerar relatório automático).
- **credenciais.json do Google** → só para **Calendar / Gmail / Drive / Sheets**.
- **sexta-feira.py / modelo de voz** → só para **controle por voz** no PC.

👉 **Para a página Analytics e o link público funcionarem, nada disso acima é necessário.**

---

## 2. Pegar o código

**Opção A — `git clone` (só o código, sem dados nem segredos):**
```bash
git clone <seu-repo> mavis
cd mavis
```

**Opção B — baixar o projeto inteiro do Emergent (RECOMENDADO p/ migrar):**
> Traz também os **arquivos de dados** (rotas, relatórios, cache) que o git NÃO versiona.
> Use o recurso de download/“Save to GitHub” da plataforma.

Se usou a Opção A, copie manualmente da sua máquina atual estes arquivos para a raiz:
```
banco_de_dados.json        (267 rotas KM — essencial p/ cálculo)
banco_relatorios.json      (fonte do Analytics, se não usar Sheets)
sheets_cache.json          (fonte alternativa, vinda do Google Sheets)
geocode_cache.json         (coordenadas das unidades p/ o mapa de calor)
whatsapp_favoritos.json    (opcional)
long_memory.json           (opcional)
```
> `public_tokens.json` NÃO precisa copiar — é recriado quando você gera links.

---

## 3. Criar o `backend\.env` (você cria na mão)

Crie o arquivo `backend\.env` com este conteúdo (ajuste a chave):

```
MONGO_URL=mongodb://localhost:27017
DB_NAME=sexta_feira
CORS_ORIGINS=*
CHAVE_GEMINI=COLOQUE_SUA_NOVA_CHAVE_AQUI
GEMINI_MODEL=gemini-2.5-flash
NOME_IA=Sexta-feira
VOZ_SINTETIZADOR=pt-BR-ThalitaNeural
MAVIS_PERSONALITY=sarcastica
PAUSE_THRESHOLD=1.0
```

Opcionais (só se for usar):
```
FIELDCONTROL_EMAIL=...
FIELDCONTROL_SENHA=...
WHATSAPP_NUMERO=55...
WHATSAPP_GRUPO=...
WAHA_URL=http://localhost:3001
WAHA_API_KEY=mavis123
WAHA_SESSION=default
```

> ⚠️ **A página Analytics nem usa o Gemini** — ela calcula tudo dos JSONs.
> A chave só é necessária para Chat/Agente. **Use uma chave NOVA** (rotacionada).

O `frontend\.env` você **não** precisa criar: o `preparar.bat` gera sozinho um
`frontend\.env.production.local` apontando para `http://localhost:8001`.

---

## 4. Rodar (1 clique)

**Primeira vez** (instala tudo + build do frontend):
```cmd
scripts\preparar.bat
```

**Ligar tudo** (escolha um):
```cmd
scripts\rodar_tudo.bat     :: Mongo + backend + frontend (SEM Docker/WhatsApp/voz)
scripts\iniciar_tudo.bat   :: TUDO, inclusive Docker+WAHA e o loop de voz
```
Abre sozinho em **http://localhost:3000**.

**Parar tudo:**
```cmd
scripts\parar_tudo.bat
```

> O `rodar_tudo.bat` já chama o `preparar.bat` automaticamente se faltar algo.

---

## 5. Gerar e ENVIAR o link da página pública

1. No painel, abra **“Compartilhar”** (`/share`).
2. Dê um rótulo, defina após quantas tentativas erradas o link expira, **“Gerar link”**.
3. Copie a URL (o token só aparece **uma vez**) e envie.

### ⚠️ O ponto importante sobre “enviar o link”

Rodando local, o link é `http://localhost:3000/p/analytics?...` — e **`localhost` só abre
no SEU próprio PC**. Para outra pessoa abrir, escolha um caminho:

| Cenário | Como | Observação |
|---|---|---|
| **Mesma rede Wi-Fi** (LAN) | trocar `localhost` pelo IP da sua máquina (ex. `http://192.168.0.10:3000`) | Precisa **rebuildar** o frontend com `REACT_APP_BACKEND_URL=http://192.168.0.10:8001` |
| **Internet (qualquer pessoa)** | **Túnel** (Cloudflare Tunnel / ngrok) apontando para o app | Link temporário; o PC precisa ficar ligado |
| **Internet com link FIXO** | **Deploy** num servidor/cloud | Mais estável; não depende do seu PC ligado |

> **Por que rebuildar?** O frontend (3000) e o backend (8001) são separados. O navegador
> do visitante precisa alcançar o backend pelo **mesmo endereço** que você divulgar — não
> por `localhost`. Então o build do frontend tem que apontar `REACT_APP_BACKEND_URL` para
> esse endereço público/IP, e aí rodar `yarn build` de novo. O `CORS_ORIGINS=*` já permite.

✅ **Resumo honesto:** para uso **só seu**, `localhost` basta. Para **mandar pra alguém**,
o caminho mais simples e estável é **deploy**; o mais rápido e temporário é um **túnel**.

---

## 6. Linux / Mac (alternativa via Docker)

Sem as funções de voz/RPA, dá para subir tudo com:
```bash
docker compose up -d
```
(`docker-compose.yml` já sobe Mongo + backend + frontend; o serviço `waha` é o WhatsApp.)

---

## Checklist rápido

- [ ] Python, Node+Yarn e MongoDB instalados
- [ ] Código baixado (com os JSONs de dados copiados)
- [ ] `backend\.env` criado com a **chave nova**
- [ ] `scripts\preparar.bat` rodado uma vez
- [ ] `scripts\rodar_tudo.bat` → abre em localhost:3000
- [ ] Para compartilhar com outros: túnel ou deploy (rebuild do frontend apontando o backend)
