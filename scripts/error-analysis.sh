#!/bin/bash

set -e

echo "=== Análise de Erros ==="
timestamp=$(date '+%Y-%m-%d %H:%M:%S')
report_file="monitoring/error-analysis-${timestamp}.log"

mkdir -p monitoring

# Função para consultar o Prometheus
query_prometheus() {
    local query=$1
    local result=$(curl -s -G --data-urlencode "query=$query" http://prometheus:9090/api/v1/query | jq -r '.data.result[]')
    echo "$result"
}

echo "Iniciando análise de erros..." | tee -a $report_file
echo "Timestamp: $timestamp" | tee -a $report_file
echo "----------------------------------------" | tee -a $report_file

# Análise de erros HTTP
echo -e "\n1. Erros HTTP por endpoint" | tee -a $report_file
query_prometheus 'topk(10, sum(rate(http_requests_total{status=~"5.."}[5m])) by (endpoint))'

# Análise de erros por serviço
echo -e "\n2. Erros por serviço" | tee -a $report_file
query_prometheus 'topk(10, sum(rate(http_requests_total{status=~"5.."}[5m])) by (service))'

# Análise de latência
echo -e "\n3. Endpoints mais lentos" | tee -a $report_file
query_prometheus 'topk(10, histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le, endpoint)))'

# Circuit breakers
echo -e "\n4. Circuit breakers ativos" | tee -a $report_file
query_prometheus 'circuit_breaker_state{state="open"}'

# Erros de integração
echo -e "\n5. Erros de integração" | tee -a $report_file
query_prometheus 'rate(integration_errors_total[5m])'

# Análise de logs
echo -e "\n6. Análise de logs" | tee -a $report_file
echo "Últimos erros nos logs:" | tee -a $report_file
docker-compose logs --tail=50 | grep -i "error\|exception\|fail" | tee -a $report_file

# Métricas de recursos
echo -e "\n7. Uso de recursos" | tee -a $report_file
echo "CPU:" | tee -a $report_file
query_prometheus 'sum(rate(container_cpu_usage_seconds_total[5m])) by (container)'
echo "Memória:" | tee -a $report_file
query_prometheus 'sum(container_memory_usage_bytes) by (container)'

# Resumo
echo -e "\n8. Resumo" | tee -a $report_file
echo "----------------------------------------" | tee -a $report_file
total_errors=$(query_prometheus 'sum(rate(http_requests_total{status=~"5.."}[5m]))')
error_rate=$(query_prometheus 'sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m])) * 100')
avg_latency=$(query_prometheus 'avg(rate(http_request_duration_seconds_sum[5m]) / rate(http_request_duration_seconds_count[5m]))')

echo "Total de erros/s: $total_errors" | tee -a $report_file
echo "Taxa de erro: $error_rate%" | tee -a $report_file
echo "Latência média: ${avg_latency}s" | tee -a $report_file

echo -e "\nRelatório completo salvo em: $report_file" 