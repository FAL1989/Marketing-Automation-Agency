# Testes de Carga

Este diretório contém todos os testes de carga do projeto, incluindo testes de API, MFA e rate limiting.

## Estrutura

```
tests/load/
├── python/                    # Testes de carga em Python
│   ├── test_mfa_load.py      # Testes de carga do MFA
│   ├── test_api_endpoints_load.py  # Testes de carga dos endpoints
│   └── test_rate_limit_load.py     # Testes de carga do rate limiting
├── load-test.js              # Testes de carga em JavaScript
├── config.js                 # Configurações dos testes JS
└── run-tests.sh             # Script para executar todos os testes
```

## Como Executar

1. Testes JavaScript:
```bash
node load-test.js
```

2. Testes Python:
```bash
pytest python/test_*.py -v
```

3. Todos os Testes:
```bash
./run-tests.sh
```

## Métricas Coletadas

- Tempo de resposta (média, p95, p99)
- Taxa de erro
- Throughput
- Uso de recursos (CPU, memória)
- Taxa de sucesso do MFA
- Efetividade do rate limiting

## Configuração

Ajuste os parâmetros de teste no arquivo `config.js` para os testes JavaScript e nas próprias classes de teste para os testes Python.

## Resultados

Os resultados dos testes são salvos em:
- Testes JS: `load-test-summary.json`
- Testes Python: Relatório do pytest e logs específicos

## Integração com CI/CD

Os testes de carga são executados automaticamente:
- A cada release
- Diariamente em ambiente de staging
- Sob demanda através do pipeline de CI 