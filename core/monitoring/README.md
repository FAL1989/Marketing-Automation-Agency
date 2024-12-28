# Sistema de Monitoramento

## Visão Geral
O sistema de monitoramento é responsável por coletar, armazenar e visualizar métricas de performance, uso e saúde do sistema, fornecendo insights em tempo real e alertas proativos.

## Arquitetura

### Estrutura do Módulo
```
monitoring/
├── collectors/         # Coletores de métricas
│   ├── system.py      # Métricas do sistema
│   ├── application.py # Métricas da aplicação
│   └── business.py    # Métricas de negócio
├── exporters/         # Exportadores para diferentes backends
├── alerts/            # Sistema de alertas
└── dashboards/        # Configurações dos dashboards
```

### Fluxo de Dados
1. Coleta de métricas pelos coletores
2. Processamento e agregação
3. Exportação para backends (Prometheus)
4. Visualização em dashboards (Grafana)
5. Geração de alertas quando necessário

## Métricas Coletadas

### Métricas do Sistema
- CPU, Memória, Disco
- Latência de rede
- Throughput de I/O
- Uso de recursos do Kubernetes

### Métricas da Aplicação
- Requisições por segundo
- Latência de endpoints
- Taxa de erros
- Uso de cache
- Performance de queries

### Métricas de Negócio
- Gerações de conteúdo
- Uso por cliente
- Custos de API
- Satisfação do usuário

## Uso

### Coletores de Métricas
```python
from core.monitoring import metrics

# Contador simples
requests_total = metrics.counter(
    'http_requests_total',
    'Total de requisições HTTP'
)
requests_total.inc()

# Histograma de latência
request_latency = metrics.histogram(
    'http_request_duration_seconds',
    'Latência das requisições HTTP',
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0]
)
with request_latency.time():
    # Código a ser medido
    process_request()

# Gauge para valores que sobem e descem
active_requests = metrics.gauge(
    'http_requests_active',
    'Requisições ativas no momento'
)
active_requests.inc()
# ... processar ...
active_requests.dec()
```

### Exportação de Métricas
```python
from core.monitoring import exporter

# Configurar endpoint /metrics
app.add_middleware(exporter.PrometheusMiddleware)
app.add_route("/metrics", exporter.metrics_endpoint)
```

### Alertas
```python
from core.monitoring import alerts

# Definir alerta
alert = alerts.Alert(
    name="high_error_rate",
    query='rate(http_errors_total[5m]) > 0.1',
    severity="critical",
    annotations={
        "summary": "Alta taxa de erros",
        "description": "Taxa de erros > 10% nos últimos 5 minutos"
    }
)

# Registrar alerta
alerts.register(alert)
```

## Dashboards

### Dashboard Principal
- Visão geral do sistema
- Métricas principais
- Status dos serviços
- Alertas ativos

### Dashboard de Performance
- Latência detalhada
- Throughput
- Uso de recursos
- Bottlenecks

### Dashboard de Negócio
- KPIs
- Tendências
- Custos
- Uso por cliente

## Configuração

### Variáveis de Ambiente
```env
# Prometheus
PROMETHEUS_PUSH_GATEWAY=http://pushgateway:9091
PROMETHEUS_RETENTION_DAYS=15

# Alertmanager
ALERTMANAGER_URL=http://alertmanager:9093
ALERT_SLACK_WEBHOOK=https://hooks.slack.com/...

# Grafana
GRAFANA_URL=http://grafana:3000
GRAFANA_API_KEY=your-api-key
```

### Configuração via Código
```python
from core.monitoring import config

# Configurar retenção de métricas
config.set_metrics_retention(days=15)

# Configurar exportação
config.configure_exporter(
    push_gateway="http://pushgateway:9091",
    job_name="aiagency-core"
)

# Configurar alertas
config.configure_alerts(
    slack_webhook="https://hooks.slack.com/...",
    email="alerts@aiagency.com"
)
```

## Alertas

### Níveis de Severidade
- **Critical**: Requer ação imediata
- **Warning**: Requer atenção em breve
- **Info**: Informativo apenas

### Canais de Notificação
- Slack
- Email
- SMS
- PagerDuty

### Exemplos de Alertas
```yaml
# Alta latência
- alert: HighLatency
  expr: http_request_duration_seconds > 1
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "Alta latência detectada"

# Erro de integração
- alert: IntegrationError
  expr: integration_errors_total > 0
  for: 1m
  labels:
    severity: critical
  annotations:
    summary: "Erro na integração detectado"
```

## Visualização

### Grafana
- URL: http://grafana:3000
- Autenticação: OAuth2
- Organização: AIAgency

### Dashboards Disponíveis
1. **Sistema**
   - `/d/system-overview`
   - `/d/system-resources`
   - `/d/system-network`

2. **Aplicação**
   - `/d/app-overview`
   - `/d/app-performance`
   - `/d/app-errors`

3. **Negócio**
   - `/d/business-kpis`
   - `/d/business-costs`
   - `/d/business-usage`

## Troubleshooting

### Verificação de Saúde
```bash
# Verificar status do Prometheus
curl http://prometheus:9090/-/healthy

# Verificar status do Alertmanager
curl http://alertmanager:9093/-/healthy

# Verificar status do Grafana
curl http://grafana:3000/api/health
```

### Problemas Comuns

1. **Métricas não aparecem**
```
Causa: Problema na coleta/exportação
Solução: Verificar endpoints e conectividade
```

2. **Alertas não disparam**
```
Causa: Configuração incorreta do Alertmanager
Solução: Verificar regras e conectividade
```

3. **Dashboards lentos**
```
Causa: Muitas métricas/retenção longa
Solução: Otimizar queries e retenção
```

## Manutenção

### Backup
- Configurações do Prometheus
- Regras de alertas
- Dashboards do Grafana

### Limpeza
- Rotação de logs
- Limpeza de métricas antigas
- Arquivamento de alertas

## Segurança

### Políticas
- Acesso restrito aos endpoints de métricas
- Autenticação em todas as UIs
- Logs de acesso

### Proteção de Dados
- Sanitização de labels
- Agregação de dados sensíveis
- Retenção controlada

## Contribuição

### Guidelines
1. Seguir padrões de naming
2. Documentar novas métricas
3. Criar dashboards úteis
4. Manter alertas precisos

### Processo
1. Propor mudanças
2. Revisar impacto
3. Testar em staging
4. Deploy em produção

## Suporte
- Docs: https://docs.aiagency.com/core/monitoring
- Chat: #monitoring-support
- Email: monitoring@aiagency.com 