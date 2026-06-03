import asyncio
import edge_tts
import pygame
import os
import json
import pyaudio
import time

import speech_recognition as sr
from vosk import Model, KaldiRecognizer, SetLogLevel
from duckduckgo_search import DDGS
from google import genai 

# Importando nossos próprios módulos modulares
import config
import rotinas

SetLogLevel(-1)

# ==========================================
# MÓDULO DE VOZ E AUDIÇÃO
# ==========================================
def limpar_tela():
    os.system('cls' if os.name == 'nt' else 'clear')

async def gerar_audio(texto, arquivo_saida="resposta.mp3"):
    communicate = edge_tts.Communicate(texto, config.VOZ_SINTETIZADOR)
    await communicate.save(arquivo_saida)

def falar(texto, modelo_interrupcao=None):
    print(f"\n{config.NOME_IA}: {texto}")
    arquivo = "resposta.mp3"
    asyncio.run(gerar_audio(texto, arquivo))
    
    pygame.mixer.init()
    pygame.mixer.music.load(arquivo)
    pygame.mixer.music.play()
    
    interrompido = False
    
    if modelo_interrupcao is not None:
        reconhecedor = KaldiRecognizer(modelo_interrupcao, 16000)
        p = pyaudio.PyAudio()
        try:
            stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=8000)
            stream.start_stream()
            while pygame.mixer.music.get_busy():
                data = stream.read(4000, exception_on_overflow=False)
                if reconhecedor.AcceptWaveform(data):
                    res = json.loads(reconhecedor.Result())
                    txt = res.get("text", "")
                    if any(apelido in txt for apelido in ["sexta-feira", "sexta feira", "sexta"]):
                        pygame.mixer.music.stop() 
                        interrompido = True
                        break
            stream.stop_stream()
            stream.close()
            p.terminate()
        except Exception:
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
    else:
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
            
    pygame.mixer.quit()
    if os.path.exists(arquivo):
        try: os.remove(arquivo)
        except: pass
        
    return interrompido 

def ouvir_comando():
    recognizer = sr.Recognizer()
    recognizer.pause_threshold = config.PAUSE_THRESHOLD 
    
    with sr.Microphone() as source:
        print("\n[ Escutando... ]", end="\r") 
        recognizer.adjust_for_ambient_noise(source, duration=1.0)
        try:
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=15)
            print("[ Processando... ]      ", end="\r")
            return recognizer.recognize_google(audio, language="pt-BR").lower()
        except sr.UnknownValueError:
            print("\n[AVISO]: Não entendi o que foi dito. Som ininteligível.")
            return ""
        except sr.RequestError as e:
            print(f"\n[ERRO DE INTERNET/GOOGLE]: {e}")
            return ""
        except Exception as e:
            print(f"\n[ERRO NO MICROFONE]: {e}")
            return ""

def vigia_offline(modelo):
    reconhecedor = KaldiRecognizer(modelo, 16000)
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=8000)
    stream.start_stream()
    
    print(f"\n[ Radar offline ] Diga '{config.NOME_IA}'.")
    while True:
        data = stream.read(4000, exception_on_overflow=False)
        if reconhecedor.AcceptWaveform(data):
            res = json.loads(reconhecedor.Result())
            txt = res.get("text", "")
            if any(apelido in txt for apelido in ["sexta-feira", "sexta feira", "sexta"]):
                stream.stop_stream()
                stream.close()
                p.terminate()
                return True

# ==========================================
# MÓDULO COGNITIVO (MEMÓRIA E DB)
# ==========================================
def carregar_memoria_e_db():
    # Carrega a memória de conversa
    historico = []
    if os.path.exists(config.ARQUIVO_MEMORIA):
        try:
            with open(config.ARQUIVO_MEMORIA, 'r', encoding='utf-8') as f:
                historico = json.load(f)
        except: pass
        
    # Carrega o banco de dados (A grande novidade!)
    dados_db = "{}"
    if os.path.exists(config.ARQUIVO_DB):
        try:
            with open(config.ARQUIVO_DB, 'r', encoding='utf-8') as f:
                dados_db = f.read()
        except: pass
        
    return historico, dados_db

def salvar_memoria(historico):
    with open(config.ARQUIVO_MEMORIA, 'w', encoding='utf-8') as f:
        json.dump(historico[-15:], f, ensure_ascii=False, indent=4)

