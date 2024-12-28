#!/bin/bash

# Configurações
BASE_URL=${1:-"http://localhost:3001"}
TEST_DIR="test-results/$(date +%Y%m%d_%H%M%S)"

# Criar diretório para resultados
mkdir -p "$TEST_DIR"

echo "Iniciando suite completa de testes..."
echo "URL Base: $BASE_URL"
echo "Resultados serão salvos em: $TEST_DIR"

# Função para executar e registrar resultados
run_test() {
  local test_name=$1
  local command=$2
  local start_time=$(date +%s)
  
  echo -e "\n=== Executando $test_name ==="
  echo "Iniciado em: $(date)"
  
  if eval "$command"; then
    local status="✅ Passou"
  else
    local status="❌ Falhou"
  fi
  
  local end_time=$(date +%s)
  local duration=$((end_time - start_time))
  
  echo "$test_name: $status (${duration}s)" >> "$TEST_DIR/summary.txt"
  echo "Concluído em: $(date)"
  echo "Duração: ${duration}s"
  echo "Status: $status"
}

# 1. Testes Unitários
run_test "Testes Unitários" "npm test -- --coverage --json --outputFile=$TEST_DIR/unit-test-results.json"

# 2. Testes de Integração
run_test "Testes de Integração" "npm run test:integration"

# 3. Testes E2E
run_test "Testes E2E" "npm run test:e2e"

# 4. Testes de Carga
run_test "Testes de Carga" "./scripts/run-load-tests.sh $BASE_URL"

# 5. Testes de Segurança
run_test "Testes de Segurança" "node tests/security/security-checks.js"

# 6. Lint e Type Check
run_test "ESLint" "npm run lint"
run_test "TypeScript" "npm run type-check"

# Gerar relatório final
echo -e "\n=== Relatório Final ===" | tee -a "$TEST_DIR/summary.txt"
echo "Data: $(date)" | tee -a "$TEST_DIR/summary.txt"
echo "URL Base: $BASE_URL" | tee -a "$TEST_DIR/summary.txt"
echo -e "\nResultados:" | tee -a "$TEST_DIR/summary.txt"
cat "$TEST_DIR/summary.txt"

# Verificar se algum teste falhou
if grep -q "❌" "$TEST_DIR/summary.txt"; then
  echo -e "\n❌ Alguns testes falharam!"
  exit 1
else
  echo -e "\n✅ Todos os testes passaram!"
fi

# Copiar relatórios relevantes
cp coverage/lcov-report "$TEST_DIR/coverage" -r
cp security-report.json "$TEST_DIR/"
cp load-test-summary.json "$TEST_DIR/"

echo "Relatórios completos disponíveis em: $TEST_DIR" 