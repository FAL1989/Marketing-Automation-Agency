#!/bin/bash

# Aguarda PostgreSQL
until pg_isready -h $POSTGRES_HOST -p 5432 -U $POSTGRES_USER -d $POSTGRES_DB; do
  echo "Aguardando PostgreSQL..."
  sleep 2
done

# Aguarda Redis
until nc -z $REDIS_HOST $REDIS_PORT; do
  echo "Aguardando Redis..."
  sleep 2
done

# Instala o pacote em modo desenvolvimento
pip install -e .

if [ "$TESTING" = "true" ]; then
    echo "Ambiente de teste pronto para execução dos testes..."
    tail -f /dev/null  # Mantém o container rodando
else
    echo "Executando migrações..."
    alembic upgrade head
    echo "Iniciando aplicação..."
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
fi 