def pensar(comando_usuario, historico, banco_de_dados_str):
    palavras_tempo_real = ["hoje", "agora", "notícia", "clima", "tempo", "dólar", "previsão", "temperatura"]
    contexto_extra = ""
    
    if any(p in comando_usuario for p in palavras_tempo_real):
        print("[ Acessando rede global... ]", end="\r")
        try:
            resultados = DDGS().text(comando_usuario, region='br-pt', safesearch='moderate', max_results=1)
            for res in resultados:
                contexto_extra += f"\n[DADO AO VIVO]: {res['title']} - {res['body']}"
        except: pass

    print(f"[ {config.NOME_IA} analisando... ]      ", end="\r")
    
    instrucoes = f"""Você é a {config.NOME_IA}, uma inteligência artificial corporativa avançada.
    Regras de Ouro:
    1. Respostas ágeis, conversacionais e diretas.
    2. Chame o usuário de 'senhor'.
    3. Nunca use asteriscos (**) ou emojis.
    4. Se fizer uma pergunta ao usuário, termine EXATAMENTE com a tag '[ESPERAR]'.
    
    BANCO DE DADOS ATUAL DO SISTEMA:
    {banco_de_dados_str}
    (Use as informações acima caso o usuário pergunte sobre distâncias, rotas ou planilhas armazenadas)."""

    try:
        client = genai.Client(api_key=config.CHAVE_GEMINI)
        
        conversa_completa = instrucoes + "\n\n"
        for msg in historico:
            conversa_completa += f"{msg['role']}: {msg['texto']}\n"
            
        conversa_completa += f"Usuário: {comando_usuario} {contexto_extra}\n{config.NOME_IA}: "
        
        resposta = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=conversa_completa
        )
        
        texto_resposta = resposta.text
        
        historico.append({'role': 'Usuário', 'texto': comando_usuario})
        historico.append({'role': config.NOME_IA, 'texto': texto_resposta})
        salvar_memoria(historico)
        
        return texto_resposta, historico
        
    except Exception as e:
        print(f"\n[ERRO CRÍTICO]: {e}")
        time.sleep(5) 
        return "Tive um problema na sinapse com os servidores de nova geração, senhor.", historico

# ==========================================
# LOOP PRINCIPAL DO SISTEMA
# ==========================================
if __name__ == "__main__":
    limpar_tela()
    print("=======================================")
    print(f"            S.E.X.T.A - F.E.I.R.A          ")
    print("=======================================\n")
        
    try:
        modelo_offline = Model("model")
    except Exception:
        print("ERRO: Pasta 'model' do Vosk não encontrada.")
        exit()
        
    historico_atual, banco_de_dados = carregar_memoria_e_db()
    falar("Pronta para operar, senhor.")
    
    manter_ouvido_aberto = False 
    
    while True:
        if not manter_ouvido_aberto:
            vigia_offline(modelo_offline)
            
        limpar_tela()
        print("=======================================")
        print(f"       S.E.X.T.A - F.E.I.R.A          ")
        print("======================================\n")
            
        if not manter_ouvido_aberto:
            falar("Pois não senhor?") 
            
        comando = ouvir_comando()
        
        if comando:
            limpar_tela()
            print("=======================================")
            print(f"       S.E.X.T.A - F.E.I.R.A          ")
            print("=====================================\n")
            print(f"Você: {comando}")
            
            if "desligar" in comando:
                falar("Desligando núcleos e encerrando rotinas de background. Até logo, senhor.")
                break

            else:
                # 1. Roteador de Ações Físicas
                resposta_da_acao = rotinas.executar_rotina_local(comando)
                
                texto_final = ""
                if resposta_da_acao != "":
                    texto_final = resposta_da_acao
                else:
                    # 2. Cérebro Neural (com acesso ao JSON de rotas)
                    texto_final, historico_atual = pensar(comando, historico_atual, banco_de_dados)
                
                # 3. Lógica de conversa contínua
                if "[ESPERAR]" in texto_final:
                    manter_ouvido_aberto = True
                    texto_final = texto_final.replace("[ESPERAR]", "").strip()
                elif texto_final.strip().endswith('?'):
                    manter_ouvido_aberto = True
                else:
                    manter_ouvido_aberto = False
                
                # 4. Falar resposta
                foi_interrompida = falar(texto_final, modelo_interrupcao=modelo_offline)
                if foi_interrompida:
                    manter_ouvido_aberto = True
                    
        else:
            limpar_tela()
            print("=======================================")
            print(f"       S.E.X.T.A - F.E.I.R.A          ")
            print("=====================================\n")
            foi_interrompida = falar("Retornando ao modo de prontidão.", modelo_interrupcao=modelo_offline)
            manter_ouvido_aberto = foi_interrompida