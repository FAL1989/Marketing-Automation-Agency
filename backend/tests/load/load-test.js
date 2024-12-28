import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

// Métricas personalizadas
export const errorRate = new Rate('errors');

// Configuração do teste
export const options = {
  stages: [
    { duration: '30s', target: 10 },  // Rampa de subida para 10 usuários em 30s
    { duration: '1m', target: 10 },   // Mantém 10 usuários por 1 minuto
    { duration: '30s', target: 0 },   // Rampa de descida para 0 usuários em 30s
  ],
  thresholds: {
    http_req_duration: ['p(95)<5000'], // 95% das requisições devem completar em menos de 5s
    errors: ['rate<0.1'],             // Taxa de erro deve ser menor que 10%
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';

// Dados de teste
const testUser = {
  username: 'test@example.com',
  password: 'test123'
};

// Função principal
export default function () {
  // Login - usando application/x-www-form-urlencoded
  const loginRes = http.post(`${BASE_URL}/auth/login`, 
    Object.keys(testUser)
      .map(key => `${key}=${encodeURIComponent(testUser[key])}`)
      .join('&'),
    {
      headers: { 
        'Content-Type': 'application/x-www-form-urlencoded'
      },
    }
  );

  check(loginRes, {
    'login successful': (r) => r.status === 200,
    'has token': (r) => JSON.parse(r.body).access_token !== undefined,
  });

  errorRate.add(loginRes.status !== 200);

  if (loginRes.status === 200) {
    const token = JSON.parse(loginRes.body).access_token;
    const headers = {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    };

    // Teste de métricas
    const metricsRes = http.get(`${BASE_URL}/metrics`, { headers });
    check(metricsRes, {
      'metrics successful': (r) => r.status === 200,
    });
    errorRate.add(metricsRes.status !== 200);

    // Teste de geração de conteúdo
    const contentData = {
      title: 'Test Content',
      prompt: 'Test content generation',
      model: 'gpt-3.5-turbo',
      parameters: {
        max_tokens: 100
      }
    };

    // Primeiro cria o conteúdo
    const createContentRes = http.post(`${BASE_URL}/contents`, JSON.stringify(contentData), { headers });
    
    if (createContentRes.status === 200) {
      const contentId = JSON.parse(createContentRes.body).id;
      
      // Depois gera o conteúdo
      const generateContentRes = http.post(`${BASE_URL}/contents/${contentId}/generate`, null, { headers });
      
      check(generateContentRes, {
        'content generation successful': (r) => r.status === 200,
      });
      errorRate.add(generateContentRes.status !== 200);
    }
  }

  sleep(1);
} 