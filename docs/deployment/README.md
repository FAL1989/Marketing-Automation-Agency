# Guia de Deploy

## Introdução
Este guia detalha o processo de deploy do AI Agency em diferentes ambientes.

## Ambientes

### 1. Desenvolvimento
- Local development
- Feature branches
- Testes unitários
- Hot reload

### 2. Staging
- Ambiente de teste
- Branch develop
- Testes de integração
- Dados de teste

### 3. Produção
- Ambiente final
- Branch main
- Dados reais
- Alta disponibilidade

## Infraestrutura

### Kubernetes Clusters

#### Desenvolvimento
```yaml
# k8s/dev/cluster.yaml
apiVersion: k8s.io/v1
kind: Cluster
metadata:
  name: dev-cluster
spec:
  nodes: 1
  machineType: n1-standard-2
  location: us-central1
```

#### Staging
```yaml
# k8s/staging/cluster.yaml
apiVersion: k8s.io/v1
kind: Cluster
metadata:
  name: staging-cluster
spec:
  nodes: 2
  machineType: n1-standard-4
  location: us-central1
```

#### Produção
```yaml
# k8s/prod/cluster.yaml
apiVersion: k8s.io/v1
kind: Cluster
metadata:
  name: prod-cluster
spec:
  nodes: 3
  machineType: n1-standard-8
  location: us-central1
  highAvailability: true
```

## Processo de Deploy

### 1. Build

#### Frontend
```bash
# Build do frontend
cd frontend
npm install
npm run build

# Docker build
docker build -t aiagency/frontend:latest .
```

#### Backend
```bash
# Build do backend
cd backend
pip install -r requirements.txt
python -m build

# Docker build
docker build -t aiagency/backend:latest .
```

### 2. Testes

#### Pipeline de CI
```yaml
# .github/workflows/ci.yml
name: CI Pipeline
on:
  push:
    branches: [ develop, main ]
  pull_request:
    branches: [ develop ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Setup Node.js
        uses: actions/setup-node@v2
        with:
          node-version: '18'
          
      - name: Frontend Tests
        run: |
          cd frontend
          npm install
          npm test
          
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.10'
          
      - name: Backend Tests
        run: |
          cd backend
          pip install -r requirements.txt
          pytest
```

### 3. Deploy

#### Staging
```bash
# Deploy para staging
kubectl apply -f k8s/staging/

# Verificar status
kubectl get pods -n staging
kubectl get services -n staging
```

#### Produção
```bash
# Deploy para produção
kubectl apply -f k8s/prod/

# Verificar status
kubectl get pods -n production
kubectl get services -n production
```

## Configurações

### 1. Variáveis de Ambiente

#### Development
```env
NODE_ENV=development
API_URL=http://localhost:8000
DEBUG=true
LOG_LEVEL=debug
```

#### Staging
```env
NODE_ENV=staging
API_URL=https://api.staging.aiagency.com
DEBUG=false
LOG_LEVEL=info
```

#### Production
```env
NODE_ENV=production
API_URL=https://api.aiagency.com
DEBUG=false
LOG_LEVEL=warn
```

### 2. Secrets

#### Kubernetes Secrets
```yaml
# k8s/prod/secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: aiagency-secrets
type: Opaque
data:
  DB_PASSWORD: <base64>
  JWT_SECRET: <base64>
  API_KEY: <base64>
```

### 3. Recursos

#### Resource Limits
```yaml
# k8s/prod/deployment.yaml
resources:
  limits:
    cpu: "2"
    memory: "4Gi"
  requests:
    cpu: "1"
    memory: "2Gi"
```

## Monitoramento

### 1. Métricas

#### Prometheus
```yaml
# prometheus/rules.yaml
groups:
  - name: deployment
    rules:
      - alert: DeploymentFailed
        expr: kube_deployment_status_replicas_available == 0
        for: 5m
        labels:
          severity: critical
```

#### Grafana Dashboards
```json
{
  "dashboard": {
    "panels": [
      {
        "title": "Deployment Status",
        "type": "graph",
        "targets": [
          {
            "expr": "kube_deployment_status_replicas_available"
          }
        ]
      }
    ]
  }
}
```

### 2. Logs

#### Fluentd Config
```yaml
# fluentd/config.yaml
<source>
  @type kubernetes
  tag kubernetes.*
</source>

<filter kubernetes.**>
  @type kubernetes_metadata
</filter>

<match kubernetes.**>
  @type elasticsearch
  host elasticsearch
  port 9200
  logstash_format true
</match>
```

## Rollback

### 1. Procedimento

#### Automático
```bash
# Rollback automático
kubectl rollout undo deployment/frontend -n production
kubectl rollout undo deployment/backend -n production
```

#### Manual
```bash
# Rollback manual para versão específica
kubectl rollout undo deployment/frontend --to-revision=2 -n production
kubectl rollout undo deployment/backend --to-revision=2 -n production
```

### 2. Verificação

#### Health Check
```bash
# Verificar status dos pods
kubectl get pods -n production

# Verificar logs
kubectl logs deployment/frontend -n production
kubectl logs deployment/backend -n production
```

## Backup

### 1. Database

#### Backup Automático
```bash
# Script de backup
#!/bin/bash
DATE=$(date +%Y%m%d)
kubectl exec -n production $(kubectl get pod -l app=postgres -o jsonpath="{.items[0].metadata.name}") \
  -- pg_dump -U postgres aiagency > backup_${DATE}.sql
```

#### Restore
```bash
# Script de restore
#!/bin/bash
kubectl exec -i -n production $(kubectl get pod -l app=postgres -o jsonpath="{.items[0].metadata.name}") \
  -- psql -U postgres aiagency < backup_file.sql
```

### 2. Storage

#### Object Storage
```yaml
# backup/storage.yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: backup-storage
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 100Gi
```

## Checklist de Deploy

### 1. Pré-deploy
- [ ] Todos os testes passando
- [ ] Code review aprovado
- [ ] Documentação atualizada
- [ ] Backup realizado

### 2. Deploy
- [ ] Build dos containers
- [ ] Push para registry
- [ ] Apply das configurações
- [ ] Verificação de pods

### 3. Pós-deploy
- [ ] Health check
- [ ] Métricas normais
- [ ] Logs sem erros
- [ ] Funcionalidades testadas

## Recursos Adicionais

### Documentação
- [Kubernetes Guide](/docs/kubernetes)
- [Monitoring Setup](/docs/monitoring)
- [Backup Procedures](/docs/backup)

### Scripts
- [Deploy Scripts](/scripts/deploy)
- [Rollback Scripts](/scripts/rollback)
- [Backup Scripts](/scripts/backup)

### Contatos
- DevOps Team: devops@aiagency.com
- Emergency: +1 (555) 123-4567
- Slack: #deploy-alerts 