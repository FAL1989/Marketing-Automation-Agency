#!/bin/bash

set -e

echo "=== Sistema de Monitoramento Contínuo ==="
timestamp=$(date '+%Y-%m-%d %H:%M:%S')
report_file="monitoring/health-report-${timestamp}.log"

mkdir -p monitoring

# Função para consultar o Prometheus
query_prometheus() {
    local query=$1
    local result=$(curl -s -G --data-urlencode "query=$query" http://prometheus:9090/api/v1/query | jq -r '.data.result[0].value[1]')
    echo $result
}

# Verificar disponibilidade dos serviços
echo "Verificando disponibilidade dos serviços..." | tee -a $report_file
services=("app" "prometheus" "grafana" "alertmanager" "pushgateway" "node-exporter" "cadvisor")
for service in "${services[@]}"; do
    if curl -s "http://${service}:8000/health" > /dev/null; then
        echo "✅ $service: Operacional" | tee -a $report_file
    else
        echo "❌ $service: Não respondendo" | tee -a $report_file
    fi
done

# Verificar métricas de performance
echo -e "\nVerificando métricas de performance..." | tee -a $report_file

# Taxa de erro
error_rate=$(query_prometheus 'rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) * 100')
echo "Taxa de erro: ${error_rate}%" | tee -a $report_file

# Latência
latency=$(query_prometheus 'histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))')
echo "Latência (p95): ${latency}s" | tee -a $report_file

# Uso de CPU
cpu_usage=$(query_prometheus 'avg(rate(container_cpu_usage_seconds_total{container!=""}[5m]) * 100) by (container)')
echo "Uso de CPU: ${cpu_usage}%" | tee -a $report_file

# Uso de memória
memory_usage=$(query_prometheus 'avg(container_memory_usage_bytes{container!=""} / container_spec_memory_limit_bytes * 100) by (container)')
echo "Uso de memória: ${memory_usage}%" | tee -a $report_file

# Espaço em disco
disk_usage=$(query_prometheus '(node_filesystem_size_bytes - node_filesystem_free_bytes) / node_filesystem_size_bytes * 100')
echo "Uso de disco: ${disk_usage}%" | tee -a $report_file

# Verificar backups
echo -e "\nVerificando status dos backups..." | tee -a $report_file
last_backup=$(query_prometheus 'backup_success_timestamp')
current_time=$(date +%s)
backup_age=$((current_time - last_backup))

if [ $backup_age -lt 86400 ]; then
    echo "✅ Backup: Atualizado (última execução há $(($backup_age/3600))h)" | tee -a $report_file
else
    echo "❌ Backup: Desatualizado (última execução há $(($backup_age/3600))h)" | tee -a $report_file
fi

# Verificar circuit breakers
echo -e "\nVerificando circuit breakers..." | tee -a $report_file
tripped_breakers=$(query_prometheus 'count(circuit_breaker_state{state="open"})')
if [ "$tripped_breakers" -eq "0" ]; then
    echo "✅ Circuit Breakers: Todos fechados" | tee -a $report_file
else
    echo "❌ Circuit Breakers: $tripped_breakers aberto(s)" | tee -a $report_file
fi

# Verificar tráfego anormal
echo -e "\nVerificando padrões de tráfego..." | tee -a $report_file
traffic_anomaly=$(query_prometheus 'rate(http_requests_total[5m]) > 2 * avg_over_time(rate(http_requests_total[1h])[1d:1h])')
if [ "$traffic_anomaly" -eq "0" ]; then
    echo "✅ Tráfego: Normal" | tee -a $report_file
else
    echo "⚠️ Tráfego: Pico detectado" | tee -a $report_file
fi

echo -e "\nRelatório completo salvo em: $report_file"

# Enviar métricas para o Pushgateway
echo "Enviando métricas para o Pushgateway..."
curl -X POST -H "Content-Type: text/plain" --data-binary "
# TYPE health_check_status gauge
health_check_status{check=\"error_rate\"} $error_rate
health_check_status{check=\"latency\"} $latency
health_check_status{check=\"cpu_usage\"} $cpu_usage
health_check_status{check=\"memory_usage\"} $memory_usage
health_check_status{check=\"disk_usage\"} $disk_usage
health_check_status{check=\"backup_age\"} $backup_age
health_check_status{check=\"tripped_breakers\"} $tripped_breakers
" http://pushgateway:9091/metrics/job/health_check 