#!/bin/bash

echo "Iniciando testes de carga..."

# Diretório dos testes
TEST_DIR="python"
RESULTS_DIR="results"

# Cria diretório de resultados se não existir
mkdir -p $RESULTS_DIR

# Executa os testes de endpoints
echo "Executando testes de endpoints..."
pytest $TEST_DIR/test_api_endpoints_load.py -v

# Executa os testes de MFA
echo "Executando testes de MFA..."
pytest $TEST_DIR/test_mfa_load.py -v

# Executa os testes de rate limiting
echo "Executando testes de rate limiting..."
pytest $TEST_DIR/test_rate_limit_load.py -v

echo "Testes de carga concluídos!" 