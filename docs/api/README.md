# Documentação da API

## Visão Geral
A API do AI Agency fornece endpoints para gerenciamento de templates, geração de conteúdo e monitoramento de métricas. A API segue os princípios REST e utiliza JSON para comunicação.

## Base URL
```
Desenvolvimento: http://localhost:8000/api/v1
Staging: https://staging-api.aiagency.com/v1
Produção: https://api.aiagency.com/v1
```

## Autenticação
Todas as requisições devem incluir um token JWT no header:
```
Authorization: Bearer <seu-token-jwt>
```

Para obter um token:
1. Faça login em `/auth/login`
2. Use o token retornado nas requisições
3. Renove o token em `/auth/refresh` quando necessário

## Endpoints Detalhados

### Autenticação

#### POST /auth/login
Autentica um usuário e retorna um token JWT.

**Request Body:**
```json
{
  "email": "string",
  "password": "string"
}
```

**Resposta:**
```json
{
  "access_token": "string",
  "refresh_token": "string",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

#### POST /auth/refresh
Renova um token JWT usando o refresh token.

**Request Body:**
```json
{
  "refresh_token": "string"
}
```

### Templates

#### GET /templates
Lista todos os templates disponíveis.

**Parâmetros de Query:**
- `page`: Número da página (default: 1, min: 1, max: 1000)
- `limit`: Itens por página (default: 10, min: 1, max: 100)
- `search`: Busca por nome ou descrição (min: 3 caracteres)
- `status`: Filtro por status (active, draft, archived)
- `sort`: Campo para ordenação (created_at, updated_at, name)
- `order`: Direção da ordenação (asc, desc)

**Exemplo de Sucesso:**
```json
{
  "data": [
    {
      "id": "template_123abc",
      "name": "Email Marketing",
      "description": "Template para campanhas de email",
      "status": "active",
      "parameters": [
        {
          "name": "subject",
          "type": "string",
          "required": true,
          "default": "Novidades da AI Agency"
        }
      ],
      "created_at": "2025-03-28T10:30:00Z",
      "updated_at": "2025-03-28T15:45:00Z",
      "created_by": "user_456def",
      "version": "1.0.0"
    }
  ],
  "pagination": {
    "total": 42,
    "page": 1,
    "limit": 10,
    "total_pages": 5
  }
}
```

**Exemplo de Erro - Parâmetros Inválidos:**
```json
{
  "error": {
    "code": "invalid_parameters",
    "message": "Parâmetros de paginação inválidos",
    "details": {
      "page": "Deve ser maior que 0",
      "limit": "Não pode exceder 100"
    }
  }
}
```

#### GET /templates/{id}
Retorna detalhes de um template específico.

**Parâmetros de Path:**
- `id`: ID do template

**Resposta:**
```json
{
  "id": "string",
  "name": "string",
  "description": "string",
  "content": "string",
  "status": "active",
  "parameters": [
    {
      "name": "string",
      "type": "string",
      "required": boolean,
      "default": "string",
      "description": "string"
    }
  ],
  "validation_rules": [
    {
      "field": "string",
      "rule": "string",
      "message": "string"
    }
  ],
  "metadata": {
    "version": "string",
    "tags": ["string"],
    "category": "string"
  },
  "created_at": "datetime",
  "updated_at": "datetime",
  "created_by": "string",
  "updated_by": "string"
}
```

#### POST /templates
Cria um novo template.

**Request Body:**
```json
{
  "name": "string",
  "description": "string",
  "content": "string",
  "parameters": [
    {
      "name": "string",
      "type": "string",
      "required": boolean,
      "default": "string",
      "description": "string"
    }
  ],
  "validation_rules": [
    {
      "field": "string",
      "rule": "string",
      "message": "string"
    }
  ],
  "metadata": {
    "tags": ["string"],
    "category": "string"
  }
}
```

**Resposta:**
```json
{
  "id": "string",
  "name": "string",
  "description": "string",
  "status": "active",
  "created_at": "datetime",
  "version": "string"
}
```

#### PUT /templates/{id}
Atualiza um template existente.

**Parâmetros de Path:**
- `id`: ID do template

**Request Body:**
```json
{
  "name": "string",
  "description": "string",
  "content": "string",
  "parameters": [
    {
      "name": "string",
      "type": "string",
      "required": boolean,
      "default": "string",
      "description": "string"
    }
  ],
  "validation_rules": [
    {
      "field": "string",
      "rule": "string",
      "message": "string"
    }
  ],
  "metadata": {
    "tags": ["string"],
    "category": "string"
  }
}
```

#### DELETE /templates/{id}
Remove um template.

**Parâmetros de Path:**
- `id`: ID do template

### Gerações

#### POST /generations
Gera conteúdo a partir de um template.

**Request Body:**
```json
{
  "template_id": "string",
  "parameters": {
    "key": "value"
  },
  "provider": "string",
  "options": {
    "temperature": number,
    "max_tokens": number,
    "top_p": number,
    "frequency_penalty": number,
    "presence_penalty": number
  },
  "callback_url": "string"
}
```

**Resposta:**
```json
{
  "id": "string",
  "status": "processing",
  "created_at": "datetime",
  "estimated_completion": "datetime"
}
```

#### GET /generations/{id}
Retorna o status e resultado de uma geração.

**Parâmetros de Path:**
- `id`: ID da geração

**Resposta:**
```json
{
  "id": "string",
  "template_id": "string",
  "status": "completed",
  "result": "string",
  "error": "string",
  "metrics": {
    "tokens_used": number,
    "processing_time": number,
    "provider": "string"
  },
  "created_at": "datetime",
  "completed_at": "datetime"
}
```

### Métricas

#### GET /metrics
Retorna métricas de uso e performance.

**Parâmetros de Query:**
- `start_date`: Data inicial (ISO 8601)
- `end_date`: Data final (ISO 8601)
- `type`: Tipo de métrica (usage, performance, cost)
- `interval`: Intervalo de agregação (hour, day, week, month)
- `provider`: Filtro por provedor
- `template_id`: Filtro por template

**Resposta:**
```json
{
  "period": {
    "start": "datetime",
    "end": "datetime"
  },
  "metrics": {
    "generations": {
      "total": number,
      "success": number,
      "failed": number
    },
    "tokens": {
      "total": number,
      "by_provider": {
        "openai": number,
        "anthropic": number,
        "cohere": number
      }
    },
    "costs": {
      "total": number,
      "by_provider": {
        "openai": number,
        "anthropic": number,
        "cohere": number
      }
    },
    "performance": {
      "average_latency": number,
      "p95_latency": number,
      "error_rate": number
    }
  },
  "timeline": [
    {
      "timestamp": "datetime",
      "generations": number,
      "tokens": number,
      "cost": number
    }
  ]
}
```

## Guia de Integração

### 1. Primeiros Passos

1. **Obter Credenciais**
   ```bash
   # Registre sua aplicação
   curl -X POST https://api.aiagency.com/v1/applications/register \
     -H "Content-Type: application/json" \
     -d '{
       "name": "Minha Aplicação",
       "description": "Descrição da aplicação",
       "redirect_urls": ["https://meuapp.com/callback"]
     }'
   ```

2. **Autenticação**
   ```bash
   # Login
   curl -X POST https://api.aiagency.com/v1/auth/login \
     -H "Content-Type: application/json" \
     -d '{
       "email": "user@example.com",
       "password": "senha123"
     }'
   ```

3. **Verificar Quota**
   ```bash
   # Consultar limites
   curl https://api.aiagency.com/v1/quota \
     -H "Authorization: Bearer <token>"
   ```

### 2. Fluxo Básico

1. **Criar Template**
   ```bash
   curl -X POST https://api.aiagency.com/v1/templates \
     -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" \
     -d '{
       "name": "Email Marketing",
       "description": "Template para emails",
       "content": "Olá {name},\n\n{content}\n\nAtenciosamente,\n{signature}",
       "parameters": [
         {
           "name": "name",
           "type": "string",
           "required": true,
           "description": "Nome do destinatário"
         },
         {
           "name": "content",
           "type": "string",
           "required": true,
           "description": "Conteúdo do email"
         },
         {
           "name": "signature",
           "type": "string",
           "required": true,
           "description": "Assinatura do email"
         }
       ]
     }'
   ```

2. **Gerar Conteúdo**
   ```bash
   curl -X POST https://api.aiagency.com/v1/generations \
     -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" \
     -d '{
       "template_id": "123",
       "parameters": {
         "name": "João",
         "content": "Conteúdo do email",
         "signature": "Equipe AI Agency"
       },
       "provider": "openai",
       "options": {
         "temperature": 0.7,
         "max_tokens": 500
       }
     }'
   ```

3. **Consultar Resultado**
   ```bash
   curl https://api.aiagency.com/v1/generations/456 \
     -H "Authorization: Bearer <token>"
   ```

### 3. Webhooks

1. **Configurar Webhook**
   ```bash
   curl -X POST https://api.aiagency.com/v1/webhooks \
     -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" \
     -d '{
       "url": "https://meuapp.com/webhook",
       "events": ["generation.completed", "template.updated"],
       "secret": "webhook-secret"
     }'
   ```

2. **Formato do Payload**
   ```json
   {
     "event": "generation.completed",
     "timestamp": "datetime",
     "data": {
       "generation_id": "string",
       "status": "completed",
       "result": "string"
     }
   }
   ```

### 4. Tratamento de Erros

1. **Retry com Backoff Exponencial**
   ```python
   import time
   
   def make_request_with_retry(func, max_retries=3):
       for attempt in range(max_retries):
           try:
               return func()
           except Exception as e:
               if attempt == max_retries - 1:
                   raise e
               time.sleep(2 ** attempt)
   ```

2. **Validação de Parâmetros**
   ```python
   def validate_parameters(template, parameters):
       for param in template['parameters']:
           if param['required'] and param['name'] not in parameters:
               raise ValueError(f"Parâmetro obrigatório ausente: {param['name']}")
   ```

### 5. Boas Práticas

1. **Rate Limiting**
   - Implemente cache local
   - Respeite os headers de rate limit
   - Use exponential backoff em caso de 429

2. **Segurança**
   - Armazene tokens de forma segura
   - Valide webhooks usando o secret
   - Use HTTPS para todas as requisições

3. **Monitoramento**
   - Monitore o uso de quota
   - Configure alertas para erros
   - Acompanhe métricas de performance

## Códigos de Erro

### HTTP Status Codes
- 400: Bad Request - Parâmetros inválidos
- 401: Unauthorized - Token ausente ou inválido
- 403: Forbidden - Sem permissão para o recurso
- 404: Not Found - Recurso não encontrado
- 429: Too Many Requests - Rate limit excedido
- 500: Internal Server Error - Erro interno do servidor

### Erros Específicos
```json
{
  "error": {
    "code": "string",
    "message": "string",
    "details": {
      "field": "string",
      "reason": "string"
    }
  }
}
```

### Códigos de Erro Comuns
- `invalid_parameters`: Parâmetros inválidos
- `template_not_found`: Template não encontrado
- `generation_failed`: Falha na geração
- `quota_exceeded`: Quota excedida
- `rate_limit_exceeded`: Rate limit excedido
- `invalid_token`: Token inválido
- `provider_error`: Erro do provedor de IA

## Rate Limiting

### Limites por Plano
- **Free**
  - 100 requisições por minuto por IP
  - 1000 requisições por hora por usuário
  - 50 gerações por minuto por usuário

- **Pro**
  - 500 requisições por minuto por IP
  - 5000 requisições por hora por usuário
  - 200 gerações por minuto por usuário

- **Enterprise**
  - Limites customizados

### Headers de Rate Limit
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640995200
```

