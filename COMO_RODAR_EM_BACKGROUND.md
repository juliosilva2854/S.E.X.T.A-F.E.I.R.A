# Como rodar a Sexta-feira (Mavis) em background no seu PC

> O ambiente hospedado (preview) já roda o backend + frontend automaticamente. Este guia é
> para você manter o app rodando **sozinho** na sua máquina (Windows), inclusive as funções
> "desktop-only" (RPA Field Control e envio automático de WhatsApp via web.whatsapp.com), que
> precisam de um navegador visível e não funcionam em servidor headless.

## Opção A — Serviço do Windows (NSSM)  ✅ recomendado p/ rodar sempre
1. Instale o [NSSM](https://nssm.cc/download) e coloque `nssm.exe` no PATH.
2. Backend (FastAPI):
   ```
   nssm install SextaFeiraBackend "C:\caminho\python.exe" "-m uvicorn server:app --host 0.0.0.0 --port 8001"
   nssm set SextaFeiraBackend AppDirectory "C:\caminho\backend"
   nssm start SextaFeiraBackend
   ```
3. Frontend (build estático servido):
   ```
   cd frontend && yarn build
   nssm install SextaFeiraFront "C:\caminho\npx.cmd" "serve -s build -l 3000"
   nssm start SextaFeiraFront
   ```
4. Os serviços sobem junto com o Windows, sem terminal aberto.

## Opção B — Inicialização automática + janela oculta
- Crie um `.bat` que ativa o venv e roda `uvicorn ... --port 8001` e `serve -s build`.
- Use o **Agendador de Tarefas** do Windows: "Ao fazer logon", ação = o `.bat`, marcar
  "Executar com privilégios mais altos" e "Oculto".

## Opção C — Docker Compose (Linux/servidor, SEM as funções desktop)
> Use só se NÃO precisar do RPA/WhatsApp visual. Bom para o painel/Analytics.
```yaml
services:
  mongo:    { image: mongo:7, volumes: ["mongo:/data/db"] }
  backend:  { build: ./backend, env_file: backend/.env, ports: ["8001:8001"], depends_on: [mongo] }
  frontend: { build: ./frontend, ports: ["3000:3000"], depends_on: [backend] }
volumes: { mongo: {} }
```

## Observações importantes
- **RPA Field Control e WhatsApp** precisam de navegador visível (`headless=False`) e de uma
  sessão logada → use a Opção A/B no Windows com sua sessão de usuário ativa.
- O **MongoDB** precisa estar rodando (serviço local ou container).
- Os arquivos `.env` (backend e frontend) devem existir com as chaves corretas.
- Para WhatsApp automático: na primeira execução, escaneie o QR do WhatsApp Web na pasta de
  sessão (`WHATSAPP_SESSION_DIR`) — depois fica logado.
