#!/bin/bash

set -e

echo "=== Sistema de Restauração ==="

# Verificar se o backup foi especificado
if [ -z "$1" ]; then
    echo "❌ Uso: $0 <nome_do_backup>"
    exit 1
fi

BACKUP_NAME=$1
BACKUP_DIR="backups"
RESTORE_DIR="${BACKUP_DIR}/restore_${BACKUP_NAME}"

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

# 0. Verificar existência do backup
echo -e "\n0. Verificando backup..."
if [ ! -f "${BACKUP_DIR}/${BACKUP_NAME}.tar.gz" ]; then
    # Tentar baixar do S3
    if [ ! -z "${AWS_ACCESS_KEY_ID}" ] && [ ! -z "${AWS_SECRET_ACCESS_KEY}" ]; then
        aws s3 cp "s3://${S3_BUCKET}/backups/${BACKUP_NAME}.tar.gz" "${BACKUP_DIR}/"
    else
        log_error "Backup não encontrado: ${BACKUP_NAME}"
    fi
fi

# 1. Extrair backup
echo -e "\n1. Extraindo backup..."
mkdir -p "${RESTORE_DIR}"
tar -xzf "${BACKUP_DIR}/${BACKUP_NAME}.tar.gz" -C "${RESTORE_DIR}"

# 2. Verificar integridade
echo -e "\n2. Verificando integridade..."
if [ ! -d "${RESTORE_DIR}/${BACKUP_NAME}" ]; then
    log_error "Backup corrompido ou incompleto"
fi

# 3. Backup do estado atual (segurança)
echo -e "\n3. Realizando backup de segurança..."
./scripts/backup.sh
if [ $? -ne 0 ]; then
    log_error "Falha ao criar backup de segurança"
fi

# 4. Restaurar configurações
echo -e "\n4. Restaurando configurações..."
kubectl cp "${RESTORE_DIR}/${BACKUP_NAME}/config/prometheus.yml" production/prometheus:/etc/prometheus/prometheus.yml
kubectl cp "${RESTORE_DIR}/${BACKUP_NAME}/config/prometheus_rules" production/prometheus:/etc/prometheus/rules
kubectl cp "${RESTORE_DIR}/${BACKUP_NAME}/config/alertmanager.yml" production/alertmanager:/etc/alertmanager/alertmanager.yml
kubectl cp "${RESTORE_DIR}/${BACKUP_NAME}/config/alertmanager_templates" production/alertmanager:/etc/alertmanager/templates

# 5. Restaurar recursos do Kubernetes
echo -e "\n5. Restaurando recursos do Kubernetes..."
kubectl apply -f "${RESTORE_DIR}/${BACKUP_NAME}/kubernetes/configmaps.yaml"
kubectl apply -f "${RESTORE_DIR}/${BACKUP_NAME}/kubernetes/secrets.yaml"
kubectl apply -f "${RESTORE_DIR}/${BACKUP_NAME}/kubernetes/persistent_volumes.yaml"
kubectl apply -f "${RESTORE_DIR}/${BACKUP_NAME}/kubernetes/all_resources.yaml"

# 6. Restaurar banco de dados
echo -e "\n6. Restaurando banco de dados..."
PGPASSWORD=${DB_PASSWORD} pg_restore -h ${DB_HOST} -U ${DB_USER} -d ${DB_NAME} -c "${RESTORE_DIR}/${BACKUP_NAME}/database/postgres_dump.backup"

# 7. Restaurar arquivos persistentes
echo -e "\n7. Restaurando arquivos persistentes..."
kubectl cp "${RESTORE_DIR}/${BACKUP_NAME}/files/uploads" production/ai-platform-backend:/app/uploads
kubectl cp "${RESTORE_DIR}/${BACKUP_NAME}/files/static" production/ai-platform-backend:/app/static

# 8. Reiniciar serviços
echo -e "\n8. Reiniciando serviços..."
kubectl rollout restart deployment/ai-platform-backend -n production
kubectl rollout restart deployment/prometheus -n production
kubectl rollout restart deployment/alertmanager -n production

# 9. Verificar saúde
echo -e "\n9. Verificando saúde dos serviços..."
sleep 30  # Aguardar reinicialização dos serviços

if ! check_health; then
    log_error "Serviços não estão saudáveis após restauração"
fi

# 10. Limpeza
echo -e "\n10. Realizando limpeza..."
rm -rf "${RESTORE_DIR}"

# 11. Notificar equipe
echo -e "\n11. Enviando notificação..."
if [ ! -z "${SLACK_WEBHOOK_URL}" ]; then
    curl -X POST -H "Content-Type: application/json" \
         -d "{\"text\":\"Restauração do backup ${BACKUP_NAME} concluída com sucesso em $(date)\"}" \
         "${SLACK_WEBHOOK_URL}"
fi

echo -e "\n=== Restauração concluída com sucesso! ===" 