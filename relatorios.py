import config
from datetime import datetime, timedelta
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from playwright.sync_api import sync_playwright
from google import genai 
import re
import json
import os
import time

# ==========================================
# 1. MOTOR DE INTERPRETAÇÃO DE DATAS
# ==========================================
def interpretar_data_comando(comando):
    hoje = datetime.now()
    inicio = hoje
    fim = hoje

    comando_min = comando.lower()
    
    meses = {
        "janeiro": 1, "fevereiro": 2, "março": 3, "marco": 3, "abril": 4,
        "maio": 5, "junho": 6, "julho": 7, "agosto": 8, "setembro": 9,
        "outubro": 10, "novembro": 11, "dezembro": 12
    }

    padrao_datas = re.search(r"dia (\d{1,2}) de (\w+) at. (?:o )?dia (\d{1,2}) de (\w+)", comando_min)

    if padrao_datas:
        d1, m1, d2, m2 = padrao_datas.groups()
        if m1 in meses and m2 in meses:
            try:
                inicio = hoje.replace(month=meses[m1], day=int(d1))
                fim = hoje.replace(month=meses[m2], day=int(d2))
                print(f"[Motor de Tempo] Período customizado detetado: {inicio.strftime('%d/%m/%Y')} a {fim.strftime('%d/%m/%Y')}")
            except ValueError:
                pass
    
    elif "semana passada" in comando_min:
        inicio = hoje - timedelta(days=hoje.weekday() + 7)
        fim = inicio + timedelta(days=4)
    elif "dessa semana" in comando_min or "desta semana" in comando_min:
        inicio = hoje - timedelta(days=hoje.weekday()) 
        fim = hoje
    elif "desse mês" in comando_min or "deste mês" in comando_min:
        inicio = hoje.replace(day=1)
        fim = hoje
    
    inicio = inicio.replace(hour=0, minute=0, second=0, microsecond=0)
    fim = fim.replace(hour=23, minute=59, second=59, microsecond=0)
    
    return inicio.strftime("%d/%m/%Y"), fim.strftime("%d/%m/%Y"), inicio, fim

# ==========================================
# 2. BANCO DE DADOS LOCAL
# ==========================================
def salvar_relatorio_bd(data_inicio, data_fim, relatorio_texto):
    arquivo_bd = "banco_relatorios.json"
    dados = []
    
    if os.path.exists(arquivo_bd):
        try:
            with open(arquivo_bd, "r", encoding="utf-8") as f:
                dados = json.load(f)
        except Exception as e:
            print(f"[Aviso do Banco] Falha ao ler banco antigo, criando um novo. Erro: {e}")
            pass
    
    novo_registro = {
        "gerado_em": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "periodo": f"{data_inicio} a {data_fim}",
        "conteudo_relatorio": relatorio_texto
    }
    
    dados.append(novo_registro)
    
    with open(arquivo_bd, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=4)
    print(f"[Banco de Dados] Relatório do período {data_inicio} a {data_fim} salvo com sucesso.")

# ==========================================
# 3. EXTRATOR DA PLANILHA DE REEMBOLSO
# ==========================================
def buscar_tickets_da_planilha(data_inicio_str, data_fim_str, inicio_dt, fim_dt):
    print(f"[Planilha] Procurando tickets de {data_inicio_str} até {data_fim_str}...")
    try:
        escopos = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        credenciais = ServiceAccountCredentials.from_json_keyfile_name('credenciais.json', escopos)
        cliente = gspread.authorize(credenciais)
        
        meses_texto = {1: "Jan", 2: "Fev", 3: "Mar", 4: "Abril", 5: "Maio", 6: "Jun", 7: "Jul", 8: "Ago", 9: "Set", 10: "Out", 11: "Nov", 12: "Dezembro"}
        nome_aba = f"{meses_texto[fim_dt.month]}-{fim_dt.strftime('%y')}"
        
        aba = cliente.open("Planilha KM - Julio Cesar MTFL").worksheet(nome_aba)
        dados = aba.get_all_values()
        
        tickets_encontrados = []
        
        for linha in dados:
            if len(linha) >= 7:
                data_linha = linha[0].strip()
                destino = linha[3].strip()
                tipo_visita = linha[5].strip()
                ticket = linha[6].strip()
                
                if not data_linha or data_linha == "Data" or ticket == "":
                    continue
                
                try:
                    dt_atual = datetime.strptime(data_linha, "%d/%m/%Y")
                    if inicio_dt <= dt_atual <= fim_dt:
                        tickets_encontrados.append({
                            "data": data_linha,
                            "destino": destino,
                            "tipo": tipo_visita,
                            "ticket": ticket,
                            "descricao": ""
                        })
                except ValueError:
                    continue 
        
        tickets_encontrados.sort(key=lambda x: datetime.strptime(x["data"], "%d/%m/%Y"))
        return tickets_encontrados
    except Exception as e:
        print(f"Erro na planilha: {e}")
        return []

