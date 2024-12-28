# Guia de Ambiente de Desenvolvimento

## Introdução
Este guia explica como configurar e manter um ambiente de desenvolvimento para o AI Agency.

## Requisitos

### Sistema Operacional
- Linux (Ubuntu 20.04+ recomendado)
- macOS (Catalina+)
- Windows 10/11 com WSL2

### Software Base
- Git 2.30+
- Docker 20.10+
- Docker Compose 2.0+
- Node.js 18+
- Python 3.10+
- kubectl 1.25+

### IDEs Recomendadas
- VSCode com extensões:
  - Python
  - React
  - Docker
  - Kubernetes
  - ESLint
  - Prettier
- PyCharm Professional
- WebStorm

## Setup Inicial

### 1. Clonagem do Repositório
```bash
git clone https://github.com/aiagency/aiagency.git
cd aiagency
```

### 2. Configuração do Python
```bash
# Criar ambiente virtual
python -m venv venv

# Ativar ambiente
source venv/bin/activate  # Linux/macOS
.\venv\Scripts\activate   # Windows

# Instalar dependências
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 3. Configuração do Node.js
```bash
# Instalar dependências
cd frontend
npm install

# Configurar husky para git hooks
npm run prepare
```

### 4. Configuração do Docker
```bash
# Build das imagens
docker-compose build

# Iniciar serviços
docker-compose up -d
```

### 5. Configuração do Kubernetes
```bash
# Aplicar configurações
kubectl apply -f k8s/dev/

# Verificar status
kubectl get pods
```

## Estrutura do Projeto

### Diretórios Principais
```
aiagency/
├── backend/
│   ├── api/
│   ├── core/
│   └── tests/
├── frontend/
│   ├── src/
│   ├── public/
│   └── tests/
├── k8s/
│   ├── dev/
│   └── prod/
└── docs/
    ├── api/
    └── guides/
```

### Arquivos de Configuração
```yaml
# .env.example
API_URL=http://localhost:8000
DB_HOST=localhost
DB_PORT=5432
DB_NAME=aiagency
DB_USER=postgres
DB_PASSWORD=postgres
```

## Workflows de Desenvolvimento

### 1. Desenvolvimento Local

#### Backend
```bash
# Ativar ambiente virtual
source venv/bin/activate

# Executar servidor de desenvolvimento
python manage.py runserver

# Executar testes
pytest
```

#### Frontend
```bash
# Iniciar servidor de desenvolvimento
npm run dev

# Executar testes
npm test

# Lint e formatação
npm run lint
npm run format
```

### 2. Desenvolvimento com Docker

#### Comandos Principais
```bash
# Iniciar todos os serviços
docker-compose up -d

# Logs de serviços específicos
docker-compose logs -f api

# Executar comandos em containers
docker-compose exec api python manage.py migrate
```

#### Hot Reload
- Backend: Montagem de volume em `/app`
- Frontend: Montagem de volume em `/app/src`

### 3. Desenvolvimento com Kubernetes

#### Comandos Principais
```bash
# Aplicar configurações
kubectl apply -f k8s/dev/

# Port-forward para serviços
kubectl port-forward svc/api 8000:8000

# Logs de pods
kubectl logs -f deployment/api
```

## Melhores Práticas

### 1. Controle de Versão

#### Branches
- `main`: Produção
- `develop`: Desenvolvimento
- `feature/*`: Novas funcionalidades
- `bugfix/*`: Correções
- `release/*`: Preparação para release

#### Commits
```bash
# Formato
<tipo>(<escopo>): <descrição>

# Exemplos
feat(api): adiciona endpoint de métricas
fix(ui): corrige layout do dashboard
docs(readme): atualiza instruções de setup
```

### 2. Qualidade de Código

#### Linting
```bash
# Backend
flake8
black .
isort .

# Frontend
npm run lint
npm run format
```

#### Testes
```bash
# Backend
pytest --cov

# Frontend
npm test -- --coverage
```

### 3. Segurança

#### Credenciais
- Use `.env` para variáveis de ambiente
- Nunca commite credenciais
- Use secrets do Kubernetes

#### Dependências
- Mantenha dependências atualizadas
- Use `npm audit` e `safety check`
- Configure Dependabot

## Troubleshooting

### Problemas Comuns

#### 1. Conflitos de Porta
```bash
# Verificar portas em uso
netstat -tulpn | grep LISTEN

# Matar processo
kill -9 $(lsof -t -i:8000)
```

#### 2. Problemas de Dependência
```bash
# Limpar cache npm
npm cache clean --force

# Reinstalar node_modules
rm -rf node_modules
npm install
```

#### 3. Problemas de Docker
```bash
# Limpar containers e volumes
docker-compose down -v
docker system prune -af

# Reconstruir imagens
docker-compose build --no-cache
```

## Monitoramento Local

### Métricas

#### Backend
```bash
# Prometheus metrics
curl localhost:8000/metrics

# Profile Python
python -m cProfile script.py
```

#### Frontend
```bash
# Lighthouse
npm run lighthouse

# Bundle analysis
npm run analyze
```

### Logs

#### Estrutura
```json
{
  "timestamp": "2024-01-20T10:30:00Z",
  "level": "DEBUG",
  "service": "api",
  "message": "Request processed",
  "metadata": {
    "method": "GET",
    "path": "/api/v1/templates",
    "duration_ms": 45
  }
}
```

#### Visualização
- Kibana local
- Grafana
- Console logs

## Recursos Adicionais

### Documentação
- [Guia de Arquitetura](/docs/architecture)
- [Guia de API](/docs/api)
- [Guia de Frontend](/docs/frontend)

### Ferramentas
- [Scripts úteis](/scripts)
- [Configurações de IDE](/docs/ide)
- [Templates git](/docs/git)

### Suporte
- Canal Slack: #dev-support
- Wiki do projeto
- FAQ técnico 