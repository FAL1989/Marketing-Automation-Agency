export const CONFIG = {
  // Configurações gerais
  baseURL: 'http://localhost:8000',
  timeout: '30s',
  
  // Thresholds de performance
  thresholds: {
    http_req_duration: ['p(95)<500', 'p(99)<1000'],  // 95% < 500ms, 99% < 1s
    http_req_failed: ['rate<0.01'],                   // < 1% de falhas
    http_reqs: ['rate>100'],                          // > 100 RPS
  },
  
  // Cenários de teste
  scenarios: {
    // Teste de carga constante
    constant_load: {
      executor: 'constant-vus',
      vus: 50,
      duration: '5m',
    },
    
    // Teste de rampa
    ramp_up: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '2m', target: 50 },   // Ramp-up para 50 VUs
        { duration: '5m', target: 50 },   // Manter 50 VUs
        { duration: '2m', target: 0 },    // Ramp-down para 0
      ],
    },
    
    // Teste de pico
    stress_test: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '1m', target: 100 },  // Ramp-up rápido
        { duration: '2m', target: 100 },  // Manter carga alta
        { duration: '1m', target: 0 },    // Ramp-down rápido
      ],
    },
  },
  
  // Endpoints para teste
  endpoints: {
    templates: {
      path: '/api/templates',
      method: 'GET',
      weight: 30,  // 30% das requisições
    },
    content: {
      path: '/api/content',
      method: 'GET',
      weight: 30,  // 30% das requisições
    },
    generate: {
      path: '/api/generate',
      method: 'POST',
      weight: 20,  // 20% das requisições
    },
    analyze: {
      path: '/api/analyze',
      method: 'POST',
      weight: 20,  // 20% das requisições
    },
  },
}; 