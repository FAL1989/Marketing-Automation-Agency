#!/bin/bash

# Aguarda os serviços estarem prontos
echo "Aguardando serviços..."
sleep 5

# Executa os testes
cd /app
pytest tests/integration/ -v --log-cli-level=DEBUG 