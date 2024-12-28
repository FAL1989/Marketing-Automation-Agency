#!/bin/bash

echo "=== Configurando ambiente de produção ==="

# Carregar variáveis de ambiente
echo -e "\n1. Carregando variáveis de ambiente..."
if [ -f .env.production ]; then
  export $(cat .env.production | grep -v '^#' | xargs)
  echo "✅ Variáveis de ambiente carregadas"
else
  echo "❌ Arquivo .env.production não encontrado"
  exit 1
fi

# Instalar dependências de produção
echo -e "\n2. Instalando dependências de produção..."
npm install --omit=dev
if [ $? -eq 0 ]; then
  echo "✅ Dependências instaladas com sucesso"
else
  echo "❌ Erro ao instalar dependências"
  exit 1
fi

# Executar migrations
echo -e "\n3. Executando migrations do banco de dados..."
npm run migrate
if [ $? -eq 0 ]; then
  echo "✅ Migrations executadas com sucesso"
else
  echo "❌ Erro ao executar migrations"
  exit 1
fi

# Configurar Redis
echo -e "\n4. Verificando conexão com Redis..."
if redis-cli ping > /dev/null 2>&1; then
  echo "✅ Redis está funcionando"
else
  echo "❌ Redis não está disponível"
  exit 1
fi

# Configurar monitoramento
echo -e "\n5. Configurando monitoramento..."
if [ "$ENABLE_METRICS" = "true" ]; then
  # Iniciar exportador de métricas
  npm run metrics > /dev/null 2>&1 &
  echo "✅ Monitoramento configurado na porta $METRICS_PORT"
else
  echo "ℹ️ Monitoramento desabilitado"
fi

# Verificar certificados SSL
echo -e "\n6. Verificando certificados SSL..."
if [ -f "./ssl/cert.pem" ] && [ -f "./ssl/key.pem" ]; then
  echo "✅ Certificados SSL encontrados"
  # Verificar validade
  openssl x509 -in ./ssl/cert.pem -noout -dates
else
  echo "❌ Certificados SSL não encontrados"
  exit 1
fi

# Build da aplicação
echo -e "\n7. Realizando build da aplicação..."
npm run build
if [ $? -eq 0 ]; then
  echo "✅ Build realizado com sucesso"
else
  echo "❌ Erro no build da aplicação"
  exit 1
fi

# Resultado final
echo -e "\n=== Configuração concluída ==="
echo "✅ Ambiente de produção configurado com sucesso!"
echo "Para iniciar a aplicação, execute: npm run start:prod" 