# ==========================================
# 4. ROBÔ NAVEGADOR FIELDCONTROL (RPA)
# ==========================================
def extrair_descricoes_fieldcontrol(tickets_list):
    print(f"[FieldControl] Iniciando robô navegador para {len(tickets_list)} tickets...")
    
    with sync_playwright() as p:
        navegador = p.chromium.launch(headless=False) 
        # CORREÇÃO: Força o navegador a rodar em resolução Full HD para evitar elementos fora do viewport
        contexto = navegador.new_context(viewport={"width": 1920, "height": 1080}) 
        pagina = contexto.new_page()
        
        try:
            print(" -> Acessando autenticador...")
            pagina.goto("https://app.fieldcontrol.com.br/autenticador-v2/#/login")
            
            pagina.fill('input[type="email"]', config.FIELDCONTROL_EMAIL)
            pagina.keyboard.press("Enter") 
            
            pagina.wait_for_selector('input[type="password"]', timeout=10000)
            pagina.fill('input[type="password"]', config.FIELDCONTROL_SENHA)
            pagina.keyboard.press("Enter") 
            
            print(" -> Autenticação enviada. Aguardando painel...")
            pagina.wait_for_url("**/atividades**", timeout=20000)
            
            def destruir_popups():
                try:
                    if pagina.locator('text="Lançamento de múltiplos"').is_visible(timeout=100):
                        pagina.keyboard.press("Escape")
                    
                    botao = pagina.locator('[data-cy="fc-modal-right-button"]')
                    if botao.is_visible(timeout=100):
                        botao.click(force=True)
                except: pass
            
            pagina.wait_for_timeout(4000)
            destruir_popups()
            print("[SUCESSO] Base infiltrada! Iniciando extração profunda...\n")
            
            for item in tickets_list:
                ticket_id = item["ticket"]
                print(f" -> {item['data']} | Extraindo OS: {ticket_id}")
                
                try:
                    pagina.goto("https://app.fieldcontrol.com.br/#/atividades")
                    pagina.wait_for_timeout(3500)
                    destruir_popups() 
                    
                    botao_filtrar = pagina.locator('[data-cy="filter-button"]')
                    try:
                        botao_filtrar.click(timeout=3000)
                    except:
                        destruir_popups()
                        botao_filtrar.click(force=True)
                        
                    pagina.wait_for_timeout(1500)
                    
                    campo_busca = pagina.locator('input[placeholder="Buscar..."]').first
                    if not campo_busca.is_visible():
                        pagina.locator('text="Por identificador"').click(force=True)
                        pagina.wait_for_timeout(1000)
                    
                    campo_busca.click(force=True)
                    pagina.keyboard.press("Control+A")
                    pagina.keyboard.press("Backspace")
                    campo_busca.fill(ticket_id)
                    pagina.wait_for_timeout(2000) 
                    
                    pagina.keyboard.press("Escape")
                    pagina.wait_for_timeout(1500)
                    
                    # Clique Primeiro Editar (Tabela CDK)
                    linha_resultado = pagina.locator('cdk-row').first
                    linha_resultado.locator('cdk-cell.cdk-column-action palantir-button').first.click(force=True)
                    pagina.wait_for_timeout(2000)
                    
                    # Clique Segundo Editar (Painel Superior Mapeado)
                    botao_segundo_editar = pagina.locator('order-task-card palantir-toolbar-suffix palantir-button:nth-child(2)')
                    try:
                        botao_segundo_editar.click(timeout=3000, force=True)
                    except:
                        pagina.locator('palantir-button').filter(has=pagina.locator('path[d^="M2.999"]')).last.click(force=True)
                        
                    pagina.wait_for_timeout(2000)
                    
                    # Extração Avançada via DOM JavaScript
                    textareas = pagina.locator('textarea').element_handles()
                    if textareas:
                        ultimo_textarea = textareas[-1]
                        texto_conclusao = pagina.evaluate("(element) => element.value", ultimo_textarea)
                        texto_limpo = texto_conclusao.strip() if texto_conclusao else ""
                        item["descricao"] = texto_limpo if texto_limpo else "Concluída sem descrição."
                    else:
                        item["descricao"] = "Campo de descrição não encontrado."
                        
                    resumo_terminal = item['descricao'].replace('\n', ' ')
                    print(f"    [+] Resumo lido: {resumo_terminal[:50]}...")

                except Exception as e:
                    print(f"    [!] Erro na OS {ticket_id}: Não foi possível navegar nos painéis. Erro: {e}")
                    item["descricao"] = "Serviço realizado." 
                
            print("\n[RPA] Extração concluída com sucesso!")
            
        except Exception as e:
            print(f"\n[ERRO FATAL DO ROBÔ]: {e}")
            
        finally:
            navegador.close()
            
    return tickets_list 

