# Documentação dos Alertas

Este documento descreve os alertas configurados no sistema, incluindo suas condições, severidades e ações recomendadas.

## Alertas de Rate Limit

### HighRateLimitViolations
- **Severidade**: Critical
- **Condição**: `sum(rate(rate_limit_violations_total[5m])) > 100`
- **Duração**: 1m
- **Descrição**: Alto número de violações de rate limit
- **Impacto**: Possível tentativa de DDoS ou abuso da API
- **Ações**:
  1. Verificar IPs com mais violações
  2. Analisar padrões de requisição
  3. Considerar blacklist temporária
  4. Ajustar limites se necessário

### SustainedRateLimitViolations
- **Severidade**: Warning
- **Condição**: `sum(rate(rate_limit_violations_total[15m])) > 50`
- **Duração**: 15m
- **Descrição**: Violações de rate limit sustentadas
- **Impacto**: Possível problema de configuração do cliente
- **Ações**:
  1. Contatar cliente se identificado
  2. Verificar documentação da API
  3. Analisar logs de uso
  4. Considerar ajustes nos limites

## Alertas de Segurança

### SecurityAttackAttempts
- **Severidade**: Critical
- **Condição**: `sum(rate(xss_attempts_total[5m]) + rate(csrf_attempts_total[5m])) > 10`
- **Duração**: 1m
- **Descrição**: Alto número de tentativas de ataque
- **Impacto**: Possível tentativa de comprometimento do sistema
- **Ações**:
  1. Identificar origem dos ataques
  2. Analisar payloads maliciosos
  3. Atualizar regras de segurança
  4. Considerar bloqueio de IPs

### UnauthorizedAccessSpike
- **Severidade**: Warning
- **Condição**: `sum(rate(unauthorized_access_total[5m])) > 20`
- **Duração**: 5m
- **Descrição**: Pico de tentativas de acesso não autorizado
- **Impacto**: Possível tentativa de força bruta
- **Ações**:
  1. Verificar logs de autenticação
  2. Analisar padrões de tentativa
  3. Reforçar políticas de senha
  4. Considerar 2FA

## Alertas de Performance

### HighLatency
- **Severidade**: Critical
- **Condição**: `histogram_quantile(0.95, sum(rate(request_latency_seconds_bucket[5m])) by (le)) > 2`
- **Duração**: 5m
- **Descrição**: Alta latência nas requisições
- **Impacto**: Degradação da experiência do usuário
- **Ações**:
  1. Verificar uso de recursos
  2. Analisar queries lentas
  3. Verificar conexões de rede
  4. Considerar otimizações

### HighErrorRate
- **Severidade**: Critical
- **Condição**: `sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m])) > 0.05`
- **Duração**: 5m
- **Descrição**: Alta taxa de erros HTTP 5xx
- **Impacto**: Falhas no serviço
- **Ações**:
  1. Verificar logs de erro
  2. Analisar stack traces
  3. Verificar dependências
  4. Considerar rollback

## Alertas de Sistema

### HighMemoryUsage
- **Severidade**: Warning
- **Condição**: `process_resident_memory_bytes / container_memory_limit_bytes > 0.85`
- **Duração**: 10m
- **Descrição**: Alto uso de memória
- **Impacto**: Possível degradação de performance
- **Ações**:
  1. Verificar memory leaks
  2. Analisar uso de recursos
  3. Considerar scaling
  4. Otimizar uso de memória

### HighCPUUsage
- **Severidade**: Warning
- **Condição**: `rate(process_cpu_seconds_total[5m]) > 0.85`
- **Duração**: 10m
- **Descrição**: Alto uso de CPU
- **Impacto**: Possível degradação de performance
- **Ações**:
  1. Verificar processos intensivos
  2. Analisar profiling
  3. Considerar scaling
  4. Otimizar processamento

## Alertas de Monitoramento

### PrometheusTargetMissing
- **Severidade**: Critical
- **Condição**: `up == 0`
- **Duração**: 5m
- **Descrição**: Target do Prometheus não responde
- **Impacto**: Perda de métricas
- **Ações**:
  1. Verificar status do serviço
  2. Analisar conectividade
  3. Verificar configuração
  4. Reiniciar se necessário

### AlertmanagerNotificationFailures
- **Severidade**: Critical
- **Condição**: `rate(alertmanager_notifications_failed_total[5m]) > 0`
- **Duração**: 5m
- **Descrição**: Falhas no envio de notificações
- **Impacto**: Alertas não entregues
- **Ações**:
  1. Verificar configuração
  2. Analisar conectividade
  3. Verificar credenciais
  4. Testar notificações

## Configuração de Roteamento

### Rotas de Alerta
```yaml
route:
  group_by: ['alertname', 'severity']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h
  receiver: 'default'
  routes:
    - match:
        severity: critical
      receiver: 'critical'
      group_wait: 0s
      repeat_interval: 1h
    - match:
        severity: warning
      receiver: 'warning'
      group_wait: 1m
      repeat_interval: 2h
```

### Receivers
```yaml
receivers:
  - name: 'critical'
    email_configs:
      - to: 'oncall@example.com'
        send_resolved: true
    slack_configs:
      - channel: '#alerts-critical'
        send_resolved: true
  
  - name: 'warning'
    email_configs:
      - to: 'alerts@example.com'
        send_resolved: true
    slack_configs:
      - channel: '#alerts-warning'
        send_resolved: true
```

## Silenciamento de Alertas

### Políticas de Silêncio
1. Manutenção Programada
   ```yaml
   matchers:
     - name: instance
       value: app-01
   startsAt: 2024-01-01T00:00:00Z
   endsAt: 2024-01-01T02:00:00Z
   createdBy: "admin"
   comment: "Manutenção programada"
   ```

2. Falso Positivo Conhecido
   ```yaml
   matchers:
     - name: alertname
       value: HighCPUUsage
     - name: instance
       value: batch-processor
   ```

### Boas Práticas
1. Sempre incluir:
   - Razão do silêncio
   - Duração esperada
   - Responsável
   - Ticket relacionado

2. Revisar regularmente:
   - Silêncios ativos
   - Silêncios expirados
   - Padrões de silenciamento

## Manutenção

### Checklist Diário
1. Verificar alertas ativos
2. Analisar falsos positivos
3. Verificar notificações pendentes

### Checklist Semanal
1. Revisar silêncios
2. Verificar latência de notificações
3. Atualizar contatos de notificação

### Checklist Mensal
1. Revisar regras de alerta
2. Atualizar thresholds
3. Testar notificações
4. Revisar documentação 