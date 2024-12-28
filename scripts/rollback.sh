#!/bin/bash

set -e

echo "=== Iniciando procedimento de rollback ==="

# Funções de utilidade
log_success() {
    echo "✅ $1"
}

log_error() {
    echo "❌ $1"
    exit 1
}

check_health() {
    local retries=5
    local wait=10

    echo "Verificando saúde do serviço..."
    
    for i in $(seq 1 $retries); do
        if curl --output /dev/null --silent --head --fail "http://localhost:8000/health"; then
            return 0
        fi
        echo "Tentativa $i de $retries falhou. Aguardando ${wait}s..."
        sleep $wait
    done
    
    return 1
}

# 1. Verificar se existe backup
if [ ! -f "backup/pre-deploy-state.yaml" ]; then
    log_error "Arquivo de backup não encontrado em backup/pre-deploy-state.yaml"
fi

# 2. Aplicar rollback
echo -e "\n1. Aplicando estado anterior..."
kubectl apply -f backup/pre-deploy-state.yaml
if [ $? -ne 0 ]; then
    log_error "Falha ao aplicar estado anterior"
fi

# 3. Verificar saúde após rollback
echo -e "\n2. Verificando saúde após rollback..."
if check_health; then
    log_success "Serviço está saudável após rollback"
else
    log_error "Serviço não está respondendo após rollback"
fi

# 4. Verificar métricas
echo -e "\n3. Verificando métricas..."
error_rate=$(curl -s http://localhost:9090/api/v1/query?query=rate\(http_requests_total{status=~\"5..\"}[5m]\)%20/%20rate\(http_requests_total[5m]\))
if (( $(echo "$error_rate > 0.01" | bc -l) )); then
    log_error "Taxa de erro está acima de 1% após rollback"
fi

# 5. Verificar logs
echo -e "\n4. Verificando logs..."
if kubectl logs deployment/ai-platform -n production | grep -i error > /dev/null; then
    log_error "Encontrados erros nos logs após rollback"
fi

# 6. Notificar equipe
echo -e "\n5. Enviando notificação..."
curl -X POST -H "Content-Type: application/json" \
     -d "{\"text\":\"Rollback realizado com sucesso em $(date)\"}" \
     "${SLACK_WEBHOOK_URL}"

echo -e "\n=== Rollback concluído com sucesso! ===" 