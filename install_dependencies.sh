#!/bin/bash

# Criar e ativar ambiente virtual
python -m venv venv
source venv/bin/activate

# Instalar dependências do shared
cd shared
pip install -r requirements.txt
cd ..

# Instalar dependências do ai-orchestrator
cd services/ai-orchestrator
pip install -r requirements.txt
cd ../..

# Instalar dependências do analytics-service
cd services/analytics
pip install -r requirements.txt
cd ../..

echo "Todas as dependências foram instaladas com sucesso!" 