## Webhooks

### Eventos Disponíveis
- `generation.completed`: Geração concluída
- `generation.failed`: Falha na geração
- `template.created`: Template criado
- `template.updated`: Template atualizado
- `template.deleted`: Template removido
- `quota.warning`: Alerta de quota
- `quota.exceeded`: Quota excedida

### Segurança
- Use HTTPS para callbacks
- Valide a assinatura do webhook
- Configure timeouts adequados

### Retry Policy
- 3 tentativas com backoff exponencial
- Intervalo inicial de 5 segundos
- Máximo de 1 hora entre tentativas 

### Segurança e Validação

#### Headers do Webhook
```
X-Webhook-ID: whk_123abc
X-Webhook-Timestamp: 2025-03-28T10:30:00Z
X-Webhook-Signature: sha256=...
```

#### Verificação da Assinatura
```python
import hmac
import hashlib

def verify_webhook_signature(payload, signature, secret):
    expected = hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(signature, expected)
```

#### Exemplo de Payload Completo
```json
{
  "id": "evt_123abc",
  "event": "generation.completed",
  "timestamp": "2025-03-28T10:30:00Z",
  "data": {
    "generation_id": "gen_456def",
    "template_id": "template_789ghi",
    "status": "completed",
    "result": "Conteúdo gerado com sucesso...",
    "metrics": {
      "tokens_used": 150,
      "processing_time_ms": 2500,
      "provider": "openai"
    }
  },
  "metadata": {
    "user_id": "user_abc123",
    "ip": "192.168.1.1",
    "user_agent": "Mozilla/5.0..."
  }
}
```