# ==========================================
# 5. COMPILADOR DE REDAÇÃO (IA)
# ==========================================
def formatar_relatorio_com_ia(tickets, data_inicio_str, data_fim_str):
    print("[IA] Redigindo relatório executivo...")
    
    dados_brutos = ""
    for t in tickets:
        dados_brutos += f"Data: {t['data']} | Unidade: {t['destino']} | Visita: {t['tipo']} | O que foi feito: {t['descricao']}\n"
        
    prompt = f"""
    Você é um assistente corporativo de alta precisão. Seu objetivo é transformar dados brutos de ordens de serviço em um diário narrativo coeso, fluido e elegante em primeira pessoa (como se o próprio técnico Julio Cesar estivesse relatando o seu dia de trabalho).
    
    Siga RIGOROSAMENTE este formato visual (com quebras de linha duplas entre os dias e mantendo os calendários):
    🗓️ {data_inicio_str} - {data_fim_str} 🗓️
    
    📅 [Data 1]
    [Texto narrativo único e integrado de todas as atividades do dia]
    
    📅 [Data 2]
    [Texto narrativo único e integrado de todas as atividades do dia]
    
    DIRETRIZES SEVERAS DE REDAÇÃO (SIGA À RISCA):
    1. PARÁGRAFO ÚNICO POR DIA: É terminantemente PROIBIDO criar tópicos ou uma frase isolada por chamado. Se o técnico fez vários atendimentos no mesmo dia, junte todos em um único texto corrido e fluido sobre o dia todo.
    2. CONECTORES SEQUENCIAIS NARRATIVOS: Conecte os atendimentos do dia usando expressões como: "Início o dia realizando...", "após isso sigo para...", "em seguida faço...", "na sequência realizo...", "encerro as atividades do dia com...".
    3. PROIBIÇÃO DE MARCAÇÕES DE TEMPO (REGRAS EXPLICITAS): Não utilize NENHUMA menção a períodos do dia, como "pela manhã", "durante a tarde", "no fim da noite", "finalizo a manhã", "fim da tarde". Foque na sequência cronológica das ações, cobrindo o dia todo de forma contínua.
    4. PROIBIÇÃO DE PALAVRAS DE DEDICAÇÃO: Não use termos que indiquem foco exclusivo ou desperdício de tempo como "me dediquei a", "foi inteiramente dedicado a", "focado em". Vá direto para a ação (ex: em vez de "meu dia foi inteiramente dedicado a um atendimento", use "Realizo um atendimento técnico na unidade...").
    5. LIMPEZA DE TERMOS DO SISTEMA:
       - Nunca escreva "Visita Técnica". Substitua por "atendimento técnico" ou "visitas técnicas".
       - Nunca escreva "Visita Preventiva". Substitua por "atendimento preventivo" ou "manutenção preventiva".
       - Nunca escreva a palavra "Outros". Ignore esse termo e use o contexto da ação (ex: "realizo a entrega de insumos", "efetuo a troca de teclado").
    6. PROIBIÇÃO DE TEXTOS PADRÃO (FILTRO CRÍTICO): Remova COMPLETAMENTE qualquer variação das frases: "Deixei a unidade com o sistema funcionando normalmente", "sistema operante", "deixo funcionando normalmente ok", ou menções sobre deixar com supervisão. Foque apenas na ação técnica realizada.
    7. REMOVA PATRIMÔNIOS E NOMES: Delete números de patrimônio e nomes de funcionários locais. Isso polui o resumo.
    
    DADOS BRUTOS COLETADOS:
    {dados_brutos}
    """
    
    tentativas = 3
    for tentativa in range(tentativas):
        try:
            client = genai.Client(api_key=config.CHAVE_GEMINI)
            resposta = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt
            )
            return resposta.text
        except Exception as e:
            erro_str = str(e)
            if ("503" in erro_str or "429" in erro_str or "RESOURCE_EXHAUSTED" in erro_str) and tentativa < tentatives - 1:
                tempo_espera = 30 if ("429" in erro_str or "RESOURCE_EXHAUSTED" in erro_str) else 5
                print(f"    [!] Servidor ocupado. Aguardando {tempo_espera} segundos... (Tentativa {tentativa + 1}/{tentativas})")
                time.sleep(tempo_espera)
            else:
                return f"Senhor, os dados foram extraídos, mas houve falha na geração do texto pela IA. Erro: {e}"

# ==========================================
# 6. GATILHO DA ROTINA PRINCIPAL
# ==========================================
def gerar_resumo(comando):
    data_inicio_str, data_fim_str, dt_i, dt_f = interpretar_data_comando(comando)
    tickets = buscar_tickets_da_planilha(data_inicio_str, data_fim_str, dt_i, dt_f)
    
    if not tickets:
        return f"Senhor, não encontrei nenhum ticket preenchido na sua planilha para o período de {data_inicio_str} a {data_fim_str}."
    
    tickets_preenchidos = extrair_descricoes_fieldcontrol(tickets)
    texto_final = formatar_relatorio_com_ia(tickets_preenchidos, data_inicio_str, data_fim_str)
    
    print("\n=======================================")
    print("        RELATÓRIO PRONTO               ")
    print("=======================================\n")
    print(texto_final)
    print("\n=======================================\n")
    
    if "Erro:" not in texto_final and "falha na geração" not in texto_final:
        salvar_relatorio_bd(data_inicio_str, data_fim_str, texto_final)
    else:
        print("[Banco de Dados] Salvamento abortado devido a falha na IA.")
        
    return "O relatório está concluído, senhor. O texto foi gerado, impresso na tela e guardado com sucesso no nosso banco de dados local."