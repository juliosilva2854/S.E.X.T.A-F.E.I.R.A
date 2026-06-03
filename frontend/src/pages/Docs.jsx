import React from "react";
import { Book } from "@phosphor-icons/react";

const SECTIONS = [
  {
    title: "1. Como rodar o painel web (este painel)",
    body: `O painel já está rodando neste container, mantido pelo supervisor:

  sudo supervisorctl status   # mostra backend + frontend
  sudo supervisorctl restart backend
  sudo supervisorctl restart frontend

Backend: FastAPI em :8001 · Frontend: React em :3000 · Mongo: localhost:27017
Logs: tail -n 200 /var/log/supervisor/backend.err.log`,
  },
  {
    title: "2. Como rodar a MAVIS desktop (voz, microfone, RPA)",
    body: `No seu PC (Windows/Linux/Mac):

  pip install -r requirements.txt
  playwright install chromium   # para WhatsApp e FieldControl
  python sexta-feira.py

Pré-requisitos:
  - Python 3.10+
  - PortAudio: Linux 'sudo apt install portaudio19-dev'; macOS 'brew install portaudio'; Windows vem no wheel
  - Microfone e alto-falantes ativos
  - credenciais.json do Google (veja seção 5) — só necessário se quiser usar Google Calendar/Gmail/Drive`,
  },
  {
    title: "3. Comandos de voz suportados",
    body: `SISTEMA: "qual a bateria", "uso de CPU", "RAM", "trava o PC", "desliga o PC"
COMPUTADOR: "abre Chrome", "fecha Spotify", "tira print"
VISÃO: "olha a tela", "o que tem na tela"
GOOGLE: "minha agenda hoje", "agenda da semana", "marca reunião amanhã 14h", "tenho email", "busca X no drive"
WHATSAPP: "mensagens não lidas", "manda mensagem pro Pedro: estou chegando"
MEMÓRIA: "lembra disso: X", "me lembra de Y amanhã às 8h", "quais meus lembretes"
MÍDIA: "play música", "pausa", "próxima música"
INFORMAÇÃO: "notícias", "manchetes", "clima hoje", "vai chover"
LEGADAS: "aprender rotas", "atualizar planilha", "gerar relatório"

Comandos NOVOS criáveis: vá em "Comandos" no painel e cadastre regex → resposta personalizada.`,
  },
  {
    title: "4. Como configurar tudo pelo painel",
    body: `Configuração → Editor .ENV: edite chave Gemini, voz, personalidade, FieldControl, WhatsApp, km/L, R$/L
Configuração → Personalidade: corporativa | casual | sarcástica (clique pra trocar)
Configuração → Voz: 5+ vozes neurais (toque o play pra testar)
Configuração → Google Credenciais: faça upload do credenciais.json aqui
Comandos: cadastre atalhos regex (instantâneos, sem custo Gemini)
Lembretes → POR FRASE: a MAVIS interpreta "me lembra de X amanhã às 9h"
Memória Longa: grave fatos sobre você (a MAVIS sempre lembra)
Workflows: builder visual pra automatizar sequências (chat→busca→resumo→nota)
Knowledge Base: faça upload de PDFs e pergunte qualquer coisa sobre eles`,
  },
  {
    title: "5. Habilitar Google APIs (Calendar/Gmail/Drive/Sheets)",
    body: `Passo-a-passo:
1. console.cloud.google.com → criar projeto "MAVIS"
2. APIs e Serviços → Biblioteca → habilitar:
     Google Calendar API · Gmail API · Google Drive API · Google Sheets API
3. APIs e Serviços → Tela de consentimento OAuth → External → preencha
     Test users: ADICIONE SEU EMAIL (senão Google bloqueia)
4. Credenciais → Criar credenciais → ID do cliente OAuth → Aplicativo para computador
5. Download JSON
6. No painel: Configuração → Google Credenciais → CARREGAR credenciais.json
7. Rode 'python sexta-feira.py' uma vez → abrirá navegador pedindo consentimento
8. Token salvo em google_token.json (silencioso a partir daí)

Pronto. A MAVIS agora lê sua agenda, emails e drive.`,
  },
  {
    title: "6. Resumo Semanal Automático",
    body: `Toda SEXTA-FEIRA às 18h (configurável em .env: MAVIS_AUTO_WEEKLY_HOUR), a MAVIS roda automaticamente:

1. Lê estatísticas da semana via analytics
2. Pede ao Gemini um resumo executivo
3. Salva como relatório com periodo "AUTO YYYY-Sxx"
4. Aparece em Relatórios e nos gráficos de Analytics

Pra desligar: .env → MAVIS_AUTO_WEEKLY=0 (e reinicie backend)
Pra forçar agora: chame POST /api/reports/auto-weekly (ou crie um Workflow disparando isso)`,
  },
  {
    title: "7. Modo Proativo",
    body: `Em .env: MAVIS_PROATIVO=1
A MAVIS roda loop em background no app desktop. Ela te avisa por voz:
- Quando um lembrete chega na hora marcada
- Quando bateria <20% sem carregador (a cada 5 min)
- Quando próxima reunião do Google Calendar começa em 15 min

Customizar em mavis/skills/proactive.py`,
  },
  {
    title: "8. Importar relatórios antigos em massa",
    body: `Use POST /api/reports/import com:
  { "items": [{ "periodo": "...", "conteudo_relatorio": "..." }, ...] }

Ou na página Relatórios → ADICIONAR (cole texto manualmente).

Quanto mais relatórios você importar, mais ricos ficam os gráficos do Analytics.`,
  },
  {
    title: "9. Backup & Restore",
    body: `Os dados ficam todos em arquivos JSON na raiz /app/:
  banco_de_dados.json    (rotas)
  banco_relatorios.json  (relatórios)
  memoria_mavis.json     (conversa curta)
  long_memory.json       (fatos persistentes)
  reminders.json         (lembretes)
  todos.json, quick_notes.json, workflows.json, custom_commands.json

Para backup: zip esses arquivos. Para restore: cole de volta e reinicie o backend.
O .env tem backup automático em .env.bak a cada save pelo painel.`,
  },
  {
    title: "10. Solução de problemas",
    body: `❌ "Google app not verified": adicione seu email em Test users na OAuth consent screen
❌ portaudio.h not found: Linux 'sudo apt install portaudio19-dev'
❌ TTS retorna 403: atualizar 'pip install -U edge-tts' (>= 7.0)
❌ Cérebro responde "Rate limit": Gemini free tier = 5 req/min, aguarde 60s
❌ WhatsApp não abre: 'playwright install chromium' e escaneie o QR code uma vez
❌ Painel mostra "OFFLINE": verifique 'sudo supervisorctl status' e logs
❌ Voz não toca no browser: verifique permissões de áudio do site no Chrome/Firefox`,
  },
];

export default function Docs() {
  return (
    <div className="p-6 space-y-4 max-w-5xl">
      <div>
        <h1 className="font-display text-3xl">Documentação</h1>
        <p className="text-zinc-500 text-xs tracking-widest uppercase mt-1">
          // MANUAL OPERACIONAL · COMANDOS · CONFIGURAÇÃO
        </p>
      </div>

      {SECTIONS.map((s, i) => (
        <div key={i} className="panel">
          <div className="panel-header">
            <span className="flex items-center gap-2">
              <Book size={12} className="text-amber" /> {s.title}
            </span>
          </div>
          <pre className="p-5 whitespace-pre-wrap text-sm leading-relaxed text-zinc-200 font-mono">
            {s.body}
          </pre>
        </div>
      ))}

      <div className="panel p-4 text-[11px] text-zinc-500">
        <span className="text-amber tracking-widest uppercase">// SOBRE</span> MAVIS / Sexta-feira v4.2 — IA pessoal modular construída sobre Gemini 2.5 Flash, Edge TTS, Vosk, openWakeWord, Playwright, Google APIs e psutil. Painel web em React + FastAPI. App desktop em Python.
      </div>
    </div>
  );
}
