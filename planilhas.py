import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
from datetime import datetime

def obter_aba_atual(cliente, nome_planilha):
    meses_texto = {
        1: "Jan", 2: "Fev", 3: "Mar", 4: "Abril", 5: "Maio", 6: "Jun",
        7: "Jul", 8: "Ago", 9: "Set", 10: "Out", 11: "Nov", 12: "Dezembro"
    }
    hoje = datetime.now()
    mes_str = meses_texto[hoje.month]
    ano_str = hoje.strftime("%y") 
    nome_aba_esperado = f"{mes_str}-{ano_str}"
    
    planilha_mestra = cliente.open(nome_planilha)
    return planilha_mestra.worksheet(nome_aba_esperado)

def preencher_km_faltantes():
    try:
        escopos = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        credenciais = ServiceAccountCredentials.from_json_keyfile_name('credenciais.json', escopos)
        cliente = gspread.authorize(credenciais)

        try:
            aba = obter_aba_atual(cliente, "Planilha KM - Julio Cesar MTFL")
        except gspread.exceptions.WorksheetNotFound:
            return "Senhor, não encontrei a aba deste mês na sua planilha."

        with open('banco_de_dados.json', 'r', encoding='utf-8') as f:
            db = json.load(f)

        dados = aba.get_all_values()
        atualizacoes_em_lote = []
        
        total_sem_km = 0
        preenchidos_com_sucesso = 0
        rotas_desconhecidas = set() # Usamos 'set' para não repetir nomes se a mesma rota faltar 5 vezes

        for i, linha in enumerate(dados):
            linha_numero = i + 1 
            
            if linha_numero < 6 or len(linha) < 4:
                continue
                
            origem = linha[1].strip().upper() if len(linha) > 1 else ""
            destino = linha[3].strip().upper() if len(linha) > 3 else ""
            km_rodado = linha[7].strip() if len(linha) > 7 else ""
            
            if origem != "" and destino != "" and km_rodado == "":
                total_sem_km += 1 
                chave_rota = f"{origem}_{destino}"
                
                if chave_rota in db.get("rotas_km", {}):
                    km_correto = db["rotas_km"][chave_rota]
                    atualizacoes_em_lote.append({
                        'range': f'H{linha_numero}',
                        'values': [[km_correto]]
                    })
                    preenchidos_com_sucesso += 1
                else:
                    # Regista o nome da rota que ela não sabe
                    rotas_desconhecidas.add(f"de {origem} para {destino}")

        if total_sem_km == 0:
            return "Excelente, senhor. Não encontrei nenhuma rota sem quilometragem na planilha de hoje."
            
        if atualizacoes_em_lote:
            aba.batch_update(atualizacoes_em_lote)
            
        # RELATÓRIO FALADO INTELIGENTE
        if total_sem_km == preenchidos_com_sucesso:
            return f"Identifiquei {total_sem_km} rotas sem quilometragem. Todas foram preenchidas com sucesso, senhor."
        else:
            faltaram = total_sem_km - preenchidos_com_sucesso
            # Pega em até 3 rotas para não fazer um discurso gigante se faltarem 20
            exemplos = ", e ".join(list(rotas_desconhecidas)[:3])
            
            mensagem = f"Senhor, preenchi {preenchidos_com_sucesso} rotas. Mas não consegui preencher {faltaram}, pois não constam no banco de dados. Ficaram pendentes rotas como: {exemplos}."
            return mensagem

    except Exception as e:
        print(f"\n[ERRO PLANILHA]: {e}")
        return "Houve uma falha de comunicação com os servidores do Google Sheets, senhor."