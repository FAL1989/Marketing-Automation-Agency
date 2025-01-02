#!/bin/bash

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Função para log
log() {
    echo -e "${2:-$YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

# Função para verificar Redis
check_redis() {
    python scripts/check_redis.py
    return $?
}

# Ativa o ambiente virtual
log "Ativando ambiente virtual..."
source venv/bin/activate

# Verifica se o Redis está respondendo
log "Verificando conexão Redis..."
if ! check_redis; then
    log "❌ Redis não está respondendo. Tentando iniciar localmente..." $YELLOW
    
    if command -v redis-server &> /dev/null; then
        redis-server &
        sleep 2
        
        if ! check_redis; then
            log "❌ Não foi possível conectar ao Redis. Verifique a configuração e o serviço." $RED
            exit 1
        fi
    else
        log "❌ Redis não está instalado localmente." $RED
        exit 1
    fi
fi

log "✅ Redis está funcionando corretamente!" $GREEN

# Inicia o servidor FastAPI
log "Iniciando servidor FastAPI..." $GREEN
uvicorn app.main:app --reload --log-level debug

# Captura Ctrl+C e outros sinais
trap 'log "Parando servidor..." $YELLOW; pkill -f "uvicorn"; pkill -f "redis-server"' SIGINT SIGTERM

# Aguarda o processo uvicorn
wait 