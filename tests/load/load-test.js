import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Counter } from 'k6/metrics';

// Métricas personalizadas
const metrics = {
  errors: new Rate('errors'),
  authFailures: new Counter('auth_failures'),
  rateLimitHits: new Counter('rate_limit_hits'),
  successfulRequests: new Counter('successful_requests')
};

export const options = {
  stages: [
    { duration: '1m', target: 50 },
    { duration: '2m', target: 50 },
    { duration: '1m', target: 100 },
    { duration: '3m', target: 100 },
    { duration: '1m', target: 150 },
    { duration: '3m', target: 150 },
    { duration: '1m', target: 0 },
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'],
    errors: ['rate<0.05'],
    auth_failures: ['count<10'],
    rate_limit_hits: ['count<50'],
    successful_requests: ['count>1000']
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';
const tokenCache = new Map();

// Função para obter token de autenticação
async function getAuthToken(username) {
  if (tokenCache.has(username)) return tokenCache.get(username);

  const loginRes = http.post(`${BASE_URL}/auth/login`, {
    username: 'admin@test.com',
    password: 'test@123',
  }, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
  });

  if (loginRes.status === 200) {
    const token = JSON.parse(loginRes.body).access_token;
    tokenCache.set(username, token);
    return token;
  }

  metrics.authFailures.add(1);
  return null;
}

// Função para gerar dados de teste
function generateTestData() {
  return {
    title: `Test ${Date.now()}`,
    content: 'Test content',
    metadata: {
      source: 'load-test',
      timestamp: new Date().toISOString()
    }
  };
}

export default async function () {
  const username = 'admin@test.com';
  const token = await getAuthToken(username);

  if (!token) {
    metrics.errors.add(1);
    sleep(1);
    return;
  }

  const params = {
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
  };

  // Test group 1: API Health Check
  {
    const healthRes = http.get(`${BASE_URL}/health`);
    check(healthRes, {
      'health check successful': (r) => r.status === 200,
    });
  }

  sleep(0.5);

  // Test group 2: Protected Endpoints
  {
    const testRes = http.get(`${BASE_URL}/protected/test`, params);
    
    if (testRes.status === 429) {
      metrics.rateLimitHits.add(1);
    } else if (testRes.status === 200) {
      metrics.successfulRequests.add(1);
    } else {
      metrics.errors.add(1);
    }

    check(testRes, {
      'protected endpoint accessible': (r) => r.status === 200,
      'rate limit headers present': (r) => 
        r.headers['X-RateLimit-Limit'] !== undefined &&
        r.headers['X-RateLimit-Remaining'] !== undefined,
    });
  }

  sleep(0.5);

  // Test group 3: Content Creation
  {
    const contentRes = http.post(
      `${BASE_URL}/content`,
      JSON.stringify(generateTestData()),
      params
    );

    if (contentRes.status === 429) {
      metrics.rateLimitHits.add(1);
    } else if (contentRes.status === 201 || contentRes.status === 200) {
      metrics.successfulRequests.add(1);
    } else {
      metrics.errors.add(1);
    }

    check(contentRes, {
      'content creation successful': (r) => r.status === 201 || r.status === 200,
      'response has id': (r) => JSON.parse(r.body).id !== undefined,
    });
  }

  sleep(0.5);

  // Test group 4: Metrics
  {
    const metricsRes = http.get(`${BASE_URL}/metrics`, params);
    
    if (metricsRes.status === 429) {
      metrics.rateLimitHits.add(1);
    } else if (metricsRes.status === 200) {
      metrics.successfulRequests.add(1);
    } else {
      metrics.errors.add(1);
    }

    check(metricsRes, {
      'metrics endpoint accessible': (r) => r.status === 200,
      'metrics data present': (r) => r.body.length > 0,
    });
  }

  sleep(1);
}

export function handleSummary(data) {
  return {
    'stdout': JSON.stringify(data, null, 2),
    './load-test-summary.json': JSON.stringify(data),
  };
} 