import requests
from bs4 import BeautifulSoup
import os

# Base URL da Receita Federal
BASE_URL = 'https://arquivos.receitafederal.gov.br/dados/cnpj/dados_abertos_cnpj/2024-10/'
OUTPUT_DIR = 'dados-publicos-zip'

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

def download_files():
    print(f"Acessando {BASE_URL}...")
    response = requests.get(BASE_URL)
    if response.status_code != 200:
        print("Erro ao acessar a página da Receita Federal.")
        return

    soup = BeautifulSoup(response.text, 'html.parser')
    links = [a['href'] for a in soup.find_all('a', href=True) if a['href'].endswith('.zip')]

    for link in links:
        file_url = BASE_URL + link
        file_path = os.path.join(OUTPUT_DIR, link)
        if not os.path.exists(file_path):
            print(f"Baixando: {link}...")
            # Usando requests para download para melhor controle
            with requests.get(file_url, stream=True) as r:
                r.raise_for_status()
                with open(file_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            print(f"Download concluído: {link}")
        else:
            print(f"Já existe: {link}")

if __name__ == "__main__":
    download_files()
