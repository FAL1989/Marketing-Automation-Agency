#!/bin/bash

set -e

echo "=== Deploy Gradual em Produção ==="

# Configurações
NAMESPACE="production"
APP_NAME="ai-platform"
INITIAL_REPLICAS=3
DEPLOY_INTERVAL=300  # 5 minutos entre cada etapa
HEALTH_CHECK_RETRIES=5
HEALTH_CHECK_INTERVAL=30

# Funções de utilidade
log_success() {
    echo "✅ $1"
    # Enviar métrica para o Prometheus via pushgateway
    curl -X POST -H "Content-Type: text/plain" --data-binary "deploy_step_success{step=\"$1\"} 1" http://pushgateway:9091/metrics/job/deploy/instance/gradual
}

log_error() {
    echo "❌ $1"
    # Enviar métrica para o Prometheus
    curl -X POST -H "Content-Type: text/plain" --data-binary "deploy_step_failure{step=\"$1\"} 1" http://pushgateway:9091/metrics/job/deploy/instance/gradual
    exit 1
}

check_health() {
    local service=$1
    local retries=$HEALTH_CHECK_RETRIES
    local interval=$HEALTH_CHECK_INTERVAL

    echo "Verificando saúde do serviço $service..."
    
    for i in $(seq 1 $retries); do
        if curl --output /dev/null --silent --head --fail "http://$service:8000/health"; then
            return 0
        fi
        echo "Tentativa $i de $retries falhou. Aguardando ${interval}s..."
        sleep $interval
    done
    
    return 1
}

check_metrics() {
    local error_rate=$(curl -s "http://prometheus:9090/api/v1/query?query=rate(http_requests_total{status=~\"5..\"}[5m])/rate(http_requests_total[5m])*100" | jq '.data.result[0].value[1]')
    local latency_p95=$(curl -s "http://prometheus:9090/api/v1/query?query=histogram_quantile(0.95,rate(http_request_duration_seconds_bucket[5m]))" | jq '.data.result[0].value[1]')
    
    if (( $(echo "$error_rate > 1" | bc -l) )); then
        return 1
    fi
    
    if (( $(echo "$latency_p95 > 2" | bc -l) )); then
        return 1
    fi
    
    return 0
}

# 1. Verificações pré-deploy
echo -e "\n1. Realizando verificações pré-deploy..."

# 1.1 Verificar se temos backup recente
if ! ./scripts/backup.sh; then
    log_error "Falha ao criar backup pré-deploy"
fi

# 1.2 Verificar recursos do cluster
kubectl get nodes -o json | jq -r '.items[] | select(.status.conditions[] | select(.type=="Ready" and .status=="True")) | .metadata.name' > /dev/null
if [ $? -ne 0 ]; then
    log_error "Nós do cluster não estão prontos"
fi

# 1.3 Verificar métricas atuais
if ! check_metrics; then
    log_error "Métricas atuais estão fora dos limites aceitáveis"
fi

log_success "Verificações pré-deploy concluídas"

# 2. Deploy em staging
echo -e "\n2. Realizando deploy em staging..."
kubectl apply -f kubernetes/staging/ --namespace=staging

if ! check_health "staging-$APP_NAME"; then
    log_error "Falha no health check do ambiente de staging"
fi

log_success "Deploy em staging concluído"

# 3. Deploy gradual em produção
echo -e "\n3. Iniciando deploy gradual em produção..."

# 3.1 Deploy inicial (10% do tráfego)
echo "Fase 1: 10% do tráfego"
kubectl patch deployment $APP_NAME -n $NAMESPACE --patch '{"spec": {"strategy": {"rollingUpdate": {"maxSurge": 1, "maxUnavailable": 0}}}}'
kubectl scale deployment $APP_NAME -n $NAMESPACE --replicas=1

if ! check_health "$APP_NAME"; then
    echo "Iniciando rollback da Fase 1..."
    kubectl rollout undo deployment/$APP_NAME -n $NAMESPACE
    log_error "Falha no health check da Fase 1"
fi

if ! check_metrics; then
    echo "Iniciando rollback da Fase 1..."
    kubectl rollout undo deployment/$APP_NAME -n $NAMESPACE
    log_error "Métricas fora dos limites na Fase 1"
fi

log_success "Fase 1 concluída"
sleep $DEPLOY_INTERVAL

# 3.2 Aumentar para 50% do tráfego
echo "Fase 2: 50% do tráfego"
kubectl scale deployment $APP_NAME -n $NAMESPACE --replicas=2

if ! check_health "$APP_NAME"; then
    echo "Iniciando rollback da Fase 2..."
    kubectl rollout undo deployment/$APP_NAME -n $NAMESPACE
    log_error "Falha no health check da Fase 2"
fi

if ! check_metrics; then
    echo "Iniciando rollback da Fase 2..."
    kubectl rollout undo deployment/$APP_NAME -n $NAMESPACE
    log_error "Métricas fora dos limites na Fase 2"
fi

log_success "Fase 2 concluída"
sleep $DEPLOY_INTERVAL

# 3.3 Deploy completo (100% do tráfego)
echo "Fase 3: 100% do tráfego"
kubectl scale deployment $APP_NAME -n $NAMESPACE --replicas=$INITIAL_REPLICAS

if ! check_health "$APP_NAME"; then
    echo "Iniciando rollback da Fase 3..."
    kubectl rollout undo deployment/$APP_NAME -n $NAMESPACE
    log_error "Falha no health check da Fase 3"
fi

if ! check_metrics; then
    echo "Iniciando rollback da Fase 3..."
    kubectl rollout undo deployment/$APP_NAME -n $NAMESPACE
    log_error "Métricas fora dos limites na Fase 3"
fi

log_success "Fase 3 concluída"

# 4. Verificações pós-deploy
echo -e "\n4. Realizando verificações pós-deploy..."

# 4.1 Verificar todos os serviços
for service in $(kubectl get services -n $NAMESPACE -o jsonpath='{.items[*].metadata.name}'); do
    if ! check_health "$service"; then
        log_error "Serviço $service não está saudável após deploy"
    fi
done

# 4.2 Verificar métricas finais
if ! check_metrics; then
    log_error "Métricas finais estão fora dos limites aceitáveis"
fi

# 4.3 Verificar logs
if kubectl logs deployment/$APP_NAME -n $NAMESPACE | grep -i error > /dev/null; then
    log_error "Encontrados erros nos logs após deploy"
fi

log_success "Verificações pós-deploy concluídas"

# 5. Notificar equipe
echo -e "\n5. Enviando notificação..."
if [ ! -z "${SLACK_WEBHOOK_URL}" ]; then
    curl -X POST -H "Content-Type: application/json" \
         -d "{\"text\":\"Deploy gradual concluído com sucesso em $(date)\"}" \
         "${SLACK_WEBHOOK_URL}"
fi

echo -e "\n=== Deploy gradual concluído com sucesso! ===" 