### Retry e Recuperação de Falhas

#### Política de Retry Detalhada
1. **Primeira tentativa**: Imediata
2. **Segunda tentativa**: Após 5 segundos
3. **Terceira tentativa**: Após 25 segundos
4. **Quarta tentativa**: Após 125 segundos
5. **Tentativas subsequentes**: Exponencial até 1 hora

#### Headers de Retry
```
X-Webhook-Retry-Count: 2
X-Webhook-Retry-Reason: timeout
X-Webhook-Next-Retry: 2025-03-28T10:35:00Z
```

#### Códigos de Status Esperados
- `200`: Sucesso - Evento processado
- `410`: Gone - Endpoint não existe mais
- `429`: Too Many Requests - Rate limit excedido
- `5xx`: Erro do servidor - Será feito retry

### Monitoramento de Webhooks

#### Dashboard de Webhooks
URL: `https://dashboard.aiagency.com/webhooks`

#### Métricas Disponíveis
- Taxa de sucesso/falha
- Latência média
- Número de retries
- Eventos por tipo
- Erros por categoria

#### Alertas Configuráveis
- Falhas consecutivas
- Alta latência
- Taxa de erro elevada
- Quota próxima do limite

## Tipos de Dados

### Formatos e Validações

#### Strings
- **UUID**: formato v4, exemplo: "123e4567-e89b-12d3-a456-426614174000"
- **Email**: RFC 5322, máximo 254 caracteres
- **URL**: RFC 3986, máximo 2048 caracteres
- **Nome**: 2-100 caracteres, alfanumérico com espaços
- **Descrição**: máximo 500 caracteres

#### Números
- **Inteiros**: 32 bits (-2^31 a 2^31 - 1)
- **Decimais**: Precisão de 2 casas
- **Temperature**: 0.0 a 2.0
- **Tokens**: 1 a 4096

#### Datas
- Formato: ISO 8601
- Timezone: UTC
- Exemplos:
  - Data: "2025-03-28"
  - Data/Hora: "2025-03-28T10:30:00Z"
  - Intervalo: "P1DT2H" (1 dia e 2 horas)

#### Booleanos
- true/false (lowercase)
- 1/0 não são aceitos

### Limites e Restrições

#### Templates
- Máximo de 100 templates por usuário
- Máximo de 20 parâmetros por template
- Nome: 3-50 caracteres
- Conteúdo: máximo 10000 caracteres

#### Gerações
- Máximo de 1000 gerações por hora
- Máximo de 50 gerações simultâneas
- Timeout: 30 segundos
- Resultado: máximo 100000 caracteres

#### Métricas
- Retenção: 90 dias
- Máximo de 1000 pontos por request
- Intervalo mínimo: 5 minutos