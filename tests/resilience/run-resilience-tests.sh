#!/bin/bash

# Configurações
export BASE_URL="http://localhost:8000"
RESULTS_DIR="./results/resilience"
DATE=$(date +%Y%m%d_%H%M%S)

# Cria diretório para resultados se não existir
mkdir -p "$RESULTS_DIR"

echo "Iniciando testes de resiliência..."

# Executa testes de resiliência
k6 run \
  --out json="$RESULTS_DIR/metrics_$DATE.json" \
  --summary-export="$RESULTS_DIR/summary_$DATE.json" \
  resilience-test.js

# Verifica se os testes passaram
if [ $? -eq 0 ]; then
  echo "✅ Testes de resiliência concluídos com sucesso"
else
  echo "❌ Falha nos testes de resiliência"
  exit 1
fi

# Analisa resultados
echo "📊 Analisando resultados..."
echo "Resultados salvos em: $RESULTS_DIR"

# Extrai métricas importantes
jq -r '.metrics.errors.rate, .metrics.recovery.rate' "$RESULTS_DIR/summary_$DATE.json" > "$RESULTS_DIR/analysis_$DATE.txt"

echo "Análise completa. Verifique $RESULTS_DIR/analysis_$DATE.txt para mais detalhes." 