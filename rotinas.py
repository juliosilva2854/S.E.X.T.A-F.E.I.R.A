import webbrowser
import os
import threading
import planilhas
import aprender_rotas
import relatorios

def abrir_site_background(url):
    webbrowser.open(url)

def executar_rotina_local(comando):
    """Analisa o comando de voz e executa rotinas locais ou na nuvem."""
    comando = comando.lower()
    
    # 1. Dicionário de Sites Rápidos
    sites_conhecidos = {
        "youtube": "https://youtube.com",
        "google": "https://google.com",
        "netflix": "https://netflix.com",
        "github": "https://github.com",
        "whatsapp": "https://web.whatsapp.com"
    }

    for nome_site, url in sites_conhecidos.items():
        if nome_site in comando and ("abrir" in comando or "acesse" in comando):
            threading.Thread(target=abrir_site_background, args=(url,), daemon=True).start()
            return f"Abrindo {nome_site.capitalize()} imediatamente, senhor."

    # 2. Rotina do Servidor Local
    if "servidor" in comando and ("iniciar" in comando or "ligar" in comando):
        caminho_do_servidor = r"C:\Users\Computador\Desktop\Iniciar-sistema.bat"
        try:
            threading.Thread(target=lambda: os.startfile(caminho_do_servidor), daemon=True).start()
            return "Servidor local iniciado em segundo plano."
        except:
            return "Falha ao localizar o arquivo do servidor."

    # 3. Protocolo de Trabalho (FieldControl + Docs)
    if "protocolo" in comando and "trabalho" in comando:
        urls_trabalho = [
            "https://app.fieldcontrol.com.br/#/painel-de-controle/listagem",
            "https://app.fieldcontrol.com.br/#/equipamentos",
            "https://docs.google.com/spreadsheets/d/1BkAHzN9aoWOyb0iZXAlcTvkaj0mFd7AyPohDa0Sbhn4/edit?gid=1697523880#gid=1697523880"
        ]
        for url in urls_trabalho:
            threading.Thread(target=abrir_site_background, args=(url,), daemon=True).start()
        return "Protocolo de trabalho ativado. Módulos do FieldControl e planilhas em carregamento."

    # ==========================================
    # GATILHO DA PLANILHA 
    # ==========================================
    if "atualizar planilha" in comando or "preencher quilometragem" in comando or "atualizar plan" in comando or "fazer planilha" in comando or "preencher planilha" in comando:
        return planilhas.preencher_km_faltantes()

    # ==========================================
    # GATILHO DE APRENDIZAGEM (NOVO)
    # ==========================================
    if "aprender rotas" in comando or "estudar rotas" in comando:
        return aprender_rotas.treinar_mavis()

    # ==========================================
    # GATILHO DO RELATÓRIO SEMANAL
    # ==========================================
    if "gerar relatório" in comando or "resumo da semana" in comando:
        return relatorios.gerar_resumo(comando)

    return ""