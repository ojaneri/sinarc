import os
import pandas as pd
from sqlalchemy import create_engine, text
import sys # Import sys to handle potential errors gracefully

# --- Configuração do Banco de Dados a partir de Variáveis de Ambiente ---
# As variáveis de ambiente devem ser definidas antes de executar este script.
# Exemplo:
# export MYSQL_USER='sinarc_user'
# export MYSQL_PASSWORD='sua_senha_segura_aqui'
# export MYSQL_HOST='localhost'
# export MYSQL_PORT='3306'
# export MYSQL_DB_NAME='sinarc_db'

DB_USER = os.environ.get("MYSQL_USER")
DB_PASSWORD = os.environ.get("MYSQL_PASSWORD")
DB_HOST = os.environ.get("MYSQL_HOST", "localhost")
DB_PORT = os.environ.get("MYSQL_PORT", "3306")
DB_NAME = os.environ.get("MYSQL_DB_NAME", "sinarc_db")

if not all([DB_USER, DB_PASSWORD, DB_NAME]):
    print("Erro: Variáveis de ambiente MYSQL_USER, MYSQL_PASSWORD e MYSQL_DB_NAME devem ser definidas.")
    print("Por favor, defina-as antes de executar este script.")
    sys.exit(1)

# Construir a URL de conexão do SQLAlchemy para MySQL
# Usando o driver mysqlclient
# Formato: mysql+mysqlclient://user:password@host:port/database
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

try:
    engine = create_engine(DATABASE_URL)
    # Testar a conexão para garantir que está tudo certo antes de prosseguir
    with engine.connect() as connection:
        connection.execute(text("SELECT 1")) # Query simples para testar a conexão
    print(f"Conexão com o banco de dados MySQL estabelecida com sucesso em {DB_HOST}:{DB_PORT}/{DB_NAME}.")
except Exception as e:
    print(f"Erro ao conectar ao banco de dados MySQL: {e}")
    print("Verifique suas credenciais, se o servidor MySQL está rodando e se o banco de dados existe.")
    sys.exit(1)
# --- Fim da Configuração do Banco de Dados ---


# A partir daqui, substituímos a lógica de SQLite pela lógica de SQLAlchemy
# Caminho para arquivos de dados e nomes de tabelas
# O conceito de 'cam' (caminho para arquivo .db) não se aplica diretamente ao MySQL,
# pois nos conectamos a um servidor. Os caminhos para os arquivos de entrada (CSV, etc.)
# ainda podem ser relevantes, mas a conexão direta com arquivos de banco de dados é removida.


def get_data_file_path(filename):
    # Adaptação para encontrar caminhos de arquivos de dados, assumindo que estão na raiz ou em uma pasta 'data' relativa ao script
    # Você pode precisar ajustar esta lógica dependendo de onde os arquivos .csv e outros dados de entrada estão localizados
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Tenta encontrar o arquivo na raiz do projeto 'sinarc' ou em uma pasta 'data' dentro dela
    base_path = os.path.abspath(os.path.join(script_dir, '../../')) # Volta para a raiz do projeto clonado
    data_path = os.path.join(base_path, 'data', filename) # Tenta em ./sinarc/data/
    if not os.path.exists(data_path):
        data_path = os.path.join(base_path, filename) # Tenta na raiz do projeto ./sinarc/
    return data_path

