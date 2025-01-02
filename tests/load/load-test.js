import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';
import { CONFIG } from './config.js';

// Métricas customizadas
const customMetrics = {
  failed_requests: new Rate('failed_requests'),
  cache_hits: new Rate('cache_hits'),
  request_duration: new Trend('request_duration'),
};

// Headers padrão
const headers = {
  'Content-Type': 'application/json',
  'Authorization': 'Bearer ${__ENV.API_TOKEN}',
};

// Dados de exemplo para requisições POST
const sampleData = {
  generate: {
    template_id: 1,
    parameters: {
      topic: "AI and Machine Learning",
      tone: "professional",
      length: "medium"
    }
  },
  analyze: {
    content: "Sample content for analysis",
    metrics: ["sentiment", "readability", "keywords"]
  }
};

// Função para selecionar endpoint baseado nos pesos
function selectEndpoint() {
  const random = Math.random() * 100;
  let sum = 0;
  
  for (const [name, config] of Object.entries(CONFIG.endpoints)) {
    sum += config.weight;
    if (random <= sum) {
      return { name, config };
    }
  }
  
  return Object.entries(CONFIG.endpoints)[0];
}

// Função principal de teste
export default function() {
  const { name, config } = selectEndpoint();
  const url = `${CONFIG.baseURL}${config.path}`;
  
  let response;
  const startTime = new Date();
  
  try {
    if (config.method === 'GET') {
      response = http.get(url, { headers });
    } else {
      response = http.post(url, JSON.stringify(sampleData[name]), { headers });
    }
    
    // Registrar duração
    const duration = new Date() - startTime;
    customMetrics.request_duration.add(duration);
    
    // Verificar cache hit
    if (response.headers['X-Cache'] === 'HIT') {
      customMetrics.cache_hits.add(1);
    }
    
    // Verificar resposta
    check(response, {
      'status is 200': (r) => r.status === 200,
      'response time OK': (r) => r.timings.duration < 500,
    });
    
    if (response.status !== 200) {
      customMetrics.failed_requests.add(1);
    }
    
  } catch (e) {
    customMetrics.failed_requests.add(1);
    console.error(`Error on ${config.method} ${url}: ${e.message}`);
  }
  
  // Pausa entre requisições
  sleep(1);
}

// Configuração do teste
export const options = {
  scenarios: CONFIG.scenarios,
  thresholds: CONFIG.thresholds,
  
  // Configurações extras
  noConnectionReuse: true,
  userAgent: 'K6 Load Test',
  
  // Métricas padrão do k6
  summaryTrendStats: ['avg', 'min', 'med', 'max', 'p(95)', 'p(99)'],
  
  // Tags para Prometheus
  tags: {
    testType: 'load-test',
    environment: 'staging'
  }
}; 