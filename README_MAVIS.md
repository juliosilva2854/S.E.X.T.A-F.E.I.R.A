# MAVIS / SEXTA-FEIRA v3.0 — Setup & Manual de Operação

> IA pessoal modular: voz neural, visão computacional, controle do PC,
> conexão Google (Calendar/Gmail/Drive), WhatsApp, lembretes, memória persistente.

---

## 1. Arquitetura

| Camada | Onde roda | O que faz |
|---|---|---|
| **App Desktop** (`sexta-feira.py`) | Seu PC | Escuta voz, controla mouse/teclado, lê tela, conversa, executa todas as skills |
| **Painel Web** (FastAPI + React) | Container Emergent ou seu PC | Dashboard de controle, chat por texto, Google Hub, lembretes, memória longa, visão de imagens, status |
| **Pacote `mavis/`** | Compartilhado | Skills, cérebro, memória — usado pelos dois lados |

Os dois lados leem/escrevem os mesmos arquivos JSON em `/app`:
`memoria_mavis.json`, `banco_de_dados.json`, `banco_relatorios.json`,
`long_memory.json`, `reminders.json`.

---

## 2. Instalação no seu PC (Desktop)

### 2.1 Pré-requisitos
- **Python 3.10+**
- **PortAudio** (para microfone):
  - Windows: já vem nos wheels do PyAudio
  - Linux: `sudo apt install portaudio19-dev python3-pyaudio`
  - macOS: `brew install portaudio`
- **Google Chrome** instalado (para WhatsApp Web via Playwright)

### 2.2 Clone e dependências
```bash
git clone <seu-repo> mavis && cd mavis
pip install -r requirements.txt
playwright install chromium
```

### 2.3 Configure o `.env`
Crie `/app/backend/.env` (ou `/app/.env`) com:
```env
CHAVE_GEMINI=AIzaSy...sua-chave...
GEMINI_MODEL=gemini-2.5-flash
NOME_IA=Sexta-feira
VOZ_SINTETIZADOR=pt-BR-ThalitaNeural
PAUSE_THRESHOLD=1.0
MAVIS_PROATIVO=1
MAVIS_PERSONALITY=corporativa

FIELDCONTROL_EMAIL=seu@email.com
FIELDCONTROL_SENHA=sua_senha
WHATSAPP_NUMERO=5511...
WHATSAPP_GRUPO=Resumos - ToLife
```

### 2.4 Rode
```bash
python sexta-feira.py
```

---

## 3. Habilitando o Google Cloud Console (passo-a-passo)

A MAVIS usa **Calendar / Gmail / Drive / Sheets**. Você precisa criar suas próprias credenciais OAuth (gratuito).

### Passo 3.1 — Criar projeto no Google Cloud
1. Acesse https://console.cloud.google.com
2. Topo da tela, clique no seletor de projeto **→ NOVO PROJETO**
3. Nome: `MAVIS` (ou outro qualquer) → **Criar**

### Passo 3.2 — Habilitar as APIs necessárias
No menu lateral: **APIs e Serviços → Biblioteca**. Habilite uma por uma:
- ✅ **Google Calendar API**
- ✅ **Gmail API**
- ✅ **Google Drive API**
- ✅ **Google Sheets API** (já usado pelas planilhas)

Para cada uma: digite o nome → clique → **Ativar**.

### Passo 3.3 — Configurar tela de consentimento OAuth
1. **APIs e Serviços → Tela de consentimento OAuth**
2. **User Type**: External → **Criar**
3. Preencha:
   - Nome do app: `MAVIS`
   - Email de suporte: seu email
   - Email do desenvolvedor: seu email
4. **Salvar e continuar** até a aba **Test users**
5. Em **Test users**, clique **+ ADD USERS** e adicione seu próprio email Google
6. **Salvar**

> ⚠️ Sem adicionar seu email como Test user, o Google bloqueia (app não verificado).

### Passo 3.4 — Criar credencial OAuth (Desktop App)
1. **APIs e Serviços → Credenciais → + CRIAR CREDENCIAIS → ID do cliente OAuth**
2. Tipo de aplicativo: **Aplicativo para computador**
3. Nome: `MAVIS Desktop` → **Criar**
4. Surge um popup → clique **DOWNLOAD JSON**
5. Salve o arquivo em `/app/credenciais.json` (ou caminho que estiver no `.env`)

### Passo 3.5 — Primeiro login (consentimento)
Na primeira vez que a MAVIS tentar acessar Google (chat "qual minha agenda?"), o navegador abrirá pedindo:
- Login na sua conta Google
- Tela "Google não verificou este app" → **Avançado → Acessar MAVIS (não seguro)**
- Aceite os escopos solicitados (Calendar, Gmail, Drive, Sheets)
- Token salvo em `/app/google_token.json` automaticamente

A partir daí tudo funciona silenciosamente.

### Escopos solicitados:
```
https://www.googleapis.com/auth/calendar          (RW)
https://www.googleapis.com/auth/gmail.modify      (ler/marcar)
https://www.googleapis.com/auth/gmail.send        (enviar)
https://www.googleapis.com/auth/drive.readonly    (buscar)
https://www.googleapis.com/auth/spreadsheets      (KM planilha)
```

