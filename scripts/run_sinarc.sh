#!/bin/bash

# Script para iniciar a aplicação SINARC (substituindo o .bat)
# Este script assume que as dependências Python foram instaladas
# e que o banco de dados está configurado.

echo "Iniciando a aplicação SINARC..."

# Adapte o comando de acordo com como a aplicação é iniciada
# Exemplo: se for um script Python principal, use:
# python3 sinarc/sinarc.py

# Se houver um servidor Flask, como sugerido pelo rede.ini (porta_flask=5000), pode ser algo como:
# FLASK_APP=sinarc.py flask run --host=0.0.0.0 --port=5000

# Para este exemplo, vamos simular a execução do script principal sinarc.py
# Você precisará ajustar conforme a estrutura real do projeto.
echo "Executando script principal sinarc.py..."
python3 sinarc/sinarc.py

if [ $? -ne 0 ]; then
    echo "Erro ao iniciar a aplicação SINARC."
    exit 1
fi

echo "Aplicação SINARC iniciada."

exit 0
