#!/bin/bash

# Configurações
BASE_URL=${1:-"http://localhost:3001"}
DURATION=${2:-"23m"} # Duração total dos testes (soma dos stages no load-test.js)
OUTPUT_DIR="test-results/$(date +%Y%m%d_%H%M%S)"

# Criar diretório para resultados
mkdir -p "$OUTPUT_DIR"

echo "Iniciando testes de carga..."
echo "URL Base: $BASE_URL"
echo "Duração: $DURATION"
echo "Resultados serão salvos em: $OUTPUT_DIR"

# Executar k6 com variáveis de ambiente
k6 run \
  --out json="$OUTPUT_DIR/raw_results.json" \
  --out csv="$OUTPUT_DIR/metrics.csv" \
  --env BASE_URL="$BASE_URL" \
  tests/load/load-test.js

# Verificar se o teste foi bem-sucedido
if [ $? -eq 0 ]; then
  echo "Testes de carga concluídos com sucesso!"
  
  # Gerar relatório resumido
  echo "Gerando relatório..."
  {
    echo "# Relatório de Testes de Carga"
    echo "Data: $(date)"
    echo "URL Base: $BASE_URL"
    echo "Duração: $DURATION"
    echo
    echo "## Métricas Principais"
    echo "$(grep 'http_req_duration' "$OUTPUT_DIR/metrics.csv" | tail -n 1)"
    echo
    echo "## Taxa de Erro"
    echo "$(grep 'errors' "$OUTPUT_DIR/metrics.csv" | tail -n 1)"
    echo
    echo "## Detalhes Completos"
    echo "Consulte os arquivos em: $OUTPUT_DIR"
  } > "$OUTPUT_DIR/report.md"

  echo "Relatório gerado em: $OUTPUT_DIR/report.md"
else
  echo "Erro durante a execução dos testes!"
  exit 1
fi

# Verificar thresholds
echo "Verificando thresholds..."
if grep -q "\"thresholds\":.*\"fail\"" "$OUTPUT_DIR/raw_results.json"; then
  echo "ALERTA: Alguns thresholds não foram atingidos!"
  echo "Verifique os detalhes em: $OUTPUT_DIR/raw_results.json"
  exit 1
else
  echo "Todos os thresholds foram atingidos com sucesso!"
fi 