#!/bin/bash

set -e

echo "=== Sistema de Backup ==="

# Configurações
BACKUP_DIR="backups"
RETENTION_DAYS=30
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="backup_${TIMESTAMP}"

# Funções de utilidade
log_success() {
    echo "✅ $1"
}

log_error() {
    echo "❌ $1"
    exit 1
}

# Criar diretório de backup se não existir
mkdir -p "${BACKUP_DIR}"

# 1. Backup do estado do Kubernetes
echo -e "\n1. Realizando backup do estado do Kubernetes..."
mkdir -p "${BACKUP_DIR}/${BACKUP_NAME}/kubernetes"

# 1.1 Backup de todos os recursos do namespace
kubectl get all -n production -o yaml > "${BACKUP_DIR}/${BACKUP_NAME}/kubernetes/all_resources.yaml"
kubectl get configmap -n production -o yaml > "${BACKUP_DIR}/${BACKUP_NAME}/kubernetes/configmaps.yaml"
kubectl get secret -n production -o yaml > "${BACKUP_DIR}/${BACKUP_NAME}/kubernetes/secrets.yaml"
kubectl get pvc -n production -o yaml > "${BACKUP_DIR}/${BACKUP_NAME}/kubernetes/persistent_volumes.yaml"

# 2. Backup do banco de dados
echo -e "\n2. Realizando backup do banco de dados..."
mkdir -p "${BACKUP_DIR}/${BACKUP_NAME}/database"

# 2.1 Backup do PostgreSQL
PGPASSWORD=${DB_PASSWORD} pg_dump -h ${DB_HOST} -U ${DB_USER} -d ${DB_NAME} -F c -f "${BACKUP_DIR}/${BACKUP_NAME}/database/postgres_dump.backup"

# 3. Backup dos arquivos persistentes
echo -e "\n3. Realizando backup de arquivos persistentes..."
mkdir -p "${BACKUP_DIR}/${BACKUP_NAME}/files"

# 3.1 Backup de uploads e arquivos estáticos
kubectl cp production/ai-platform-backend:/app/uploads "${BACKUP_DIR}/${BACKUP_NAME}/files/uploads"
kubectl cp production/ai-platform-backend:/app/static "${BACKUP_DIR}/${BACKUP_NAME}/files/static"

# 4. Backup das configurações
echo -e "\n4. Realizando backup das configurações..."
mkdir -p "${BACKUP_DIR}/${BACKUP_NAME}/config"

# 4.1 Backup do Prometheus
kubectl cp production/prometheus:/etc/prometheus/prometheus.yml "${BACKUP_DIR}/${BACKUP_NAME}/config/prometheus.yml"
kubectl cp production/prometheus:/etc/prometheus/rules "${BACKUP_DIR}/${BACKUP_NAME}/config/prometheus_rules"

# 4.2 Backup do Alertmanager
kubectl cp production/alertmanager:/etc/alertmanager/alertmanager.yml "${BACKUP_DIR}/${BACKUP_NAME}/config/alertmanager.yml"
kubectl cp production/alertmanager:/etc/alertmanager/templates "${BACKUP_DIR}/${BACKUP_NAME}/config/alertmanager_templates"

# 5. Compactar backup
echo -e "\n5. Compactando backup..."
cd "${BACKUP_DIR}"
tar -czf "${BACKUP_NAME}.tar.gz" "${BACKUP_NAME}"
rm -rf "${BACKUP_NAME}"

# 6. Enviar para armazenamento externo
echo -e "\n6. Enviando backup para armazenamento externo..."
if [ ! -z "${AWS_ACCESS_KEY_ID}" ] && [ ! -z "${AWS_SECRET_ACCESS_KEY}" ]; then
    aws s3 cp "${BACKUP_NAME}.tar.gz" "s3://${S3_BUCKET}/backups/"
    log_success "Backup enviado para S3"
else
    log_error "Credenciais AWS não configuradas"
fi

# 7. Limpeza de backups antigos
echo -e "\n7. Removendo backups antigos..."
find "${BACKUP_DIR}" -name "backup_*.tar.gz" -mtime +${RETENTION_DAYS} -delete

# 8. Verificar backup
echo -e "\n8. Verificando integridade do backup..."
if tar -tzf "${BACKUP_NAME}.tar.gz" > /dev/null; then
    log_success "Backup íntegro"
else
    log_error "Backup corrompido"
fi

# 9. Registrar metadados do backup
echo -e "\n9. Registrando metadados..."
cat > "${BACKUP_DIR}/${BACKUP_NAME}_metadata.json" << EOF
{
    "backup_name": "${BACKUP_NAME}",
    "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
    "size": "$(du -h "${BACKUP_NAME}.tar.gz" | cut -f1)",
    "components": {
        "kubernetes": true,
        "database": true,
        "files": true,
        "config": true
    },
    "retention_days": ${RETENTION_DAYS}
}
EOF

# 10. Notificar equipe
echo -e "\n10. Enviando notificação..."
if [ ! -z "${SLACK_WEBHOOK_URL}" ]; then
    curl -X POST -H "Content-Type: application/json" \
         -d "{\"text\":\"Backup ${BACKUP_NAME} realizado com sucesso em $(date)\"}" \
         "${SLACK_WEBHOOK_URL}"
fi

echo -e "\n=== Backup concluído com sucesso! ===" 