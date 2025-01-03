#!/bin/bash

# Diretório base dos testes
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESULTS_DIR="$BASE_DIR/results"
PYTHON_TESTS_DIR="$BASE_DIR/python"

# Cria diretório de resultados se não existir
mkdir -p "$RESULTS_DIR"

# Configura ambiente Python
echo "Configurando ambiente Python..."
source ../../venv/bin/activate

# Instala dependências se necessário
if [ ! -f "../../requirements.txt" ]; then
    echo "Arquivo requirements.txt não encontrado!"
    exit 1
fi

pip install -r ../../requirements.txt

# Executa testes de carga
echo "Iniciando testes de carga..."

# Executa testes Python
echo "Executando testes Python..."
python -m pytest "$PYTHON_TESTS_DIR/test_api_endpoints_load.py" -v

# Verifica status dos testes
if [ $? -eq 0 ]; then
    echo "Testes de carga concluídos com sucesso!"
else
    echo "Falha nos testes de carga!"
    exit 1
fi

# Processa e exibe resultados
echo "Processando resultados..."
LATEST_RESULTS=$(ls -t "$RESULTS_DIR"/*.json | head -n 1)

if [ -n "$LATEST_RESULTS" ]; then
    echo "Últimos resultados:"
    cat "$LATEST_RESULTS"
else
    echo "Nenhum resultado encontrado!"
fi

# Desativa ambiente virtual
deactivate

echo "Script concluído!" 