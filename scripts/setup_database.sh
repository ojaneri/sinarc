#!/bin/bash

# Define os detalhes de conexão com o banco de dados MySQL
DB_NAME="sinarc_db"
DB_USER="root" # Ajuste se necessário
DB_PASS="your_mysql_password" # **IMPORTANTE: Substitua pela sua senha do MySQL ou configure via variáveis de ambiente/arquivo de configuração seguro**
DB_HOST="localhost"
DB_PORT="3306"

# Cria o banco de dados se não existir
echo "Criando banco de dados '$DB_NAME' se ele não existir..."
mysql -h $DB_HOST -P $DB_PORT -u $DB_USER -p$DB_PASS -e "CREATE DATABASE IF NOT EXISTS $DB_NAME CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
if [ $? -ne 0 ]; then
    echo "Erro ao criar ou acessar o banco de dados '$DB_NAME'. Verifique suas credenciais do MySQL e se o servidor está rodando."
    exit 1
fi
echo "Banco de dados '$DB_NAME' pronto."

# Criação das tabelas (adaptar os scripts Python para usar SQLAlchemy com MySQL)
# Por enquanto, vamos focar na configuração do SQLAlchemy nos scripts Python.
# Este script .sh pode ser estendido para chamar os scripts Python de criação de tabelas.

echo "Executando scripts Python para criar tabelas e importar dados..."
# Exemplo: você precisará adaptar os scripts Python para se conectarem ao MySQL
# e remover a lógica de SQLite.
# python3 sinarc/dados_cnpj_para_sqlite.py --db-type mysql --db-host $DB_HOST --db-port $DB_PORT --db-user $DB_USER --db-pass $DB_PASS --db-name $DB_NAME
# python3 sinarc/rede_cria_tabela_cnpj_links_ete.py --db-type mysql --db-host $DB_HOST --db-port $DB_PORT --db-user $DB_USER --db-pass $DB_PASS --db-name $DB_NAME
# python3 sinarc/rede_cria_tabela_rede.db.py --db-type mysql --db-host $DB_HOST --db-port $DB_PORT --db-user $DB_USER --db-pass $DB_PASS --db-name $DB_NAME

echo "Configuração inicial do banco de dados concluída. Adaptações nos scripts Python são necessárias."

exit 0
