# Métricas de Segurança e Monitoramento

Este documento descreve as métricas disponíveis para monitoramento da aplicação, incluindo métricas de segurança, performance e utilização.

## Métricas de Rate Limit

### rate_limit_violations_total
- **Tipo**: Counter
- **Descrição**: Total de violações de rate limit
- **Labels**:
  - `path`: Caminho da requisição
  - `ip`: IP do cliente
- **Uso**: Monitorar tentativas de abuso da API
- **Alertas**:
  - Critical: > 100 violações/minuto
  - Warning: > 50 violações/minuto

### request_latency_seconds
- **Tipo**: Histogram
- **Descrição**: Latência das requisições em segundos
- **Labels**:
  - `path`: Caminho da requisição
  - `method`: Método HTTP
- **Buckets**: [0.1, 0.5, 1.0, 2.0, 5.0]
- **Uso**: Monitorar performance da API
- **Alertas**:
  - Critical: p95 > 2s
  - Warning: p95 > 1s

## Métricas de Segurança

### suspicious_ip_activity_total
- **Tipo**: Counter
- **Descrição**: Total de atividades suspeitas por IP
- **Labels**:
  - `ip`: IP do cliente
  - `activity_type`: Tipo de atividade suspeita
- **Uso**: Detectar comportamentos maliciosos
- **Alertas**:
  - Critical: > 50 atividades/minuto
  - Warning: > 20 atividades/minuto

### xss_attempts_total
- **Tipo**: Counter
- **Descrição**: Total de tentativas de XSS detectadas
- **Labels**:
  - `path`: Caminho da requisição
  - `ip`: IP do cliente
- **Uso**: Monitorar tentativas de XSS
- **Alertas**:
  - Critical: > 10 tentativas/minuto
  - Warning: > 5 tentativas/minuto

### csrf_attempts_total
- **Tipo**: Counter
- **Descrição**: Total de tentativas de CSRF detectadas
- **Labels**:
  - `path`: Caminho da requisição
  - `ip`: IP do cliente
- **Uso**: Monitorar tentativas de CSRF
- **Alertas**:
  - Critical: > 10 tentativas/minuto
  - Warning: > 5 tentativas/minuto

### unauthorized_access_total
- **Tipo**: Counter
- **Descrição**: Total de tentativas de acesso não autorizado
- **Labels**:
  - `path`: Caminho da requisição
  - `ip`: IP do cliente
  - `method`: Método HTTP
- **Uso**: Monitorar tentativas de acesso não autorizado
- **Alertas**:
  - Critical: > 20 tentativas/minuto
  - Warning: > 10 tentativas/minuto

## Visualização das Métricas

### Dashboards do Grafana

1. **Security Dashboard**
   - Violações de rate limit
   - Atividades suspeitas de IP
   - Logs de segurança
   - Distribuição de latência

2. **Security Audit Dashboard**
   - Eventos críticos de segurança
   - Eventos por tipo
   - Top IPs por eventos
   - Eventos por severidade
   - Hits de rate limit

## Consultas Úteis do Prometheus

### Taxa de Violações de Rate Limit
```promql
rate(rate_limit_violations_total[5m])
```

### Latência de Requisições (95º percentil)
```promql
histogram_quantile(0.95, sum(rate(request_latency_seconds_bucket[5m])) by (le, path))
```

### Top 10 IPs por Atividades Suspeitas
```promql
topk(10, sum(rate(suspicious_ip_activity_total[1h])) by (ip))
```

### Total de Tentativas de Ataque
```promql
sum(
  rate(xss_attempts_total[5m]) +
  rate(csrf_attempts_total[5m]) +
  rate(unauthorized_access_total[5m])
)
```

## Configuração de Alertas

### Exemplos de Regras de Alerta

```yaml
groups:
  - name: security_alerts
    rules:
      - alert: HighRateLimitViolations
        expr: sum(rate(rate_limit_violations_total[5m])) > 100
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: Alto número de violações de rate limit
          description: Mais de 100 violações de rate limit por minuto

      - alert: HighLatency
        expr: histogram_quantile(0.95, sum(rate(request_latency_seconds_bucket[5m])) by (le)) > 2
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: Alta latência nas requisições
          description: Latência p95 acima de 2 segundos

      - alert: SecurityAttackAttempts
        expr: sum(rate(xss_attempts_total[5m]) + rate(csrf_attempts_total[5m])) > 10
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: Alto número de tentativas de ataque
          description: Mais de 10 tentativas de ataque por minuto
```

## Troubleshooting

### Problemas Comuns

1. **Alto Número de Violações de Rate Limit**
   - Verificar logs para identificar os IPs
   - Analisar padrões de requisição
   - Considerar ajustes nos limites

2. **Alta Latência**
   - Verificar uso de recursos
   - Analisar queries lentas
   - Verificar conexões de rede

3. **Tentativas de Ataque**
   - Identificar origem dos ataques
   - Verificar padrões de payload
   - Atualizar regras de segurança

### Comandos Úteis

```bash
# Verificar métricas em tempo real
curl http://localhost:9090/metrics

# Verificar status do Prometheus
curl http://localhost:9090/-/healthy

# Verificar status do Alertmanager
curl http://localhost:9093/-/healthy

# Recarregar configurações do Prometheus
curl -X POST http://localhost:9090/-/reload

# Recarregar configurações do Alertmanager
curl -X POST http://localhost:9093/-/reload
```

## Manutenção

### Rotação de Dados

- Prometheus: Retenção de 15 dias
- Loki: Retenção de 30 dias
- Alertmanager: Silêncios expiram em 24h

### Backup

- Backup diário das configurações
- Backup semanal dos dados do Prometheus
- Backup mensal dos dashboards do Grafana

### Atualizações

- Atualizar Prometheus mensalmente
- Atualizar Grafana a cada release LTS
- Revisar regras de alerta trimestralmente 