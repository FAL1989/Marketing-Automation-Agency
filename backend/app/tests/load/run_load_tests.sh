#!/bin/bash

# Script para executar testes de carga

# Cores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${YELLOW}Iniciando testes de carga...${NC}"

# Verifica se o Locust está instalado
if ! command -v locust &> /dev/null; then
    echo -e "${RED}Locust não encontrado. Instalando...${NC}"
    pip install locust
fi

# Cria diretório para relatórios se não existir
REPORT_DIR="reports"
if [ ! -d "$REPORT_DIR" ]; then
    mkdir -p "$REPORT_DIR"
fi

# Define timestamp para os relatórios
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Executa testes em modo headless
echo -e "${GREEN}Executando testes...${NC}"
locust \
    -f locustfile.py \
    --config=locust.conf \
    --headless \
    --html="$REPORT_DIR/report_${TIMESTAMP}.html" \
    --csv="$REPORT_DIR/results_${TIMESTAMP}" \
    --logfile="$REPORT_DIR/log_${TIMESTAMP}.txt" \
    --run-time=10m \
    --users=100 \
    --spawn-rate=10

# Verifica se os testes foram bem-sucedidos
if [ $? -eq 0 ]; then
    echo -e "${GREEN}Testes concluídos com sucesso!${NC}"
    echo -e "Relatórios gerados em:"
    echo -e "- HTML: $REPORT_DIR/report_${TIMESTAMP}.html"
    echo -e "- CSV: $REPORT_DIR/results_${TIMESTAMP}_stats.csv"
    echo -e "- Log: $REPORT_DIR/log_${TIMESTAMP}.txt"
else
    echo -e "${RED}Erro durante a execução dos testes${NC}"
    exit 1
fi

# Analisa resultados
echo -e "\n${YELLOW}Analisando resultados...${NC}"
python3 -c "
import pandas as pd
import sys

try:
    df = pd.read_csv('$REPORT_DIR/results_${TIMESTAMP}_stats.csv')
    total_reqs = df['Request Count'].sum()
    total_fails = df['Failure Count'].sum()
    avg_response = df['Average Response Time'].mean()
    
    print(f'\nResumo dos Testes:')
    print(f'Total de Requisições: {total_reqs}')
    print(f'Total de Falhas: {total_fails}')
    print(f'Taxa de Erro: {(total_fails/total_reqs)*100:.2f}%')
    print(f'Tempo Médio de Resposta: {avg_response:.2f}ms')
    
    # Verifica thresholds
    if avg_response > 200:
        print('\n${RED}ALERTA: Tempo médio de resposta acima do threshold de 200ms${NC}')
    if (total_fails/total_reqs)*100 > 1:
        print('\n${RED}ALERTA: Taxa de erro acima do threshold de 1%${NC}')
except Exception as e:
    print(f'Erro ao analisar resultados: {e}')
    sys.exit(1)
" 