import os
import pandas as pd
from sqlalchemy import create_engine, text
import sys

# --- Configuração do Banco de Dados a partir de Variáveis de Ambiente ---
DB_USER = os.environ.get("MYSQL_USER")
DB_PASSWORD = os.environ.get("MYSQL_PASSWORD")
DB_HOST = os.environ.get("MYSQL_HOST", "localhost")
DB_PORT = os.environ.get("MYSQL_PORT", "3306")
DB_NAME = os.environ.get("MYSQL_DB_NAME", "sinarc_db")

if not all([DB_USER, DB_PASSWORD, DB_NAME]):
    print("Erro: Variáveis de ambiente MYSQL_USER, MYSQL_PASSWORD e MYSQL_DB_NAME devem ser definidas.")
    sys.exit(1)

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

try:
    engine = create_engine(DATABASE_URL)
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    print(f"Conexão com o banco de dados MySQL estabelecida com sucesso em {DB_HOST}:{DB_PORT}/{DB_NAME}.")
except Exception as e:
    print(f"Erro ao conectar ao banco de dados MySQL: {e}")
    sys.exit(1)
# --- Fim da Configuração do Banco de Dados ---

# Removemos a importação de sqlite3 e as conexões diretas com arquivos .db SQLite.
# Usaremos a engine SQLAlchemy configurada para se conectar ao MySQL.

def get_data_file_path(filename):
    # Adaptação para encontrar caminhos de arquivos de dados.
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_path = os.path.abspath(os.path.join(script_dir, '../../')) # Volta para a raiz do projeto clonado
    data_path = os.path.join(base_path, 'data', filename) # Tenta em ./sinarc/data/
    if not os.path.exists(data_path):
        data_path = os.path.join(base_path, filename) # Tenta na raiz do projeto ./sinarc/
    return data_path

def carregar_tabela_com_pandas(nome_tabela, sql_create_table, arquivo_csv, indices=None, connection=None):
    """
    Carrega dados de um arquivo CSV para uma tabela MySQL usando Pandas e SQLAlchemy.
    Cria a tabela se ela não existir e adiciona índices.
    """
    print(f"Processando tabela: {nome_tabela}")
    try:
        full_csv_path = get_data_file_path(arquivo_csv)
        if not os.path.exists(full_csv_path):
            print(f"AVISO: Arquivo CSV '{full_csv_path}' não encontrado. Pulando carregamento para '{nome_tabela}'.")
            return

        # Cria a tabela se não existir
        check_table_query = text(f"SHOW TABLES LIKE '{nome_tabela}'")
        if not connection.execute(check_table_query).fetchone():
            print(f"Criando tabela '{nome_tabela}'...")
            create_table_sql = text(sql_create_table)
            connection.execute(create_table_sql)
            print(f"Tabela '{nome_tabela}' criada.")
        else:
            print(f"Tabela '{nome_tabela}' já existe. Pulando criação.")

        # Carrega os dados do CSV
        df = pd.read_csv(full_csv_path)
        # print(f"Carregadas {len(df)} linhas do arquivo {arquivo_csv}") # Debugging opcional

        # Insere os dados no banco de dados MySQL
        df.to_sql(nome_tabela, con=connection, if_exists='append', index=False)
        print(f"{len(df)} linhas inseridas na tabela '{nome_tabela}'.")

        # Criação de Índices
        if indices:
            print(f"Criando índices para a tabela '{nome_tabela}'...")
            for idx_info in indices:
                coluna = idx_info['coluna']
                nome_indice = idx_info.get('nome', f'ix_{nome_tabela}_{coluna}')
                try:
                    create_index_sql = text(f'CREATE INDEX "{nome_indice}" ON "{nome_tabela}" ("{coluna}")')
                    connection.execute(create_index_sql)
                    print(f"Índice '{nome_indice}' criado na coluna '{coluna}'.")
                except Exception as idx_e:
                    if "Duplicate key name" in str(idx_e):
                        print(f"Índice '{nome_indice}' na coluna '{coluna}' já existe para a tabela '{nome_tabela}'.")
                    else:
                        print(f"Erro ao criar índice '{nome_indice}' para a tabela '{nome_tabela}': {idx_e}")
    except Exception as e:
        print(f"Erro geral ao processar a tabela '{nome_tabela}': {e}")


def main():
    print("Iniciando adaptação do script rede_cria_tabela_rede.db.py...")
    # Este script lidava com várias bases SQLite e operações complexas (ATTACH/DETACH DATABASE, in-memory DBs).
    # A adaptação para MySQL envolve simplificar e focar na criação e carregamento das tabelas principais.

    with engine.connect() as connection:
        # --- Adaptação das tabelas baseadas nas queries originais ---
        # O script original tinha muitas tabelas criadas com 'create table ... AS SELECT ...'
        # e manipulações de arquivos .db. Vamos adaptar para as tabelas principais.

        # Exemplo: Tabela 'ligacao1'
        nome_tabela_ligacao1 = "ligacao1"
        sql_create_table_ligacao1 = """
        CREATE TABLE IF NOT EXISTS ligacao1 (
            id1 VARCHAR(255),
            id2 VARCHAR(255),
            tipo_ligacao VARCHAR(50)
        )
        """
        # Assumindo que os dados vêm de um CSV, nome do arquivo precisa ser verificado.
        dados_fonte_ligacao1 = "ligacao1.csv" # **VERIFICAR NOME CORRETO DO ARQUIVO**
        indices_ligacao1 = [{'coluna': 'id1'}, {'coluna': 'id2'}]
        carregar_tabela_com_pandas(nome_tabela_ligacao1, sql_create_table_ligacao1, dados_fonte_ligacao1, indices_ligacao1, connection)

        # Exemplo: Tabela 'tfilial'
        nome_tabela_tfilial = "tfilial"
        sql_create_table_tfilial = """
        CREATE TABLE IF NOT EXISTS tfilial (
            cnpj_basico VARCHAR(14),
            cnpj_ordem VARCHAR(4),
            cnpj_dv VARCHAR(2),
            nome_fantasia VARCHAR(255),
            uf VARCHAR(2)
        )
        """
        dados_fonte_tfilial = "tfilial.csv" # **VERIFICAR NOME CORRETO DO ARQUIVO**
        indices_tfilial = [{'coluna': 'cnpj_basico'}]
        carregar_tabela_com_pandas(nome_tabela_tfilial, sql_create_table_tfilial, dados_fonte_tfilial, indices_tfilial, connection)

        # Exemplo: Tabela 'ligacao'
        nome_tabela_ligacao = "ligacao"
        sql_create_table_ligacao = """
        CREATE TABLE IF NOT EXISTS ligacao (
            id1 VARCHAR(255),
            id2 VARCHAR(255),
            tipo_ligacao VARCHAR(50)
        )
        """
        dados_fonte_ligacao = "ligacao.csv" # **VERIFICAR NOME CORRETO DO ARQUIVO**
        indices_ligacao = [{'coluna': 'id1'}, {'coluna': 'id2'}]
        carregar_tabela_com_pandas(nome_tabela_ligacao, sql_create_table_ligacao, dados_fonte_ligacao, indices_ligacao, connection)

        # Removidas referências diretas a SQLite (engine.execute, sqlite3.connect, ATTACH/DETACH DATABASE)
        # As operações de criação de tabelas e inserção de dados são agora centralizadas
        # na função carregar_tabela_com_pandas, que usa SQLAlchemy para se conectar ao MySQL.

        print("Adaptação de rede_cria_tabela_rede.db.py concluída.")

if __name__ == "__main__":
    main()
    sys.exit(0)
