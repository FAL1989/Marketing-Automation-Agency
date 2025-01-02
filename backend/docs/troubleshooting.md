# Guia de Troubleshooting

Este documento fornece instruções para diagnosticar e resolver problemas comuns na aplicação.

## Problemas de Segurança

### 1. Alto Número de Violações de Rate Limit

#### Sintomas
- Muitas requisições retornando 429 (Too Many Requests)
- Alertas de `HighRateLimitViolations`
- Aumento nas métricas `rate_limit_violations_total`

#### Diagnóstico
1. Verificar os IPs com mais violações:
```promql
topk(10, sum(rate(rate_limit_violations_total[5m])) by (ip))
```

2. Analisar os endpoints mais afetados:
```promql
topk(10, sum(rate(rate_limit_violations_total[5m])) by (path))
```

3. Verificar logs do sistema:
```bash
grep "rate limit exceeded" /var/log/app/security.log
```

#### Soluções
1. Ajustar limites de rate limit:
   ```python
   # config.py
   RATE_LIMIT_PER_MINUTE = 100  # Ajustar conforme necessário
   ```

2. Adicionar IPs à lista de exclusão:
   ```python
   RATE_LIMIT_EXCLUDE_IPS = ["1.2.3.4", "5.6.7.8"]
   ```

3. Implementar blacklist temporária:
   ```python
   await redis_client.setex(f"blacklist:{ip}", 3600, "1")
   ```

### 2. Tentativas de XSS/CSRF

#### Sintomas
- Aumento nas métricas `xss_attempts_total` ou `csrf_attempts_total`
- Alertas de `SecurityAttackAttempts`
- Logs de tentativas de injeção

#### Diagnóstico
1. Verificar payloads maliciosos:
```bash
grep "XSS attempt detected" /var/log/app/security.log
```

2. Analisar padrões de ataque:
```promql
sum(rate(xss_attempts_total[1h])) by (path)
```

3. Identificar origens dos ataques:
```promql
topk(10, sum(rate(csrf_attempts_total[1h])) by (ip))
```

#### Soluções
1. Atualizar regras de detecção:
   ```python
   # security.py
   XSS_PATTERNS = [
       r'<[^>]*script.*?>',
       r'javascript:',
       r'data:',
       r'vbscript:'
   ]
   ```

2. Reforçar headers de segurança:
   ```python
   SECURITY_HEADERS = {
       "Content-Security-Policy": "default-src 'self'",
       "X-XSS-Protection": "1; mode=block"
   }
   ```

3. Implementar validação adicional:
   ```python
   def validate_input(data: str) -> bool:
       return not any(pattern.search(data) for pattern in XSS_PATTERNS)
   ```

## Problemas de Performance

### 1. Alta Latência

#### Sintomas
- Alertas de `HighLatency`
- Aumento no p95 de `request_latency_seconds`
- Reclamações de usuários sobre lentidão

#### Diagnóstico
1. Verificar latência por endpoint:
```promql
histogram_quantile(0.95, sum(rate(request_latency_seconds_bucket[5m])) by (le, path))
```

2. Analisar uso de recursos:
```bash
top
htop
docker stats
```

3. Verificar conexões de rede:
```bash
netstat -an | grep ESTABLISHED
```

#### Soluções
1. Otimizar queries do banco de dados:
   ```python
   # Antes
   results = db.query(Model).all()
   
   # Depois
   results = db.query(Model).filter(...).limit(100)
   ```

2. Implementar caching:
   ```python
   @cache(ttl=3600)
   async def get_data():
       return await expensive_operation()
   ```

3. Ajustar configurações do servidor:
   ```python
   # uvicorn_config.py
   workers = multiprocessing.cpu_count() * 2 + 1
   ```

### 2. Problemas de Memória

#### Sintomas
- Alertas de `HighMemoryUsage`
- OOM Killer ativo
- Lentidão geral do sistema

#### Diagnóstico
1. Verificar uso de memória:
```bash
free -m
ps aux --sort=-%mem | head
```

2. Analisar memory leaks:
```python
import tracemalloc
tracemalloc.start()
```

3. Verificar logs do sistema:
```bash
dmesg | grep -i "out of memory"
```

#### Soluções
1. Otimizar uso de memória:
   ```python
   # Usar generators
   def process_items():
       for item in items:
           yield process(item)
   ```

2. Implementar limites de memória:
   ```python
   import resource
   resource.setrlimit(resource.RLIMIT_AS, (max_memory, hard_limit))
   ```

3. Ajustar configurações do GC:
   ```python
   import gc
   gc.set_threshold(700, 10, 5)
   ```

## Problemas de Monitoramento

### 1. Falhas no Prometheus

#### Sintomas
- Gaps nos dados
- Alertas não disparando
- Métricas ausentes

#### Diagnóstico
1. Verificar status do Prometheus:
```bash
curl -s http://localhost:9090/-/healthy
```

2. Analisar logs:
```bash
tail -f /var/log/prometheus/prometheus.log
```

3. Verificar targets:
```bash
curl -s http://localhost:9090/api/v1/targets
```

#### Soluções
1. Reiniciar Prometheus:
   ```bash
   systemctl restart prometheus
   ```

2. Recarregar configurações:
   ```bash
   curl -X POST http://localhost:9090/-/reload
   ```

3. Verificar espaço em disco:
   ```bash
   df -h /var/lib/prometheus
   ```

### 2. Problemas com Alertmanager

#### Sintomas
- Alertas não sendo enviados
- Notificações duplicadas
- Silêncios não funcionando

#### Diagnóstico
1. Verificar status:
```bash
curl -s http://localhost:9093/-/healthy
```

2. Analisar configuração:
```bash
amtool check-config /etc/alertmanager/config.yml
```

3. Verificar rotas:
```bash
amtool config routes show
```

#### Soluções
1. Reiniciar Alertmanager:
   ```bash
   systemctl restart alertmanager
   ```

2. Recarregar configurações:
   ```bash
   curl -X POST http://localhost:9093/-/reload
   ```

3. Limpar silêncios expirados:
   ```bash
   amtool silence expire all
   ```

## Manutenção Preventiva

### Checklist Diário
1. Verificar status dos serviços:
   ```bash
   systemctl status prometheus alertmanager grafana
   ```

2. Verificar uso de recursos:
   ```bash
   df -h
   free -m
   top
   ```

3. Verificar logs de erro:
   ```bash
   journalctl -u app -p err
   ```

### Checklist Semanal
1. Backup dos dados:
   ```bash
   backup_prometheus.sh
   backup_grafana.sh
   ```

2. Limpeza de logs antigos:
   ```bash
   find /var/log -name "*.log" -mtime +30 -delete
   ```

3. Verificar atualizações:
   ```bash
   apt update
   apt list --upgradable
   ```

### Checklist Mensal
1. Rotação de certificados:
   ```bash
   certbot renew
   ```

2. Revisão de configurações:
   ```bash
   prometheus_check_config.sh
   alertmanager_check_config.sh
   ```

3. Teste de recuperação:
   ```bash
   disaster_recovery_test.sh
   ``` 