# Módulo de Integração com IA

## Visão Geral
O módulo de IA é responsável por gerenciar todas as integrações com provedores de IA, fornecendo uma interface unificada para geração de conteúdo, com recursos de fallback, cache e monitoramento.

## Arquitetura

### Estrutura do Módulo
```
ai/
├── providers/           # Implementações específicas de cada provedor
│   ├── openai.py       # Cliente OpenAI
│   ├── anthropic.py    # Cliente Anthropic
│   └── cohere.py       # Cliente Cohere
├── cache/              # Sistema de cache de respostas
├── monitoring/         # Monitoramento específico de IA
└── client.py           # Cliente unificado de IA
```

### Fluxo de Requisições
1. Requisição recebida pelo cliente unificado
2. Verificação de cache
3. Seleção do provedor baseada em:
   - Disponibilidade
   - Custo
   - Performance
   - Requisitos específicos
4. Tentativa de geração
5. Fallback automático em caso de falha
6. Cache do resultado
7. Monitoramento e métricas

## Uso

### Cliente Unificado
```python
from core.ai import AIClient

# Inicializar cliente
client = AIClient()

# Geração simples
response = await client.generate(
    prompt="Traduza para português: Hello, world!",
    provider="openai"  # Opcional, usa o melhor provedor disponível se omitido
)

# Geração com parâmetros específicos
response = await client.generate(
    prompt="Crie um título para um artigo sobre IA",
    provider="anthropic",
    max_tokens=50,
    temperature=0.7,
    top_p=0.9
)

# Geração com fallback automático
response = await client.generate_with_fallback(
    prompt="Análise de sentimento: Ótimo produto!",
    providers=["openai", "anthropic", "cohere"]
)
```

### Cache
```python
# Configurar cache
client.configure_cache(
    ttl=3600,  # Tempo de vida em segundos
    max_size=1000  # Número máximo de itens
)

# Gerar com cache
response = await client.generate(
    prompt="Pergunta frequente",
    use_cache=True
)
```

### Rate Limiting
```python
# Configurar limites
client.configure_rate_limits(
    openai=45,      # Requisições por minuto
    anthropic=30,
    cohere=20
)
```

## Provedores Suportados

### OpenAI
- Modelos: GPT-4, GPT-3.5-turbo
- Recursos: Chat, Completions, Embeddings
- Métricas específicas: Uso de tokens, latência

### Anthropic
- Modelos: Claude 2, Claude Instant
- Recursos: Chat, Completions
- Métricas específicas: Uso de caracteres, latência

### Cohere
- Modelos: Command, Generate
- Recursos: Completions, Embeddings
- Métricas específicas: Uso de tokens, latência

## Monitoramento

### Métricas Coletadas
- Latência por provedor
- Taxa de sucesso/erro
- Uso de tokens/caracteres
- Custos estimados
- Hit rate do cache
- Taxa de fallback

### Dashboards
- Métricas em tempo real: `http://grafana:3000/d/ai-realtime`
- Custos: `http://grafana:3000/d/ai-costs`
- Performance: `http://grafana:3000/d/ai-performance`

## Configuração

### Variáveis de Ambiente
```env
# API Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-...
COHERE_API_KEY=...

# Configurações
AI_DEFAULT_PROVIDER=openai
AI_CACHE_TTL=3600
AI_MAX_RETRIES=3

# Rate Limiting
AI_RATE_LIMIT_OPENAI=45
AI_RATE_LIMIT_ANTHROPIC=30
AI_RATE_LIMIT_COHERE=20
```

### Configuração via Código
```python
from core.ai import config

# Configurar provedor padrão
config.set_default_provider('anthropic')

# Configurar timeouts
config.set_timeouts(
    connect=5.0,
    read=30.0
)

# Configurar retry
config.set_retry_policy(
    max_retries=3,
    backoff_factor=1.5
)
```

## Tratamento de Erros

### Tipos de Erros
```python
from core.ai.exceptions import (
    AIProviderError,
    AIRateLimitError,
    AITimeoutError,
    AIInvalidRequestError
)

try:
    response = await client.generate(prompt="...")
except AIRateLimitError:
    # Lidar com rate limiting
except AITimeoutError:
    # Lidar com timeout
except AIProviderError as e:
    # Lidar com erro do provedor
```

### Estratégias de Retry
- Backoff exponencial
- Jitter aleatório
- Fallback automático entre provedores

## Exemplos

### Geração de Texto
```python
# Geração simples
text = await client.generate_text(
    prompt="Escreva um parágrafo sobre IA",
    max_tokens=100
)

# Geração com controle fino
text = await client.generate_text(
    prompt="Escreva um email formal",
    style="professional",
    tone="formal",
    language="pt-BR"
)
```

### Chat
```python
# Iniciar conversa
conversation = client.create_conversation()

# Adicionar mensagens
await conversation.add_message("user", "Olá, como posso ajudar?")
await conversation.add_message("assistant", "Olá! Como posso ajudar você hoje?")

# Gerar resposta
response = await conversation.generate_reply(
    "Preciso de ajuda com programação Python"
)
```

### Embeddings
```python
# Gerar embeddings
embeddings = await client.generate_embeddings(
    texts=["texto 1", "texto 2", "texto 3"]
)

# Calcular similaridade
similarity = embeddings.calculate_similarity(
    text1="consulta",
    text2="documento"
)
```

## Segurança

### Políticas
- API keys armazenadas em secrets
- Sanitização de prompts
- Validação de saídas
- Rate limiting por usuário/IP

### Logs de Segurança
- Tentativas de acesso não autorizado
- Uso suspeito de API
- Falhas de validação

## Contribuição

### Adicionar Novo Provedor
1. Criar classe em `providers/`
2. Implementar interface padrão
3. Adicionar testes
4. Atualizar documentação

### Testes
```bash
# Rodar testes
pytest core/ai/tests/

# Testar provedor específico
pytest core/ai/tests/test_openai.py
```

## Troubleshooting

### Problemas Comuns

1. **Rate Limiting**
```
Causa: Muitas requisições em pouco tempo
Solução: Ajustar configurações de rate limiting
```

2. **Timeout**
```
Causa: Provedor demorando para responder
Solução: Aumentar timeout ou usar fallback
```

3. **Custo Alto**
```
Causa: Uso excessivo de tokens
Solução: Implementar limites por usuário/projeto
```

## Suporte
- Documentação: https://docs.aiagency.com/core/ai
- Issues: https://github.com/aiagency/core/issues
- Email: ai-support@aiagency.com 