---

## 4. Comandos de voz suportados

### Sistema
- "qual minha bateria"
- "uso de CPU" / "RAM"
- "trava o PC" / "desliga o PC"

### Computador
- "abre o Chrome" / "fecha o Spotify"
- "tira print" (salva em `screenshots/`)
- "olha a tela" / "o que tem na tela" → MAVIS analisa com Gemini Vision

### Google
- "minha agenda de hoje"
- "agenda da semana"
- "marca reunião amanhã às 14h sobre projeto X"
- "tenho email" / "resumo dos emails"
- "busca relatório no drive"

### WhatsApp
- "tenho mensagens" / "mensagens não lidas no whats"
- "manda mensagem pro Pedro: estou chegando"

### Memória & Lembretes
- "lembra disso: minha esposa se chama Maria"
- "me lembra de tomar remédio amanhã às 8h"
- "quais meus lembretes?"

### Mídia
- "toca música" / "pausa" / "próxima música"

### Informação
- "notícias" / "manchetes"
- "clima hoje" / "vai chover?"

### Rotinas legacy (mantidas)
- "aprender rotas"
- "atualizar planilha"
- "gerar relatório"

---

## 5. Painel Web

Backend: `uvicorn server:app` (auto-iniciado pelo supervisor no container Emergent)
Frontend: `yarn start` (auto-iniciado)

Navegue: **Overview → Chat → Visão → Rotas → Relatórios → Memória Curta → Memória Longa → Lembretes → Google Hub → Skills → Logs → Configuração**

---

## 6. Modo Proativo

Quando `MAVIS_PROATIVO=1` no `.env`, a MAVIS roda um loop em background que:
- ✅ Dispara lembretes na hora marcada (com voz)
- ✅ Alerta bateria <20% (a cada 5min)
- ✅ Avisa "reunião em 15 minutos" para próximos eventos do Calendar
- (mais avisos podem ser adicionados em `mavis/skills/proactive.py`)

---

## 7. Personalidade

Mude o tom da MAVIS no Painel → Configuração → Personalidade:
- **corporativa** (JARVIS, "senhor", padrão)
- **casual** (amiga próxima)
- **sarcastica** (humor afiado, "chefe")

Ou no `.env`: `MAVIS_PERSONALITY=casual`

---

## 8. Wake word (opcional)

Por padrão a MAVIS escuta sempre. Para ativá-la só com palavra-chave:
1. `pip install openwakeword`
2. No seu loop custom, chame `mavis.skills.wake_word.start_listener(callback)`
3. Use modelo padrão `hey_jarvis_v0.1` ou treine "sexta-feira" próprio: https://github.com/dscripka/openWakeWord

---

## 9. Estrutura de pastas

```
/app
├── mavis/                  # Pacote compartilhado
│   ├── core/
│   │   ├── brain.py        # Gemini + multimodal + extração estruturada
│   │   ├── long_memory.py  # Fatos persistentes
│   │   ├── reminders.py    # Lembretes/alarmes
│   │   ├── router.py       # Roteador de intents (regex)
│   │   ├── paths.py
│   │   └── storage.py
│   └── skills/
│       ├── computer.py     # PyAutoGUI (desktop)
│       ├── vision.py       # Screenshot + Gemini Vision
│       ├── system_info.py  # Bateria/CPU/RAM/Disk
│       ├── whatsapp.py     # Playwright (desktop)
│       ├── google_auth.py  # OAuth shared
│       ├── google_calendar.py
│       ├── google_gmail.py
│       ├── google_drive.py
│       ├── scheduler.py    # APScheduler
│       ├── proactive.py    # Loop proativo
│       ├── wake_word.py    # openWakeWord
│       └── news_weather.py # RSS + Open-Meteo
├── sexta-feira.py          # App desktop (voz)
├── rotinas.py              # Rotinas legacy (FieldControl, etc)
├── relatorios.py
├── planilhas.py
├── aprender_rotas.py
├── backend/                # FastAPI
│   ├── server.py
│   └── .env                # CHAVE_GEMINI, configs
├── frontend/               # React + Tailwind
└── *.json                  # Estado (rotas, memórias, lembretes, relatórios)
```

---

## 10. Troubleshooting

| Sintoma | Solução |
|---|---|
| `portaudio.h not found` | Linux: `sudo apt install portaudio19-dev`. Windows: instale o wheel oficial do PyAudio. |
| Google "app not verified" | Adicione seu email em **Test users** na tela de consentimento OAuth (passo 3.3). |
| `credenciais.json não encontrado` | Coloque em `/app/credenciais.json` ou ajuste `ARQUIVO_CREDENCIAIS_GOOGLE` no `.env`. |
| WhatsApp não abre | Rode `playwright install chromium`. Primeira vez precisa escanear QR code. |
| Voz não toca | Sistema sem áudio. Teste outra voz no Painel → Configuração. |
| Wake word não detecta | Treine modelo custom em openWakeWord ou use modelo padrão `hey_jarvis`. |

---

Última atualização: Jun 2026
