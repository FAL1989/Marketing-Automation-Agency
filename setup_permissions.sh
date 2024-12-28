#!/bin/bash

# Criar diretórios necessários
mkdir -p loki/data/{wal,index,chunks}
mkdir -p tempo/data

# Ajustar permissões para o Loki (UID 10001)
chown -R 10001:10001 loki/data

# Ajustar permissões para o Tempo
chmod -R 777 tempo/data

echo "Permissões configuradas com sucesso!" 