def carregar_e_salvar_tabela(nomeTabela, sql_create_table, dados_fonte_path, colunas_indices=None):
    """
    Carrega dados de um arquivo fonte (como CSV) para uma tabela no banco de dados MySQL,
    criando a tabela se ela não existir e adicionando índices.
    """
    print(f"Processando tabela: {nomeTabela}")
    try:
        with engine.connect() as connection:
            # 1. Criação da Tabela (se não existir)
            # Verifica se a tabela já existe para evitar erros
            check_table_query = text(f"SHOW TABLES LIKE '{nomeTabela}'")
            if not connection.execute(check_table_query).fetchone():
                print(f"Criando tabela '{nomeTabela}'...")
                create_table_sql = text(sql_create_table)
                connection.execute(create_table_sql)
                print(f"Tabela '{nomeTabela}' criada.")
            else:
                print(f"Tabela '{nomeTabela}' já existe. Pulando criação.")

            # 2. Carregamento dos Dados
            # Aqui assumimos que os dados fonte são CSVs. Adapte se forem outros formatos.
            # O caminho para os dados precisa ser corrigido.
            full_data_path = get_data_file_path(dados_fonte_path)
            if not os.path.exists(full_data_path):
                print(f"AVISO: Arquivo de dados '{full_data_path}' não encontrado. Pulando carregamento para '{nomeTabela}'.")
                return

            print(f"Carregando dados de '{full_data_path}' para '{nomeTabela}'...")
            df = pd.read_csv(full_data_path)

            # Renomear colunas para evitar conflitos com palavras reservadas ou caracteres inválidos para MySQL, se necessário
            # df.columns = [col.replace(' ', '_').lower() for col in df.columns] # Exemplo de sanitização

            # Limpeza de dados ou conversão de tipos pode ser necessária aqui
            # Ex: df['data_coluna'] = pd.to_datetime(df['data_coluna'], errors='coerce')

            # Inserir dados no MySQL
            # SQLAlchemy's to_sql é uma forma conveniente de inserir DataFrames
            # Converte tipos de dados do Pandas para tipos compatíveis com MySQL se necessário
            # Para tabelas grandes, considere usar chunking com to_sql ou métodos de inserção em massa
            try:
                df.to_sql(nomeTabela, con=connection, if_exists='append', index=False)
                print(f"{len(df)} linhas inseridas na tabela '{nomeTabela}'.")
            except Exception as e:
                print(f"Erro ao inserir dados na tabela '{nomeTabela}': {e}")
                # Tentar inserir linha por linha se to_sql falhar (mais lento, mas pode depurar melhor)
                print("Tentando inserir linha por linha como fallback...")
                for index, row in df.iterrows():
                    try:
                        # Construir a query de INSERT dinamicamente ou usar parâmetros
                        # Assegurar que os nomes das colunas em 'row.index' correspondem aos da tabela
                        cols = ', '.join(row.index)
                        placeholders = ', '.join(['%s'] * len(row))
                        insert_sql_str = f"INSERT INTO {nomeTabela} ({cols}) VALUES ({placeholders})"
                        connection.execute(text(insert_sql_str), row.values)
                    except Exception as insert_e:
                        print(f"Erro ao inserir linha {index} na tabela '{nomeTabela}': {insert_e}")


            # 3. Criação de Índices (se especificado)
            if colunas_indices:
                print(f"Criando índices para a tabela '{nomeTabela}'...")
                for idx_info in colunas_indices:
                    coluna = idx_info['coluna']
                    nome_indice = idx_info.get('nome', f'ix_{nomeTabela}_{coluna}') # Nome padrão se não fornecido
                    try:
                        # Verifica se o índice já existe antes de tentar criar
                        # Nota: Verificação de índice em MySQL pode ser mais complexa.
                        # Para simplificar, vamos assumir que a criação será executada
                        # e lidar com erro se já existir ou adaptar a query.
                        # Uma forma mais robusta seria consultar INFORMATION_SCHEMA.STATISTICS
                        create_index_sql = text(f'CREATE INDEX "{nome_indice}" ON "{nomeTabela}" ("{coluna}")')
                        connection.execute(create_index_sql)
                        print(f"Índice '{nome_indice}' criado na coluna '{coluna}'.")
                    except Exception as idx_e:
                        # MySQL retorna um erro específico se o índice já existir
                        if "Duplicate key name" in str(idx_e):
                            print(f"Índice '{nome_indice}' na coluna '{coluna}' já existe para a tabela '{nomeTabela}'.")
                        else:
                            print(f"Erro ao criar índice '{nome_indice}' para a tabela '{nomeTabela}': {idx_e}")

            print(f"Processamento da tabela '{nomeTabela}' concluído.")

    except Exception as e:
        print(f"Ocorreu um erro geral ao processar a tabela '{nomeTabela}': {e}")


