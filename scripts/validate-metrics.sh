#!/bin/bash

set -e

echo "=== Validação de Métricas em Produção ==="
timestamp=$(date '+%Y-%m-%d %H:%M:%S')
validation_file="monitoring/metrics-validation-${timestamp}.log"

mkdir -p monitoring

# Função para consultar o Prometheus
query_prometheus() {
    local query=$1
    local result=$(curl -s -G --data-urlencode "query=$query" http://prometheus:9090/api/v1/query | jq -r '.data.result[0].value[1]')
    echo $result
}

# Função para validar métrica
validate_metric() {
    local name=$1
    local value=$2
    local threshold=$3
    local operator=$4
    local status="✅ PASSOU"
    
    echo -n "Validando $name (valor: $value, threshold: $threshold): "
    
    if [ "$operator" = "<" ]; then
        if ! (( $(echo "$value < $threshold" | bc -l) )); then
            status="❌ FALHOU"
        fi
    elif [ "$operator" = ">" ]; then
        if ! (( $(echo "$value > $threshold" | bc -l) )); then
            status="❌ FALHOU"
        fi
    fi
    
    echo "$status" | tee -a $validation_file
}

echo "Iniciando validação de métricas..." | tee -a $validation_file
echo "Timestamp: $timestamp" | tee -a $validation_file
echo "----------------------------------------" | tee -a $validation_file

# 1. Taxa de Erro
echo -e "\n1. Taxa de Erro" | tee -a $validation_file
error_rate=$(query_prometheus 'rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) * 100')
validate_metric "Taxa de erro" $error_rate 0.1 "<"

# 2. Disponibilidade
echo -e "\n2. Disponibilidade" | tee -a $validation_file
availability=$(query_prometheus '(1 - (rate(http_requests_total{status=~"5.."}[24h]) / rate(http_requests_total[24h]))) * 100')
validate_metric "Disponibilidade" $availability 99.9 ">"

# 3. Tempo de Resposta
echo -e "\n3. Tempo de Resposta" | tee -a $validation_file
response_time=$(query_prometheus 'rate(http_request_duration_seconds_sum[5m]) / rate(http_request_duration_seconds_count[5m])')
validate_metric "Tempo de resposta médio" $response_time 0.8 "<"

# 4. Percentil 95
echo -e "\n4. Percentil 95 de Latência" | tee -a $validation_file
p95_latency=$(query_prometheus 'histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))')
validate_metric "Latência P95" $p95_latency 3 "<"

# 5. Cobertura de Monitoramento
echo -e "\n5. Cobertura de Monitoramento" | tee -a $validation_file
monitored_services=$(query_prometheus 'count(up)')
total_services=$(query_prometheus 'count(container_last_seen)')
coverage=$(echo "scale=2; $monitored_services / $total_services * 100" | bc)
validate_metric "Cobertura de monitoramento" $coverage 95 ">"

# 6. Tempo de Detecção de Incidentes
echo -e "\n6. Tempo de Detecção de Incidentes" | tee -a $validation_file
detection_time=$(query_prometheus 'avg_over_time(prometheus_rule_evaluation_duration_seconds[1h]) * 1000')
validate_metric "Tempo de detecção" $detection_time 300 "<"

# 7. Validação de Alertas
echo -e "\n7. Validação de Alertas" | tee -a $validation_file
echo "Verificando configuração de alertas..." | tee -a $validation_file

alerts_config=$(curl -s http://prometheus:9090/api/v1/rules | jq -r '.data.groups[].rules[] | select(.type=="alerting")')
total_alerts=$(echo "$alerts_config" | jq -r '. | length')
echo "Total de alertas configurados: $total_alerts" | tee -a $validation_file

# 8. Validação de Métricas Customizadas
echo -e "\n8. Métricas Customizadas" | tee -a $validation_file
custom_metrics=$(curl -s http://app:8000/metrics | grep -c "^app_")
echo "Métricas customizadas encontradas: $custom_metrics" | tee -a $validation_file

# 9. Validação de Integrações
echo -e "\n9. Integrações" | tee -a $validation_file
echo "Verificando integrações..." | tee -a $validation_file

# Verificar Grafana
if curl -s http://grafana:3000/api/health | grep -q "ok"; then
    echo "✅ Grafana: Conectado" | tee -a $validation_file
else
    echo "❌ Grafana: Falha na conexão" | tee -a $validation_file
fi

# Verificar AlertManager
if curl -s http://alertmanager:9093/-/healthy | grep -q "ok"; then
    echo "✅ AlertManager: Conectado" | tee -a $validation_file
else
    echo "❌ AlertManager: Falha na conexão" | tee -a $validation_file
fi

# 10. Resumo
echo -e "\n10. Resumo da Validação" | tee -a $validation_file
echo "----------------------------------------" | tee -a $validation_file
total_checks=$(grep -c "PASSOU\|FALHOU" $validation_file)
passed_checks=$(grep -c "PASSOU" $validation_file)
failed_checks=$(grep -c "FALHOU" $validation_file)

echo "Total de verificações: $total_checks" | tee -a $validation_file
echo "Verificações bem-sucedidas: $passed_checks" | tee -a $validation_file
echo "Verificações falhas: $failed_checks" | tee -a $validation_file
echo "Taxa de sucesso: $(echo "scale=2; $passed_checks * 100 / $total_checks" | bc)%" | tee -a $validation_file

# Enviar métricas para o Pushgateway
echo -e "\nEnviando resultados para o Pushgateway..."
curl -X POST -H "Content-Type: text/plain" --data-binary "
# TYPE metrics_validation_status gauge
metrics_validation_total_checks $total_checks
metrics_validation_passed_checks $passed_checks
metrics_validation_failed_checks $failed_checks
metrics_validation_error_rate $error_rate
metrics_validation_availability $availability
metrics_validation_response_time $response_time
metrics_validation_p95_latency $p95_latency
metrics_validation_monitoring_coverage $coverage
metrics_validation_detection_time $detection_time
" http://pushgateway:9091/metrics/job/metrics_validation

echo -e "\nRelatório completo salvo em: $validation_file" 