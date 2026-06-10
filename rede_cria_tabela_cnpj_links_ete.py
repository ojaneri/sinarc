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

# As funções que antes trabalhavam com arquivos SQLite (.db) agora se conectarão ao MySQL.
# Caminhos de arquivo SQLite (como camDbSqliteBaseCompleta, camDBrede, camDBSaida) precisam ser removidos
# ou adaptados para simplesmente usar a conexão SQLAlchemy estabelecida.

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
        # Usar if_exists='append' para adicionar dados. Se for necessário limpar antes, adicionar if_exists='replace'.
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
    print("Iniciando adaptação do script rede_cria_tabela_cnpj_links_ete.py...")

    with engine.connect() as connection:
        # --- Tabelas e Dados relacionados a CNPJ ---
        # Este script parece criar tabelas ligadas a CNPJ.
        # As queries originais `create table ... AS SELECT * FROM arquivo.csv` foram removidas.
        # Precisamos definir as estruturas das tabelas explicitamente.

        # Exemplo: Tabela 'estabelecimento' (inferida das linhas comentadas e uso comum)
        nome_tabela_estabelecimento = "estabelecimento"
        sql_create_table_estabelecimento = """
        CREATE TABLE IF NOT EXISTS estabelecimento (
            cnpj_basico VARCHAR(14) PRIMARY KEY,
            cnpj_ordem VARCHAR(4),
            cnpj_dv VARCHAR(2),
            identificador_matriz_filial INT,
            nome_fantasia VARCHAR(255),
            data_constituicao DATE,
            uf VARCHAR(2),
            cep VARCHAR(8)
        )
        """
        dados_fonte_estabelecimento = "estabelecimento.csv" # **VERIFICAR NOME CORRETO DO ARQUIVO**
        indices_estabelecimento = [{'coluna': 'cnpj_basico'}]
        carregar_tabela_com_pandas(nome_tabela_estabelecimento, sql_create_table_estabelecimento, dados_fonte_estabelecimento, indices_estabelecimento, connection)

        # Exemplo: Tabela 'link_ete' (mencionada em CREATE TABLE link_ete as)
        nome_tabela_link_ete = "link_ete"
        sql_create_table_link_ete = """
        CREATE TABLE IF NOT EXISTS link_ete (
            id1 VARCHAR(255),
            id2 VARCHAR(255)
        )
        """
        # O script original pode ter lido isso de outra tabela ou arquivo. Precisamos verificar a fonte exata.
        # Assumindo um CSV de exemplo para fins de demonstração.
        dados_fonte_link_ete = "link_ete.csv" # **VERIFICAR NOME CORRETO DO ARQUIVO**
        indices_link_ete = [{'coluna': 'id1'}, {'coluna': 'id2'}]
        carregar_tabela_com_pandas(nome_tabela_link_ete, sql_create_table_link_ete, dados_fonte_link_ete, indices_link_ete, connection)

        # As linhas que envolviam `conBaseCompleta = sqlite3.connect(...)` ou `con.execute()`
        # e manipulações diretas de arquivos .db foram substituídas por chamadas a carregar_tabela_com_pandas
        # ou removidas se eram apenas para operações de SQLite que não se aplicam ao MySQL.

        # O script original também comentava sobre `ATTACH DATABASE` e `DETACH DATABASE`.
        # No MySQL, tabelas de diferentes bancos podem ser acessadas via `database_name.table_name`.
        # Se houver necessidade de juntar dados de bases diferentes no mesmo servidor MySQL,
        # basta referenciar com o nome do banco (ex: `sinarc_db.outra_tabela`).

        # As linhas que criavam índices diretamente no arquivo SQLite foram adaptadas para a função carregar_tabela_com_pandas.
        # Ex: conFinal.execute('CREATE INDEX "ix_link_ete_id1" ON "link_ete" ("id1")')

        print("Adaptação de rede_cria_tabela_cnpj_links_ete.py concluída.")

if __name__ == "__main__":
    main()
    sys.exit(0)