def processar_arquivos_cnpj():
    """
    Processa e salva as tabelas do CNPJ no banco de dados MySQL.
    Esta função substitui a lógica que antes escrevia diretamente em arquivos .db SQLite.
    """
    # Assumindo que os dados para CNPJ estão em arquivos CSV localizados na pasta 'data' ou raiz do projeto.
    # Os caminhos para os arquivos de entrada precisam ser corrigidos para serem acessíveis pelo script.

    # Exemplo de dados de tabelas encontradas nos scripts originais:
    # 1. Estabelecimento
    # 2. Empresa
    # 3. Socio
    # 4. Referencia (tabela auxiliar)

    # --- Dados para a tabela 'estabelecimento' ---
    # O script original usa CREATE TABLE estabelecimento AS ... SELECT ... FROM arquivo.csv
    # Vamos adaptar para ler um CSV e inserir via pandas.to_sql
    nome_tabela_estabelecimento = "estabelecimento"
    # A query CREATE TABLE original de `dados_cnpj_para_sqlite.py` é:
    # CREATE TABLE estabelecimento AS SELECT * FROM arquivo_estabelecimento.csv
    # Isso não é uma sintaxe SQL válida para criar tabelas. Precisamos definir as colunas.
    # Inferindo colunas do script original e do nome do arquivo
    # A estrutura exata das colunas precisa ser validada.
    # Para demonstração, usaremos uma estrutura hipotética baseada no uso comum de CNPJ.
    # Você precisará verificar os arquivos de entrada (.csv) para a estrutura correta.
    sql_create_table_estabelecimento = """
    CREATE TABLE IF NOT EXISTS estabelecimento (
        cnpj_basico VARCHAR(14) PRIMARY KEY,
        cnpj_ordem VARCHAR(4),
        cnpj_dv VARCHAR(2),
        identificador_matriz_filial INT,
        nome_fantasia VARCHAR(255),
        data_constituicao DATE,
        cnpj_complementar VARCHAR(14),
        uf VARCHAR(2),
        inscricao_estadual VARCHAR(50),
        inscricao_municipal VARCHAR(50),
        situacao_cadastral INT,
        data_situacao_cadastral DATE,
        motivo_situacao_cadastral INT,
        cep VARCHAR(8),
        pais VARCHAR(10),
        ddd VARCHAR(3),
        telefone VARCHAR(15),
        telefone_2 VARCHAR(15),
        fax VARCHAR(15),
        email VARCHAR(255),
        situacao_especial VARCHAR(50),
        data_situacao_especial DATE
    )
    """
    # O arquivo fonte CSV para estabelecimento não está claro no script original (menciona 'arquivo_estabelecimento.csv')
    # Usando um nome de arquivo genérico. Você DEVE verificar e corrigir o nome do arquivo real.
    # Baseado em "dados_cnpj_para_sqlite.py", ele parece processar um arquivo chamado 'estabelecimento.csv' ou similar
    # Vamos supor que o arquivo seja 'estabelecimento.csv' na pasta de dados.
    dados_fonte_estabelecimento = "estabelecimento.csv" # **VERIFICAR NOME CORRETO DO ARQUIVO**

    # Tentativa de criar um índice no código original
    indices_estabelecimento = [{'coluna': 'cnpj_basico'}] # Assumindo que cnpj_basico é o principal campo de busca

    carregar_e_salvar_tabela(nome_tabela_estabelecimento, sql_create_table_estabelecimento, dados_fonte_estabelecimento, indices_estabelecimento)

    # --- Dados para a tabela 'empresa' ---
    nome_tabela_empresa = "empresa"
    # O script original menciona CREATE TABLE empresas AS ...
    sql_create_table_empresa = """
    CREATE TABLE IF NOT EXISTS empresa (
        cnpj_basico VARCHAR(14) PRIMARY KEY,
        razao_social VARCHAR(255),
        nome_fantasia VARCHAR(255),
        natureza_juridica INT
    )
    """
    dados_fonte_empresa = "empresa.csv" # **VERIFICAR NOME CORRETO DO ARQUIVO**
    indices_empresa = [{'coluna': 'cnpj_basico'}]
    carregar_e_salvar_tabela(nome_tabela_empresa, sql_create_table_empresa, dados_fonte_empresa, indices_empresa)

    # --- Dados para a tabela 'socios' ---
    nome_tabela_socios = "socios"
    # O script original menciona CREATE TABLE socios AS ...
    sql_create_table_socios = """
    CREATE TABLE IF NOT EXISTS socios (
        cnpj_basico VARCHAR(14),
        qualificacao_socio INT,
        tipo_pessoa INT,
        nome_razao_social VARCHAR(255),
        cnpj_cpf_doc_identificador VARCHAR(14),
        data_entrada DATE,
        pais_origem INT,
        representante_legal VARCHAR(255),
        nome_representante_legal VARCHAR(255),
        qualificacao_representante_legal INT,
        pais_nacionalidade INT,
        cpf_representante_legal VARCHAR(11)
    )
    """
    dados_fonte_socios = "socios.csv" # **VERIFICAR NOME CORRETO DO ARQUIVO**
    indices_socios = [{'coluna': 'cnpj_basico'}, {'coluna': 'cnpj_cpf_doc_identificador'}]
    carregar_e_salvar_tabela(nome_tabela_socios, sql_create_table_socios, dados_fonte_socios, indices_socios)

    # --- Tabela de Referência ---
    # O script original usa INSERT INTO _referencia (referencia, valor)
    nome_tabela_referencia = "_referencia"
    sql_create_table_referencia = """
    CREATE TABLE IF NOT EXISTS _referencia (
        referencia VARCHAR(50) PRIMARY KEY,
        valor VARCHAR(255)
    )
    """
    # Esta tabela é populada com valores específicos no script original.
    # Precisamos recriar essa lógica de inserção.
    print(f"Populando tabela de referência: {nome_tabela_referencia}")
    try:
        with engine.connect() as connection:
            # Verifica se a tabela já existe
            check_ref_table_query = text(f"SHOW TABLES LIKE '{nome_tabela_referencia}'")
            if not connection.execute(check_ref_table_query).fetchone():
                print(f"Criando tabela '{nome_tabela_referencia}'...")
                create_ref_sql = text(sql_create_table_referencia)
                connection.execute(create_ref_sql)
                print(f"Tabela '{nome_tabela_referencia}' criada.")
            else:
                print(f"Tabela '{nome_tabela_referencia}' já existe. Limpando e recriando entradas.")
                connection.execute(text(f"DELETE FROM {nome_tabela_referencia}")) # Limpa dados antigos se a tabela existir

            # Os valores de dataReferencia e qtde_cnpjs são obtidos dinamicamente no script original
            # Aqui, faremos uma simulação ou precisaremos replicar a lógica de obtenção.

            # Simulação: obter data de referência (você precisará implementar a lógica real)
            from datetime import datetime
            dataReferencia = datetime.now().strftime('%Y-%m-%d') # Exemplo: formatar data atual
            # Para qtde_cnpjs, precisaríamos consultar a tabela 'estabelecimento' após o carregamento dela.
            # Vamos obter isso após o carregamento das tabelas principais.

            # Inserir a referência de CNPJ
            insert_ref_sql = text(f"INSERT INTO {nome_tabela_referencia} (referencia, valor) VALUES ('CNPJ', '{dataReferencia}')")
            connection.execute(insert_ref_sql)
            # Inserir a quantidade de CNPJs (após carregar a tabela 'estabelecimento')
            try:
                count_result = connection.execute(text('SELECT COUNT(*) FROM estabelecimento;')).fetchone()
                qtde_cnpjs = count_result[0] if count_result else 0
                insert_qtde_sql = text(f"INSERT INTO {nome_tabela_referencia} (referencia, valor) VALUES ('cnpj_qtde', '{qtde_cnpjs}')")
                connection.execute(insert_qtde_sql)
                print(f"Inserido valor para 'cnpj_qtde': {qtde_cnpjs}")
            except Exception as count_e:
                print(f"AVISO: Não foi possível obter a contagem de CNPJs para a tabela de referência: {count_e}")

            print(f"Tabela de referência '{nome_tabela_referencia}' populada.")

    except Exception as e:
        print(f"Erro ao processar a tabela de referência '{nome_tabela_referencia}': {e}")

if __name__ == "__main__":
    print("Iniciando processamento dos dados CNPJ...")
    # Certifique-se de que os arquivos CSV de entrada estão acessíveis
    # e que os nomes em get_data_file_path() e nos argumentos de carregar_e_salvar_tabela() estão corretos.

    processar_arquivos_cnpj()

    # Execução de comandos adicionais ou limpeza, se necessário
    # Exemplo: `VACUUM` em SQLite não tem equivalente direto em MySQL para otimização de espaço da mesma forma.
    # Outras otimizações podem ser aplicadas se necessário.

    print("Processamento dos dados CNPJ concluído.")
    sys.exit(0)
