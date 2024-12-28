FROM node:20-slim

WORKDIR /app

# Instalar dependências
COPY package*.json ./
RUN npm install

# Copiar o código da aplicação
COPY . .

# Expor a porta
EXPOSE 3000

# Comando para iniciar a aplicação em modo de desenvolvimento
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"] 