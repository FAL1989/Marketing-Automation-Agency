#!/bin/bash

# Configurações
export API_TOKEN="test_token"  # Token para autenticação
RESULTS_DIR="results"          # Diretório para resultados
DATE=$(date +%Y%m%d_%H%M%S)   # Timestamp para os arquivos

# Criar diretório de resultados se não existir
mkdir -p $RESULTS_DIR

# Função para executar um cenário de teste
run_scenario() {
    local scenario=$1
    local output_file="$RESULTS_DIR/${DATE}_${scenario}"
    
    echo "Executando cenário: $scenario"
    echo "Resultados serão salvos em: $output_file"
    
    # Executar k6 com output JSON
    k6 run \
        --out json=$output_file.json \
        --tag testid=$DATE \
        --tag scenario=$scenario \
        -e SCENARIO=$scenario \
        load-test.js
    
    # Aguardar um pouco entre os testes
    sleep 30
}

# Executar cenários
echo "Iniciando testes de carga..."

# Teste de carga constante
run_scenario "constant_load"

# Teste de rampa
run_scenario "ramp_up"

# Teste de stress
run_scenario "stress_test"

echo "Testes concluídos. Resultados salvos em: $RESULTS_DIR"

# Gerar relatório consolidado
echo "Gerando relatório consolidado..."
cat > "$RESULTS_DIR/${DATE}_report.md" << EOF
# Relatório de Testes de Carga - $DATE

## Cenários Executados
- Carga Constante (50 VUs por 5 minutos)
- Rampa (0-50 VUs em 9 minutos)
- Stress (0-100 VUs em 4 minutos)

## Resultados

### Métricas Principais
\`\`\`
$(cat $RESULTS_DIR/${DATE}_*.json | jq -r '.metrics.http_req_duration.values.avg')
\`\`\`

### Cache Performance
\`\`\`
$(cat $RESULTS_DIR/${DATE}_*.json | jq -r '.metrics.cache_hits.values.rate')
\`\`\`

### Falhas
\`\`\`
$(cat $RESULTS_DIR/${DATE}_*.json | jq -r '.metrics.failed_requests.values.rate')
\`\`\`

## Gráficos
Os gráficos detalhados estão disponíveis no Grafana.

## Recomendações
- Analisar pontos de latência alta
- Verificar eficiência do cache
- Ajustar rate limits se necessário
EOF

echo "Relatório gerado: $RESULTS_DIR/${DATE}_report.md" 