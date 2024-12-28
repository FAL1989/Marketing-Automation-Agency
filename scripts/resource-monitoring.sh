#!/bin/bash

set -e

echo "=== Monitoramento de Recursos ==="
timestamp=$(date '+%Y-%m-%d %H:%M:%S')
report_file="monitoring/resource-monitoring-${timestamp}.log"

mkdir -p monitoring

# Função para consultar o Prometheus
query_prometheus() {
    local query=$1
    local result=$(curl -s -G --data-urlencode "query=$query" http://prometheus:9090/api/v1/query | jq -r '.data.result[]')
    echo "$result"
}

# Função para formatar bytes
format_bytes() {
    local bytes=$1
    if [ $bytes -gt 1073741824 ]; then
        echo "$(echo "scale=2; $bytes/1073741824" | bc)GB"
    elif [ $bytes -gt 1048576 ]; then
        echo "$(echo "scale=2; $bytes/1048576" | bc)MB"
    elif [ $bytes -gt 1024 ]; then
        echo "$(echo "scale=2; $bytes/1024" | bc)KB"
    else
        echo "${bytes}B"
    fi
}

echo "Iniciando monitoramento de recursos..." | tee -a $report_file
echo "Timestamp: $timestamp" | tee -a $report_file
echo "----------------------------------------" | tee -a $report_file

# CPU por container
echo -e "\n1. Uso de CPU por Container" | tee -a $report_file
query_prometheus 'sum(rate(container_cpu_usage_seconds_total[5m])) by (container) * 100'

# Memória por container
echo -e "\n2. Uso de Memória por Container" | tee -a $report_file
query_prometheus 'sum(container_memory_usage_bytes) by (container)'

# Uso de disco
echo -e "\n3. Uso de Disco" | tee -a $report_file
query_prometheus '(node_filesystem_size_bytes - node_filesystem_free_bytes) / node_filesystem_size_bytes * 100'

# Network I/O
echo -e "\n4. Network I/O" | tee -a $report_file
echo "Bytes recebidos:" | tee -a $report_file
query_prometheus 'rate(container_network_receive_bytes_total[5m])'
echo "Bytes enviados:" | tee -a $report_file
query_prometheus 'rate(container_network_transmit_bytes_total[5m])'

# IOPS
echo -e "\n5. IOPS" | tee -a $report_file
echo "Leituras:" | tee -a $report_file
query_prometheus 'rate(node_disk_reads_completed_total[5m])'
echo "Escritas:" | tee -a $report_file
query_prometheus 'rate(node_disk_writes_completed_total[5m])'

# Conexões de rede
echo -e "\n6. Conexões de Rede" | tee -a $report_file
query_prometheus 'node_netstat_Tcp_CurrEstab'

# Processos
echo -e "\n7. Processos" | tee -a $report_file
query_prometheus 'node_procs_running'

# Análise de Tendências
echo -e "\n8. Análise de Tendências (últimas 24h)" | tee -a $report_file
echo "CPU:" | tee -a $report_file
query_prometheus 'avg_over_time(sum(rate(container_cpu_usage_seconds_total[5m])) by (container)[24h:1h])'
echo "Memória:" | tee -a $report_file
query_prometheus 'avg_over_time(sum(container_memory_usage_bytes) by (container)[24h:1h])'

# Alertas de Recursos
echo -e "\n9. Alertas de Recursos" | tee -a $report_file
echo "CPU > 80%:" | tee -a $report_file
query_prometheus 'count(sum(rate(container_cpu_usage_seconds_total[5m])) by (container) * 100 > 80)'
echo "Memória > 85%:" | tee -a $report_file
query_prometheus 'count(sum(container_memory_usage_bytes) by (container) / sum(container_spec_memory_limit_bytes) by (container) * 100 > 85)'
echo "Disco > 85%:" | tee -a $report_file
query_prometheus 'count((node_filesystem_size_bytes - node_filesystem_free_bytes) / node_filesystem_size_bytes * 100 > 85)'

# Resumo
echo -e "\n10. Resumo" | tee -a $report_file
echo "----------------------------------------" | tee -a $report_file
cpu_total=$(query_prometheus 'sum(rate(container_cpu_usage_seconds_total[5m])) * 100')
mem_total=$(query_prometheus 'sum(container_memory_usage_bytes)')
disk_usage=$(query_prometheus 'max((node_filesystem_size_bytes - node_filesystem_free_bytes) / node_filesystem_size_bytes * 100)')

echo "CPU Total: ${cpu_total}%" | tee -a $report_file
echo "Memória Total: $(format_bytes $mem_total)" | tee -a $report_file
echo "Uso de Disco: ${disk_usage}%" | tee -a $report_file

# Enviar métricas para o Pushgateway
echo -e "\nEnviando resultados para o Pushgateway..."
curl -X POST -H "Content-Type: text/plain" --data-binary "
# TYPE resource_monitoring_status gauge
resource_monitoring_cpu_total $cpu_total
resource_monitoring_memory_total $mem_total
resource_monitoring_disk_usage $disk_usage
" http://pushgateway:9091/metrics/job/resource_monitoring

echo -e "\nRelatório completo salvo em: $report_file" 