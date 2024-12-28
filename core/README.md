# Documentação do Core

## Visão Geral
O core do sistema é responsável por fornecer as funcionalidades fundamentais da plataforma AI Agency, incluindo:
- Gerenciamento de configurações
- Sistema de logging
- Autenticação e autorização
- Cache distribuído
- Monitoramento e métricas
- Integração com provedores de IA

## Estrutura do Core
```
core/
├── ai/              # Integrações com provedores de IA
├── monitoring/      # Sistema de monitoramento e métricas
├── security/        # Autenticação e autorização
├── config.py        # Gerenciamento de configurações
└── __init__.py
```

## Componentes Principais

### 1. Gerenciamento de Configurações (config.py)
Sistema centralizado para gerenciamento de configurações da aplicação.

**Características:**
- Carregamento de configurações de múltiplas fontes (env, arquivos, etc.)
- Validação de configurações obrigatórias
- Cache de configurações em memória
- Atualização dinâmica de configurações

**Uso:**
```python
from core.config import Config

# Carregar configurações
config = Config()

# Acessar configurações
db_url = config.get('DATABASE_URL')
api_key = config.get('API_KEY')
```

### 2. Sistema de Monitoramento (monitoring/)
Implementação do sistema de monitoramento e métricas.

**Características:**
- Coleta de métricas em tempo real
- Integração com Prometheus
- Dashboards no Grafana
- Alertas configuráveis

**Métricas Coletadas:**
- Latência de requisições
- Taxa de erros
- Uso de recursos
- Performance das integrações de IA

### 3. Segurança (security/)
Sistema de autenticação e autorização.

**Características:**
- Autenticação JWT
- Controle de acesso baseado em roles (RBAC)
- Rate limiting
- Proteção contra ataques comuns

**Funcionalidades:**
- Login/Logout
- Gerenciamento de sessões
- Renovação de tokens
- Auditoria de acessos

### 4. Integrações de IA (ai/)
Sistema de integração com múltiplos provedores de IA.

**Provedores Suportados:**
- OpenAI
- Anthropic
- Cohere

**Características:**
- Fallback automático entre provedores
- Cache de respostas
- Rate limiting por provedor
- Monitoramento de custos

## Configuração e Instalação

### Pré-requisitos
- Python 3.10+
- Redis 6.0+
- PostgreSQL 13+

### Variáveis de Ambiente
```env
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/dbname

# Redis
REDIS_URL=redis://localhost:6379

# Security
JWT_SECRET=your-secret-key
JWT_EXPIRATION=3600

# AI Providers
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-...
COHERE_API_KEY=...
```

### Instalação
```bash
# Instalar dependências
pip install -r requirements.txt

# Configurar ambiente
python -m core.setup

# Verificar instalação
python -m core.check
```

## Uso

### Exemplo de Uso Básico
```python
from core import create_app
from core.security import auth
from core.ai import ai_client

# Criar aplicação
app = create_app()

# Configurar autenticação
@app.route('/protected')
@auth.require_auth
def protected_route():
    return {'message': 'Protected endpoint'}

# Usar cliente de IA
@app.route('/generate')
@auth.require_auth
async def generate():
    response = await ai_client.generate(
        prompt="Hello, AI!",
        provider="openai"
    )
    return response
```

## Monitoramento e Métricas

### Endpoints de Métricas
- `/metrics` - Métricas do Prometheus
- `/health` - Status de saúde do sistema
- `/ready` - Readiness check

### Dashboards
- Performance geral: `http://grafana:3000/d/core-overview`
- Métricas de IA: `http://grafana:3000/d/ai-metrics`
- Segurança: `http://grafana:3000/d/security-metrics`

## Troubleshooting

### Logs
Os logs são armazenados em:
- Desenvolvimento: `logs/development.log`
- Produção: Enviados para o sistema de logging centralizado

### Problemas Comuns

1. **Erro de Conexão com Redis**
```
Causa: Redis não está acessível
Solução: Verificar status do Redis e configurações de conexão
```

2. **Falha na Autenticação**
```
Causa: Token JWT inválido ou expirado
Solução: Verificar geração do token e tempo de expiração
```

3. **Erro nos Provedores de IA**
```
Causa: Rate limiting ou API key inválida
Solução: Verificar quotas e validade das chaves
```

## Contribuição

### Guidelines
1. Seguir PEP 8 para estilo de código
2. Adicionar testes para novas funcionalidades
3. Documentar alterações no README
4. Manter cobertura de testes > 85%

### Processo de Review
1. Criar branch: `feature/nome-da-feature`
2. Implementar mudanças
3. Rodar testes: `pytest`
4. Criar PR para `main`

## Segurança

### Políticas
- Todas as senhas devem ser hasheadas
- Tokens JWT com expiração máxima de 1h
- Rate limiting por IP e por usuário
- Logs de todas as operações sensíveis

### Reporte de Vulnerabilidades
Enviar detalhes para security@aiagency.com

## Suporte
- Email: support@aiagency.com
- Slack: #core-support
- Docs: https://docs.aiagency.com/core 