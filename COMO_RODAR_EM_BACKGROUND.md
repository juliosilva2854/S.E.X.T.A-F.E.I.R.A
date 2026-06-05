# Como rodar a Sexta-feira (Mavis) em background no seu PC

> O ambiente hospedado (preview) já roda o backend + frontend automaticamente. Este guia é
> para você manter o app rodando **sozinho** na sua máquina (Windows), inclusive as funções
> "desktop-only" (RPA Field Control e envio automático de WhatsApp via web.whatsapp.com), que
> precisam de um navegador visível e não funcionam em servidor headless.

## Pré-requisitos (instale uma vez)

- **Python 3.11+** (marque "Add Python to PATH" no instalador)
- **Node.js LTS** + **Yarn** (`npm install -g yarn`)
- **MongoDB Community Server** instalado **como serviço do Windows** ([download](https://www.mongodb.com/try/download/community))
  - Confirme com: `sc query MongoDB` (precisa aparecer)
- **Chrome** instalado (necessário para o RPA do Field Control / WhatsApp Web)
- **`backend\.env`** preenchido (CHAVE_GEMINI, MONGO_URL, FIELDCONTROL_*, WHATSAPP_*, etc.)

---

## ✅ Opção B — Inicialização automática + janela oculta (RECOMENDADA)

Sobe backend + frontend **em segundo plano** toda vez que você fizer logon no Windows.
Sem terminal aberto, sem prompt. Os scripts prontos estão em `scripts\`:

| Arquivo | Função |
|---|---|
| `scripts\preparar.bat` | Cria o venv do backend, instala dependências, gera o build do frontend (aponta para `http://localhost:8001`). Rode UMA vez. |
| `scripts\iniciar_oculto.vbs` | Lança MongoDB + backend (uvicorn :8001) + frontend (serve :3000) **sem janela visível** e abre o navegador depois de 6s. |
| `scripts\registrar_inicializacao.bat` | Registra a tarefa no **Agendador de Tarefas** para rodar o VBS ao fazer logon. |

### Passo a passo

1. **Abra o `cmd` na pasta do projeto** (`cd C:\caminho\para\sexta-feira`).
2. **Prepare o ambiente** (uma vez só):
   ```cmd
   scripts\preparar.bat
   ```
   Isso cria `backend\venv`, instala todas as deps Python + Node, e roda `yarn build` apontando
   para `http://localhost:8001` (criado automaticamente em `frontend\.env.production.local`).

3. **Teste agora, sem reiniciar**:
   ```cmd
   wscript scripts\iniciar_oculto.vbs
   ```
   Em ~6s o navegador abre em `http://localhost:3000` mostrando o painel.
   Cheque o status `[ONLINE]` no canto superior direito.

4. **Registre para iniciar sozinho** (rode como **Administrador**):
   ```cmd
   scripts\registrar_inicializacao.bat
   ```
   A partir de agora, toda vez que você logar no Windows a Sexta-feira sobe sozinha,
   sem terminal, e o painel fica em `http://localhost:3000`.

### Comandos úteis (após registrar)

```cmd
schtasks /run    /tn "SextaFeira"     :: inicia agora sem reiniciar
schtasks /query  /tn "SextaFeira"     :: ver status da tarefa
schtasks /delete /tn "SextaFeira" /f  :: remover a inicializacao automatica
```

Para parar tudo manualmente:
```cmd
taskkill /f /im python.exe   & :: mata o uvicorn
taskkill /f /im node.exe     & :: mata o serve
```

---

## Opção A — Serviço do Windows (NSSM) — alternativa robusta

Use se quiser que backend/frontend rodem mesmo **sem nenhum usuário logado**.
Instale o [NSSM](https://nssm.cc/download) (coloque `nssm.exe` no PATH) e rode como Administrador:

```cmd
scripts\install_windows_services.bat
```

Isso instala `SextaFeiraBackend` (uvicorn :8001) e `SextaFeiraFrontend` (serve :3000) como
serviços do Windows com auto-start. Para remover: `nssm remove SextaFeiraBackend confirm`.

> ⚠️ Limitação: RPA do Field Control e WhatsApp Web **precisam de sessão gráfica logada**
> (Playwright `headless=False`). Em modo serviço puro essas skills não funcionam — use a Opção B.

---

## Opção C — Docker Compose (Linux/servidor, SEM as funções desktop)

> Use só se NÃO precisar do RPA/WhatsApp visual. Bom só para o painel/Analytics.

```bash
docker compose up -d
```

(`docker-compose.yml` já está na raiz: sobe Mongo + backend + frontend.)

---

## Observações importantes

- **RPA Field Control e WhatsApp** precisam de navegador visível (`headless=False`) e de uma
  sessão logada → use a Opção B no Windows com sua sessão de usuário ativa.
- O **MongoDB** precisa estar rodando como serviço local (`net start MongoDB`).
- Os arquivos `.env` (backend) devem existir com as chaves corretas **antes** de rodar `preparar.bat`.
- O frontend é servido como **build estático** (não dev-server), então mudou código? Rode
  `cd frontend && yarn build` de novo.
- Para WhatsApp automático: na primeira execução, escaneie o QR do WhatsApp Web na pasta de
  sessão (`sessao_whatsapp\`) — depois fica logado.

## Troubleshooting rápido

| Sintoma | Causa | Solução |
|---|---|---|
| Painel abre mas mostra "OFFLINE" | `CHAVE_GEMINI` vazia | Edite `backend\.env` → restart |
| `Invalid Host header` | (só no preview, não local) | N/A — local não dá esse erro |
| Mapa de calor vazio | Mongo não subiu | `net start MongoDB` |
| Frontend chama URL errada | Build feito com `.env` errado | Apague `frontend\build` e `frontend\.env.production.local`, rode `preparar.bat` de novo |
| Porta 8001/3000 ocupada | Outro processo | `netstat -ano \| findstr :8001` → `taskkill /f /pid <PID>` |

## Wake-word — duas opções

A Sexta-feira tem **duas formas** de ativação por voz, e elas são **complementares**:

### A) Botão flutuante no painel (Web Speech API) — sempre disponível
- No canto inferior direito do painel há um botão de microfone (laranja se desligado).
- Clique para ativar. Diga "**Sexta-feira**" + comando (ex: "Sexta-feira, qual o clima hoje?").
- Funciona em **Chrome ou Edge** (Web Speech API). Firefox/Safari não suportam.
- A IA responde por voz (edge-tts neural, mesma usada no desktop loop).
- Não exige nada instalado no PC além do navegador.

### B) Loop de voz desktop (`sexta-feira.py`) — sempre ouvindo
- Roda como processo separado (não via Opção B, é um terminal próprio).
- Use quando quiser controlar o PC inteiro por voz (mouse, teclado, abrir apps, RPA).
- Inicie com:
  ```cmd
  cd C:\caminho\para\sexta-feira
  backend\venv\Scripts\activate.bat
  python sexta-feira.py
  ```
- **Wake-word default = "hey jarvis"** (limitação do openwakeword). Para "sexta-feira"
  você precisa treinar um modelo custom seguindo o guia em
  https://github.com/dscripka/openWakeWord#training-new-models — depois aponte
  `WAKE_WORD_MODEL=caminho/para/sexta-feira.tflite` no `backend\.env`.

> Dica: deixe os dois rodando juntos. O painel é para quando você está no PC; o loop
> desktop é para quando está com as mãos ocupadas em campo.
