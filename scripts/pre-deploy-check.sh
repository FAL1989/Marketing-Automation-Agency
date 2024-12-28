#!/bin/bash

echo "=== Iniciando verificação pré-deploy ==="

# Verificar variáveis de ambiente
echo -e "\n1. Verificando variáveis de ambiente..."
required_vars=(
  "NODE_ENV"
  "DATABASE_URL"
  "JWT_SECRET"
  "OPENAI_API_KEY"
  "ANTHROPIC_API_KEY"
  "COHERE_API_KEY"
)

missing_vars=0
for var in "${required_vars[@]}"; do
  if [ -z "${!var}" ]; then
    echo "❌ Variável $var não está definida"
    missing_vars=$((missing_vars + 1))
  else
    echo "✅ Variável $var está definida"
  fi
done

# Verificar dependências
echo -e "\n2. Verificando dependências..."
npm list --prod --json > /dev/null 2>&1
if [ $? -eq 0 ]; then
  echo "✅ Todas as dependências estão instaladas corretamente"
else
  echo "❌ Problemas encontrados com as dependências"
  missing_vars=$((missing_vars + 1))
fi

# Verificar conexão com serviços externos
echo -e "\n3. Verificando conexão com serviços externos..."
services=(
  "https://api.openai.com/v1/models"
  "https://api.anthropic.com/v1/complete"
  "https://api.cohere.ai/v1/generate"
)

for service in "${services[@]}"; do
  if curl --output /dev/null --silent --head --fail "$service"; then
    echo "✅ Conexão com $service está funcionando"
  else
    echo "❌ Não foi possível conectar com $service"
    missing_vars=$((missing_vars + 1))
  fi
done

# Verificar certificados SSL
echo -e "\n4. Verificando certificados SSL..."
if [ -f "./ssl/cert.pem" ] && [ -f "./ssl/key.pem" ]; then
  echo "✅ Certificados SSL encontrados"
  # Verificar validade
  openssl x509 -in ./ssl/cert.pem -noout -dates | grep "notAfter"
else
  echo "❌ Certificados SSL não encontrados"
  missing_vars=$((missing_vars + 1))
fi

# Resultado final
echo -e "\n=== Resultado da verificação ==="
if [ $missing_vars -eq 0 ]; then
  echo "✅ Todas as verificações passaram!"
  exit 0
else
  echo "❌ Foram encontrados $missing_vars problemas que precisam ser corrigidos."
  exit 1
fi 