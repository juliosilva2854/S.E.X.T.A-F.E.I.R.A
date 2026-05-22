import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import os

def treinar_mavis():
    print("=======================================================")
    print("   S.E.X.T.A - F.E.I.R.A - PROTOCOLO DE APRENDIZADO    ")
    print("=====================================================\n")
    print("[1] Conectando aos servidores da Google...")
    
    try:
        escopos = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        # Cadeado de Diretoria: Força a usar a mesma pasta onde este script está guardado
        diretoria_atual = os.path.dirname(os.path.abspath(__file__))
        caminho_credenciais = os.path.join(diretoria_atual, 'credenciais.json')
        caminho_db = os.path.join(diretoria_atual, 'banco_de_dados.json')

        credenciais = ServiceAccountCredentials.from_json_keyfile_name(caminho_credenciais, escopos)
        cliente = gspread.authorize(credenciais)
        planilha = cliente.open("Planilha KM - Julio Cesar MTFL")
    except Exception as e:
        print(f"ERRO DE CONEXÃO.\nDetalhe: {e}")
        return

    rotas_aprendidas = {}
    abas_ignoradas = [""] # Deixe em branco se não quiser ignorar nada

    print("[2] Iniciando varredura profunda com Filtros...\n")
    
    for aba in planilha.worksheets():
        if aba.title in abas_ignoradas:
            print(f" [X] Ignorando aba restrita/oculta: {aba.title}")
            continue
            
        print(f" -> Lendo memórias da aba: {aba.title}...")
        dados = aba.get_all_values()
        
        for linha in dados:
            if len(linha) >= 8:
                origem = linha[1].strip().upper()
                destino = linha[3].strip().upper()
                km_str = linha[7].strip().replace(',', '.')
                
                # Filtro de Pureza
                if origem == "ORIGEM" or destino == "DESTINO" or origem == "" or destino == "":
                    continue
                if len(origem) < 2 or len(destino) < 2:
                    continue

                try:
                    km_valor = float(km_str)
                    if km_valor > 0:
                        chave = f"{origem}_{destino}"
                        if km_valor.is_integer():
                            km_valor = int(km_valor)
                        # Memoriza sempre o valor mais recente encontrado
                        rotas_aprendidas[chave] = km_valor
                except ValueError:
                    pass

    print("\n[3] Leitura concluída. Cruzando com os dados existentes...")

    # Carrega a base de dados atual para comparar
    if os.path.exists(caminho_db):
        with open(caminho_db, 'r', encoding='utf-8') as f:
            try:
                db = json.load(f)
            except:
                db = {}
    else:
        db = {}

    if "rotas_km" not in db:
        db["rotas_km"] = {}

    # RASTREADOR DE NOVIDADES (Informa o utilizador sobre o que mudou)
    rotas_existentes = db["rotas_km"]
    novas = 0
    atualizadas = 0

    print("---------------------------------------")
    for chave, valor in rotas_aprendidas.items():
        if chave not in rotas_existentes:
            print(f" [NOVA ROTA APRENDIDA]: {chave} -> {valor} km")
            novas += 1
        elif rotas_existentes[chave] != valor:
            print(f" [ROTA ATUALIZADA]: {chave} mudou de {rotas_existentes[chave]} para {valor} km")
            atualizadas += 1
            
    if novas == 0 and atualizadas == 0:
        print(" Nenhuma rota nova ou alteração detetada nesta varredura.")
    print("---------------------------------------")

    # Injeta as novas rotas e guarda
    db["rotas_km"].update(rotas_aprendidas)

    print(f"[4] A guardar alterações no ficheiro absoluto: {caminho_db}")
    with open(caminho_db, 'w', encoding='utf-8') as f:
        json.dump(db, f, ensure_ascii=False, indent=4)

    # NOVO: Devolve um relatório para a IA falar
    if novas == 0 and atualizadas == 0:
        return "Varredura concluída, senhor. Não encontrei nenhuma rota nova para aprender no seu histórico."
    else:
        return f"Protocolo concluído. Inseri {novas} rotas novas na minha memória, e atualizei {atualizadas} rotas existentes, senhor."

if __name__ == "__main__":
    # Quando executado no terminal, apenas imprime a resposta
    print(treinar_mavis())