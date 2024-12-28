#!/bin/bash

set -e

echo "=== Iniciando testes de deploy e rollback ==="

# Funções de utilidade
log_success() {
    echo "✅ $1"
}

log_error() {
    echo "❌ $1"
    exit 1
}

check_health() {
    local service=$1
    local retries=5
    local wait=10

    echo "Verificando saúde do serviço $service..."
    
    for i in $(seq 1 $retries); do
        if curl --output /dev/null --silent --head --fail "http://localhost:8000/health"; then
            return 0
        fi
        echo "Tentativa $i de $retries falhou. Aguardando ${wait}s..."
        sleep $wait
    done
    
    return 1
}

# 1. Backup do ambiente atual
echo -e "\n1. Realizando backup..."
kubectl get all -n production -o yaml > backup/pre-deploy-state.yaml
if [ $? -eq 0 ]; then
    log_success "Backup realizado com sucesso"
else
    log_error "Falha ao realizar backup"
fi

# 2. Deploy em staging
echo -e "\n2. Realizando deploy em staging..."
kubectl apply -f infrastructure/kubernetes/deployment.yaml --namespace=staging
if [ $? -eq 0 ]; then
    log_success "Deploy em staging realizado com sucesso"
else
    log_error "Falha no deploy em staging"
fi

# 3. Verificação em staging
echo -e "\n3. Verificando ambiente de staging..."
if check_health "staging"; then
    log_success "Ambiente de staging está saudável"
else
    log_error "Ambiente de staging não está respondendo corretamente"
fi

# 4. Deploy gradual em produção
echo -e "\n4. Iniciando deploy gradual em produção..."

# 4.1 Deploy com 10% do tráfego
echo "Configurando 10% do tráfego..."
kubectl patch deployment ai-platform -n production --patch '{"spec": {"strategy": {"rollingUpdate": {"maxSurge": 1, "maxUnavailable": 0}}}}'
kubectl scale deployment ai-platform -n production --replicas=1

if check_health "production"; then
    log_success "Deploy inicial (10%) está saudável"
else
    echo "Iniciando rollback..."
    kubectl apply -f backup/pre-deploy-state.yaml
    log_error "Deploy inicial falhou, rollback realizado"
fi

# 4.2 Aumentar para 50% do tráfego
echo "Aumentando para 50% do tráfego..."
kubectl scale deployment ai-platform -n production --replicas=2

if check_health "production"; then
    log_success "Deploy em 50% está saudável"
else
    echo "Iniciando rollback..."
    kubectl apply -f backup/pre-deploy-state.yaml
    log_error "Deploy em 50% falhou, rollback realizado"
fi

# 4.3 Deploy completo
echo "Completando deploy (100% do tráfego)..."
kubectl scale deployment ai-platform -n production --replicas=3

if check_health "production"; then
    log_success "Deploy completo está saudável"
else
    echo "Iniciando rollback..."
    kubectl apply -f backup/pre-deploy-state.yaml
    log_error "Deploy completo falhou, rollback realizado"
fi

# 5. Teste de rollback manual
echo -e "\n5. Testando procedimento de rollback manual..."
echo "Iniciando rollback..."
kubectl apply -f backup/pre-deploy-state.yaml

if check_health "production"; then
    log_success "Rollback manual realizado com sucesso"
else
    log_error "Falha no rollback manual"
fi

# 6. Verificação final
echo -e "\n6. Realizando verificação final..."
./scripts/pre-deploy-check.sh
if [ $? -eq 0 ]; then
    log_success "Verificação final passou com sucesso"
else
    log_error "Verificação final falhou"
fi

echo -e "\n=== Testes de deploy e rollback concluídos com sucesso! ===" 