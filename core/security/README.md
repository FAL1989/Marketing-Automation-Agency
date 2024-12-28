# Sistema de Segurança

## Visão Geral
O módulo de segurança é responsável por garantir a proteção, autenticação e autorização em toda a plataforma, implementando as melhores práticas de segurança e conformidade.

## Arquitetura

### Estrutura do Módulo
```
security/
├── auth/             # Sistema de autenticação
│   ├── jwt.py       # Implementação JWT
│   └── oauth.py     # Integração OAuth
├── rbac/            # Controle de acesso baseado em roles
├── encryption/      # Serviços de criptografia
└── audit/          # Sistema de auditoria
```

### Fluxo de Autenticação
1. Requisição recebida
2. Verificação de token JWT
3. Validação de permissões
4. Registro de auditoria
5. Execução da operação
6. Log de resultado

## Autenticação

### JWT (JSON Web Tokens)
```python
from core.security import auth

# Gerar token
token = auth.create_token(
    user_id="123",
    roles=["admin"],
    exp=3600  # 1 hora
)

# Validar token
try:
    payload = auth.validate_token(token)
    user_id = payload.get("user_id")
except auth.InvalidToken:
    # Token inválido
except auth.ExpiredToken:
    # Token expirado
```

### OAuth2
```python
from core.security import oauth

# Configurar providers
oauth.configure_provider(
    name="google",
    client_id="...",
    client_secret="..."
)

# Autenticar usuário
user = await oauth.authenticate(
    provider="google",
    code="..."
)
```

## Controle de Acesso (RBAC)

### Roles e Permissões
```python
from core.security import rbac

# Definir roles
admin_role = rbac.Role(
    name="admin",
    permissions=[
        "create:template",
        "delete:template",
        "manage:users"
    ]
)

# Verificar permissão
@rbac.require_permission("create:template")
async def create_template():
    # Implementação protegida
    pass
```

### Políticas de Acesso
```python
# Definir política
policy = rbac.Policy(
    resource="template",
    action="create",
    effect="allow",
    conditions={
        "user.role": ["admin", "editor"],
        "template.owner": "${user.id}"
    }
)

# Avaliar política
allowed = await rbac.evaluate_policy(
    user=current_user,
    resource="template",
    action="create"
)
```

## Criptografia

### Dados em Repouso
```python
from core.security import encryption

# Criptografar dados
encrypted = encryption.encrypt(
    data="dados sensíveis",
    key_id="master-key"
)

# Descriptografar dados
decrypted = encryption.decrypt(
    data=encrypted,
    key_id="master-key"
)
```

### Hashing de Senhas
```python
# Hash de senha
hashed = encryption.hash_password("senha123")

# Verificar senha
valid = encryption.verify_password(
    "senha123",
    hashed
)
```

## Auditoria

### Logs de Auditoria
```python
from core.security import audit

# Registrar evento
audit.log_event(
    action="template.create",
    user_id="123",
    resource_id="template-456",
    details={
        "name": "Novo Template",
        "public": True
    }
)

# Consultar logs
events = await audit.query_events(
    action="template.create",
    user_id="123",
    start_date="2024-01-01",
    end_date="2024-01-31"
)
```

### Alertas de Segurança
```python
# Configurar alerta
alert = audit.SecurityAlert(
    name="suspicious_login",
    condition="login_failures > 5",
    severity="high",
    actions=["notify_admin", "block_ip"]
)

# Registrar alerta
audit.register_alert(alert)
```

## Configuração

### Variáveis de Ambiente
```env
# JWT
JWT_SECRET=your-secret-key
JWT_EXPIRATION=3600
JWT_REFRESH_EXPIRATION=604800

# OAuth
OAUTH_GOOGLE_CLIENT_ID=...
OAUTH_GOOGLE_CLIENT_SECRET=...

# Encryption
ENCRYPTION_MASTER_KEY=...
ENCRYPTION_KEY_ROTATION_DAYS=90

# Audit
AUDIT_LOG_RETENTION_DAYS=365
AUDIT_STORAGE_PATH=/var/log/audit
```

### Configuração via Código
```python
from core.security import config

# Configurar JWT
config.configure_jwt(
    secret="your-secret-key",
    expiration=3600,
    algorithm="HS256"
)

# Configurar criptografia
config.configure_encryption(
    master_key="...",
    rotation_days=90
)

# Configurar auditoria
config.configure_audit(
    retention_days=365,
    storage_path="/var/log/audit"
)
```

## Rate Limiting

### Configuração
```python
from core.security import rate_limit

# Configurar limites
limiter = rate_limit.Limiter(
    name="api_calls",
    limit=100,
    period=60  # 100 chamadas por minuto
)

# Aplicar limite
@rate_limit.limit("api_calls")
async def protected_endpoint():
    # Implementação
    pass
```

### Políticas de Rate Limiting
```python
# Por IP
ip_policy = rate_limit.Policy(
    type="ip",
    limit=1000,
    period=3600
)

# Por usuário
user_policy = rate_limit.Policy(
    type="user",
    limit=100,
    period=60
)
```

## Proteção contra Ataques

### XSS Protection
```python
from core.security import xss

# Sanitizar input
safe_html = xss.sanitize(user_input)

# Validar conteúdo
is_safe = xss.validate(content)
```

### CSRF Protection
```python
# Gerar token
token = csrf.generate_token(session_id)

# Validar token
is_valid = csrf.validate_token(token, session_id)
```

## Monitoramento

### Métricas de Segurança
- Tentativas de login
- Falhas de autenticação
- Violações de RBAC
- Eventos suspeitos

### Dashboards
- `/security/overview`
- `/security/auth-metrics`
- `/security/audit-logs`

## Troubleshooting

### Problemas Comuns

1. **Token Inválido**
```
Causa: Assinatura inválida ou token expirado
Solução: Verificar configuração JWT e tempo
```

2. **Acesso Negado**
```
Causa: Permissões insuficientes
Solução: Verificar RBAC e roles
```

3. **Rate Limit Excedido**
```
Causa: Muitas requisições
Solução: Ajustar limites ou otimizar chamadas
```

## Manutenção

### Rotação de Chaves
- Rotação automática de chaves
- Período configurável
- Backup de chaves antigas

### Limpeza
- Logs de auditoria antigos
- Tokens expirados
- Dados temporários

## Conformidade

### Padrões Suportados
- GDPR
- LGPD
- SOC 2
- ISO 27001

### Relatórios
- Logs de auditoria
- Relatórios de conformidade
- Métricas de segurança

## Contribuição

### Guidelines
1. Seguir práticas OWASP
2. Documentar mudanças
3. Adicionar testes
4. Revisar impacto

### Processo
1. Análise de segurança
2. Implementação
3. Testes de segurança
4. Review de código

## Suporte
- Docs: https://docs.aiagency.com/core/security
- Chat: #security-support
- Email: security@aiagency.com 