#!/bin/bash

set -e

echo "=== Configurando Backups Automáticos ==="

# Funções de utilidade
log_success() {
    echo "✅ $1"
}

log_error() {
    echo "❌ $1"
    exit 1
}

# 1. Verificar permissões
echo -e "\n1. Verificando permissões..."
if [ ! -w "/etc/cron.d" ]; then
    log_error "Permissões insuficientes. Execute como root ou sudo."
fi

# 2. Criar script wrapper
echo -e "\n2. Criando script wrapper..."
cat > /usr/local/bin/run-backup << 'EOF'
#!/bin/bash
export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

# Carregar variáveis de ambiente
source /etc/ai-platform/backup.env

# Executar backup com logs
/app/scripts/backup.sh >> /var/log/ai-platform/backup.log 2>&1
EOF

chmod +x /usr/local/bin/run-backup

# 3. Configurar diretório de logs
echo -e "\n3. Configurando diretório de logs..."
mkdir -p /var/log/ai-platform
touch /var/log/ai-platform/backup.log
chmod 644 /var/log/ai-platform/backup.log

# 4. Configurar rotação de logs
echo -e "\n4. Configurando rotação de logs..."
cat > /etc/logrotate.d/ai-platform-backup << 'EOF'
/var/log/ai-platform/backup.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 root root
}
EOF

# 5. Criar arquivo de variáveis de ambiente
echo -e "\n5. Criando arquivo de variáveis de ambiente..."
mkdir -p /etc/ai-platform
cat > /etc/ai-platform/backup.env << EOF
# Banco de dados
export DB_HOST=${DB_HOST:-localhost}
export DB_USER=${DB_USER:-postgres}
export DB_PASSWORD=${DB_PASSWORD}
export DB_NAME=${DB_NAME:-aiplatform}

# AWS S3
export AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
export AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
export S3_BUCKET=${S3_BUCKET}

# Slack
export SLACK_WEBHOOK_URL=${SLACK_WEBHOOK_URL}
EOF

chmod 600 /etc/ai-platform/backup.env

# 6. Configurar cron jobs
echo -e "\n6. Configurando cron jobs..."
cat > /etc/cron.d/ai-platform-backup << 'EOF'
# Backup diário às 2:00 AM
0 2 * * * root /usr/local/bin/run-backup

# Verificação de integridade semanal (Domingo às 3:00 AM)
0 3 * * 0 root find /backups -name "backup_*.tar.gz" -exec tar -tzf {} > /dev/null \;

# Limpeza mensal de backups antigos (Primeiro dia do mês às 4:00 AM)
0 4 1 * * root find /backups -name "backup_*.tar.gz" -mtime +30 -delete
EOF

chmod 644 /etc/cron.d/ai-platform-backup

# 7. Criar script de monitoramento
echo -e "\n7. Criando script de monitoramento..."
cat > /usr/local/bin/check-backup-status << 'EOF'
#!/bin/bash

# Verificar último backup
LAST_BACKUP=$(find /backups -name "backup_*.tar.gz" -type f -printf '%T@ %p\n' | sort -n | tail -1 | cut -f2- -d" ")
LAST_BACKUP_TIME=$(stat -c %Y "$LAST_BACKUP" 2>/dev/null || echo 0)
CURRENT_TIME=$(date +%s)
HOURS_SINCE_BACKUP=$(( (CURRENT_TIME - LAST_BACKUP_TIME) / 3600 ))

if [ $HOURS_SINCE_BACKUP -gt 25 ]; then
    echo "CRITICAL - Último backup tem mais de 25 horas (${HOURS_SINCE_BACKUP}h)"
    exit 2
elif [ $HOURS_SINCE_BACKUP -gt 24 ]; then
    echo "WARNING - Último backup tem mais de 24 horas (${HOURS_SINCE_BACKUP}h)"
    exit 1
else
    echo "OK - Último backup realizado há ${HOURS_SINCE_BACKUP}h"
    exit 0
fi
EOF

chmod +x /usr/local/bin/check-backup-status

# 8. Adicionar ao monitoramento do Prometheus
echo -e "\n8. Configurando monitoramento no Prometheus..."
cat > /etc/prometheus/rules/backup.yml << 'EOF'
groups:
  - name: backup
    rules:
      - alert: BackupAtrasado
        expr: backup_last_success_timestamp < (time() - 86400)
        for: 1h
        labels:
          severity: critical
        annotations:
          summary: Backup atrasado
          description: O último backup foi realizado há mais de 24 horas
EOF

# 9. Realizar backup inicial
echo -e "\n9. Realizando backup inicial..."
/usr/local/bin/run-backup

# 10. Verificar status
echo -e "\n10. Verificando status..."
if /usr/local/bin/check-backup-status; then
    log_success "Backup inicial realizado com sucesso"
else
    log_error "Falha no backup inicial"
fi

echo -e "\n=== Configuração de backups automáticos concluída! ===" 