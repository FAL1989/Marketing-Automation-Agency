# Documentação da API AI Agency

## Visão Geral

A API do AI Agency fornece endpoints para geração de conteúdo usando múltiplos provedores de IA, gerenciamento de templates e monitoramento do sistema.

## Endpoints Principais

### Autenticação
- `POST /auth/token`: Obter token de acesso JWT

### Geração de Conteúdo
- `POST /content/generate`: Gerar conteúdo usando template
- `GET /content/status/{request_id}`: Verificar status da geração

### Templates
- `GET /templates`: Listar templates disponíveis
- `POST /templates`: Criar novo template

### Provedores
- `GET /providers/status`: Status dos provedores de IA

### Monitoramento
- `GET /monitoring/metrics`: Métricas do sistema

## Autenticação

A API usa autenticação JWT (JSON Web Token). Para acessar endpoints protegidos:

1. Obtenha um token via `POST /auth/token`
2. Inclua o token no header Authorization: `Bearer {seu_token}`

## Rate Limiting

- Limite padrão: 100 requisições por minuto por IP
- Endpoints de geração têm limites específicos por provedor:
  - OpenAI: 100 tokens/s
  - Anthropic: 50 tokens/s
  - Cohere: 20 tokens/s

## Respostas de Erro

A API usa códigos HTTP padrão:

- `400`: Parâmetros inválidos
- `401`: Não autorizado
- `403`: Acesso proibido
- `404`: Recurso não encontrado
- `429`: Rate limit excedido
- `500`: Erro interno do servidor

## Exemplos de Uso

### Gerando Conteúdo

```bash
# Autenticação
curl -X POST http://localhost:8000/auth/token \
  -H "Content-Type: application/json" \
  -d '{"username": "user@example.com", "password": "senha123"}'

# Geração de conteúdo
curl -X POST http://localhost:8000/content/generate \
  -H "Authorization: Bearer {seu_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "template_id": "550e8400-e29b-41d4-a716-446655440000",
    "variables": {
      "topic": "Inteligência Artificial",
      "tone": "profissional"
    },
    "provider": "openai"
  }'
```

## Webhooks

Para receber notificações quando a geração de conteúdo for concluída:

1. Configure um endpoint em seu sistema
2. Adicione a URL do webhook ao criar o template
3. Receberá POST com o resultado quando concluído

## Ambientes

- Desenvolvimento: http://localhost:8000
- Staging: https://staging.aiagency.com
- Produção: https://api.aiagency.com

## Ferramentas de Desenvolvimento

- [Swagger UI](http://localhost:8000/docs): Documentação interativa
- [ReDoc](http://localhost:8000/redoc): Documentação alternativa
- [Postman Collection](./postman/ai_agency.json): Coleção Postman

## Suporte

- Email: backend@aiagency.com
- Documentação completa: https://docs.aiagency.com
- Status do sistema: https://status.aiagency.com 