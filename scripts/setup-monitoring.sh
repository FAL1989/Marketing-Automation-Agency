#!/bin/bash

set -e

echo "=== Configurando Monitoramento Contínuo ==="

# Dar permissão de execução ao script de health check
chmod +x scripts/health-check.sh

# Criar diretório para logs
mkdir -p monitoring/logs

# Configurar cron para executar o health check a cada 15 minutos
(crontab -l 2>/dev/null || true; echo "*/15 * * * * /home/fernando/Ultima_tentativa_de_fazer_o_projeto/scripts/health-check.sh >> /home/fernando/Ultima_tentativa_de_fazer_o_projeto/monitoring/logs/health-check.log 2>&1") | crontab -

# Reiniciar serviços de monitoramento
echo "Reiniciando serviços de monitoramento..."
docker-compose -f docker-compose.monitoring.yml restart prometheus grafana alertmanager pushgateway

# Verificar status dos serviços
echo "Verificando status dos serviços..."
docker-compose -f docker-compose.monitoring.yml ps

echo "Configuração do monitoramento contínuo concluída!"
echo "Os relatórios de saúde serão gerados a cada 15 minutos"
echo "Logs disponíveis em: monitoring/logs/health-check.log" 