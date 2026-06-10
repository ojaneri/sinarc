import requests
from bs4 import BeautifulSoup
import os
import zipfile
from pathlib import Path

# URL base (identificada como potencialmente dinâmica, mas usaremos a raiz para busca)
BASE_URL = 'https://arquivos.receitafederal.gov.br/dados/cnpj/'
OUTPUT_DIR = Path('sinarc/dados-publicos')
ZIP_DIR = Path('sinarc/dados-publicos-zip')

def get_latest_folder():
    """Busca a pasta mais recente de dados abertos na Receita Federal."""
    print(f"Buscando a pasta mais recente em {BASE_URL}...")
    response = requests.get(BASE_URL)
    soup = BeautifulSoup(response.text, 'html.parser')
    # Procura links que apontam para pastas (ex: 'dados_abertos_cnpj/')
    links = [a['href'] for a in soup.find_all('a', href=True) if 'dados_abertos_cnpj' in a['href']]
    
    # Navega para a subpasta
    sub_url = BASE_URL + links[0]
    response = requests.get(sub_url)
    soup = BeautifulSoup(response.text, 'html.parser')
    folders = [a['href'] for a in soup.find_all('a', href=True) if a['href'].endswith('/') and a['href'] != '../']
    
    # Assume que o último da lista é o mais recente
    latest_folder = sub_url + folders[-1]
    print(f"Pasta encontrada: {latest_folder}")
    return latest_folder

def download_and_extract(url):
    ZIP_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    zip_links = [a['href'] for a in soup.find_all('a', href=True) if a['href'].endswith('.zip')]
    
    for link in zip_links:
        zip_url = url + link
        zip_path = ZIP_DIR / link
        
        print(f"Baixando {link}...")
        with requests.get(zip_url, stream=True) as r:
            with open(zip_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        
        print(f"Extraindo {link}...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(OUTPUT_DIR)
            
    print("Download e extração concluídos.")

if __name__ == "__main__":
    latest_folder_url = get_latest_folder()
    download_and_extract(latest_folder_url)
