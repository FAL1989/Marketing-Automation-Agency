FROM python:3.11-slim

WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copiar arquivos de dependências
COPY requirements.txt .
COPY shared/requirements.txt ./shared-requirements.txt

# Instalar dependências Python
RUN pip install --no-cache-dir -r requirements.txt -r shared-requirements.txt

# Copiar o código da aplicação
COPY . .
COPY shared /shared

# Adicionar shared ao PYTHONPATH
ENV PYTHONPATH=/shared:$PYTHONPATH

# Expor porta
EXPOSE 8000

# Comando para iniciar a aplicação
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"] 