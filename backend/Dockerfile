FROM python:3.12-slim

WORKDIR /app

# Instala dependências do sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    postgresql-client \
    redis-tools \
    curl \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# Copia os arquivos de requisitos primeiro para aproveitar o cache do Docker
COPY requirements.txt .
COPY requirements-test.txt .
COPY setup.py .

# Instala dependências Python
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r requirements-test.txt
RUN pip install --no-cache-dir cohere>=4.37

# Configura o PYTHONPATH e variáveis de ambiente
ENV PYTHONPATH=/app
ENV TESTING=true
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Cria diretório para logs e outros diretórios necessários
RUN mkdir -p /app/logs /app/app /app/tests /app/alembic && chmod 777 /app/logs

# Copia o resto dos arquivos do projeto
COPY . .

# Dá permissão de execução ao script de inicialização
RUN chmod +x /app/start.sh

# Expõe as portas da aplicação e métricas
EXPOSE 8000 9091

# Comando para iniciar a aplicação
CMD ["/app/start.sh"] 