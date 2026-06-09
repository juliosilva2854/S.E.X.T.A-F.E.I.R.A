import os
import zipfile
import sys

# Tenta importar o requests, que já estará instalado pelo backend/venv
try:
    import requests
except ImportError:
    print("A biblioteca 'requests' não foi encontrada. Instalando...")
    os.system(f"{sys.executable} -m pip install requests")
    import requests

# Configurações de caminhos dinâmicos
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGET_DIR = os.path.join(BASE_DIR, 'model')
OUTPUT_ZIP = os.path.join(BASE_DIR, 'model.zip')
GOOGLE_DRIVE_FILE_ID = '1rIj4YNfUDZI_WgV7jCcHYkAHQv1dVRGH'

def download_file_from_google_drive(file_id, destination):
    print("Iniciando o download do modelo de voz (Isso pode levar alguns minutos dependendo da sua internet)...")
    url = "https://docs.google.com/uc?export=download&confirm=t"
    session = requests.Session()
    
    response = session.get(url, params={'id': file_id}, stream=True)
    token = get_confirm_token(response)

    if token:
        params = {'id': file_id, 'confirm': token}
        response = session.get(url, params=params, stream=True)

    save_response_content(response, destination)
    print("\nDownload do modelo concluído com sucesso!")

def get_confirm_token(response):
    for key, value in response.cookies.items():
        if key.startswith('download_warning'):
            return value
    return None

def save_response_content(response, destination):
    CHUNK_SIZE = 32768
    with open(destination, "wb") as f:
        for chunk in response.iter_content(CHUNK_SIZE):
            if chunk: 
                f.write(chunk)

def main():
    # Verifica se a pasta do modelo já existe e não está vazia
    if os.path.exists(TARGET_DIR) and os.listdir(TARGET_DIR):
        print(f"A pasta de modelos ('{TARGET_DIR}') já existe e está pronta. Download ignorado.")
        return

    try:
        download_file_from_google_drive(GOOGLE_DRIVE_FILE_ID, OUTPUT_ZIP)
        
        print("Extraindo arquivos do modelo...")
        with zipfile.ZipFile(OUTPUT_ZIP, 'r') as zip_ref:
            # Verifica a estrutura do zip para extrair corretamente
            top_level_items = set(item.split('/')[0] for item in zip_ref.namelist())
            if 'model' in top_level_items:
                zip_ref.extractall(BASE_DIR)
            else:
                os.makedirs(TARGET_DIR, exist_ok=True)
                zip_ref.extractall(TARGET_DIR)
            
        print("Limpando arquivos temporários...")
        os.remove(OUTPUT_ZIP)
        print("✅ Modelo de voz da Mavis configurado com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro ao configurar o modelo: {e}")

if __name__ == "__main__":
    main()