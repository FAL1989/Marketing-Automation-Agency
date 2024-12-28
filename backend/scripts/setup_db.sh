#!/bin/bash

# Carrega variáveis de ambiente
source ../.env

echo "Iniciando setup do banco de dados..."

# Inicializa o banco de dados
echo "Inicializando banco de dados..."
python -m app.database.connection

# Cria usuário de teste
echo "Criando usuário de teste..."
python -m app.scripts.create_test_user

echo "Setup do banco de dados concluído!" 