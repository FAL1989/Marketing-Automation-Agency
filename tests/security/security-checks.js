const axios = require('axios');
const https = require('https');
const fs = require('fs').promises;

const BASE_URL = process.env.BASE_URL || 'http://localhost:8000';

async function runSecurityChecks() {
  console.log('Iniciando verificações de segurança...\n');
  
  const results = {
    vulnerabilities: [],
    recommendations: []
  };

  try {
    // Teste de Headers de Segurança
    const response = await axios.get(BASE_URL, {
      validateStatus: () => true,
      rejectUnauthorized: true
    });

    const headers = response.headers;
    
    // Verificações de Headers
    const requiredHeaders = {
      'x-frame-options': 'DENY',
      'x-content-type-options': 'nosniff',
      'strict-transport-security': 'max-age=31536000; includeSubDomains',
      'x-xss-protection': '1; mode=block'
    };

    Object.entries(requiredHeaders).forEach(([header, expectedValue]) => {
      if (!headers[header] || headers[header] !== expectedValue) {
        results.vulnerabilities.push({
          type: 'missing_security_header',
          header,
          expectedValue,
          currentValue: headers[header] || 'não definido'
        });
      }
    });

    // Content Security Policy
    if (!headers['content-security-policy']) {
      results.vulnerabilities.push({
        type: 'missing_csp',
        description: 'Content Security Policy não está configurada'
      });
    }

    // Testes de Autenticação
    const authTests = await testAuthentication();
    results.vulnerabilities.push(...authTests.vulnerabilities);
    
    // Testes de Injeção
    const injectionTests = await testInjectionVulnerabilities();
    results.vulnerabilities.push(...injectionTests.vulnerabilities);

    // Testes de Rate Limiting
    const rateLimitTests = await testRateLimiting();
    results.vulnerabilities.push(...rateLimitTests.vulnerabilities);

  } catch (error) {
    console.error('Erro durante os testes de segurança:', error);
    results.vulnerabilities.push({
      type: 'test_error',
      description: error.message
    });
  }

  // Gerar recomendações baseadas nas vulnerabilidades encontradas
  results.recommendations = generateRecommendations(results.vulnerabilities);

  // Salvar relatório
  const reportPath = './security-report.json';
  await fs.writeFile(reportPath, JSON.stringify(results, null, 2));
  console.log(`Relatório de segurança salvo em ${reportPath}`);

  return results;
}

async function testAuthentication() {
  const results = { vulnerabilities: [] };
  
  try {
    // Teste de Força Bruta
    const bruteForceRes = await axios.post(`${BASE_URL}/auth/login`, {
      email: 'test@example.com',
      password: 'wrongpass'
    }, { validateStatus: () => true });

    if (!bruteForceRes.headers['x-ratelimit-remaining']) {
      results.vulnerabilities.push({
        type: 'missing_rate_limit',
        endpoint: '/auth/login',
        description: 'Endpoint de login não possui rate limiting'
      });
    }

    // Teste de JWT
    const validToken = await getValidToken();
    const expiredToken = generateExpiredToken();
    const modifiedToken = tamperWithToken(validToken);

    // Testar token expirado
    const expiredRes = await axios.get(`${BASE_URL}/api/protected`, {
      headers: { Authorization: `Bearer ${expiredToken}` },
      validateStatus: () => true
    });

    if (expiredRes.status !== 401) {
      results.vulnerabilities.push({
        type: 'jwt_expiration',
        description: 'Sistema aceita tokens expirados'
      });
    }

    // Testar token modificado
    const modifiedRes = await axios.get(`${BASE_URL}/api/protected`, {
      headers: { Authorization: `Bearer ${modifiedToken}` },
      validateStatus: () => true
    });

    if (modifiedRes.status !== 401) {
      results.vulnerabilities.push({
        type: 'jwt_tampering',
        description: 'Sistema aceita tokens modificados'
      });
    }

  } catch (error) {
    results.vulnerabilities.push({
      type: 'auth_test_error',
      description: error.message
    });
  }

  return results;
}

async function testInjectionVulnerabilities() {
  const results = { vulnerabilities: [] };
  const payloads = {
    sql: ["' OR '1'='1", "'; DROP TABLE users; --"],
    xss: ["<script>alert('xss')</script>", "<img src=x onerror=alert('xss')>"],
    nosql: ["{$gt: ''}", "{$where: 'sleep(1000)'}"]
  };

  try {
    // Teste cada endpoint com payloads maliciosos
    const endpoints = ['/api/users', '/api/search', '/api/content'];
    
    for (const endpoint of endpoints) {
      for (const [type, tests] of Object.entries(payloads)) {
        for (const payload of tests) {
          const res = await axios.post(`${BASE_URL}${endpoint}`, {
            query: payload
          }, { validateStatus: () => true });

          if (res.status !== 400) {
            results.vulnerabilities.push({
              type: `${type}_injection`,
              endpoint,
              payload,
              description: `Endpoint potencialmente vulnerável a injeção de ${type}`
            });
          }
        }
      }
    }
  } catch (error) {
    results.vulnerabilities.push({
      type: 'injection_test_error',
      description: error.message
    });
  }

  return results;
}

async function testRateLimiting() {
  const results = { vulnerabilities: [] };
  
  try {
    const endpoints = ['/api/generate', '/api/analyze', '/api/content'];
    
    for (const endpoint of endpoints) {
      const requests = Array(50).fill().map(() => 
        axios.get(`${BASE_URL}${endpoint}`, { validateStatus: () => true })
      );
      
      const responses = await Promise.all(requests);
      const hasRateLimit = responses.some(r => r.status === 429);
      
      if (!hasRateLimit) {
        results.vulnerabilities.push({
          type: 'missing_rate_limit',
          endpoint,
          description: 'Endpoint não possui proteção contra sobrecarga'
        });
      }
    }
  } catch (error) {
    results.vulnerabilities.push({
      type: 'rate_limit_test_error',
      description: error.message
    });
  }

  return results;
}

function generateRecommendations(vulnerabilities) {
  const recommendations = [];
  
  const recommendationMap = {
    missing_security_header: 'Configurar headers de segurança adequadamente no servidor',
    missing_csp: 'Implementar uma política de Content Security Policy',
    missing_rate_limit: 'Adicionar rate limiting para prevenir ataques de força bruta',
    jwt_expiration: 'Verificar corretamente a expiração dos tokens JWT',
    jwt_tampering: 'Implementar verificação de assinatura JWT mais robusta',
    sql_injection: 'Implementar prepared statements e validação de entrada',
    xss_injection: 'Implementar sanitização de entrada e CSP',
    nosql_injection: 'Implementar validação de entrada para queries NoSQL'
  };

  vulnerabilities.forEach(vuln => {
    if (recommendationMap[vuln.type]) {
      recommendations.push({
        type: vuln.type,
        recommendation: recommendationMap[vuln.type],
        priority: getPriority(vuln.type)
      });
    }
  });

  return recommendations;
}

function getPriority(vulnType) {
  const highPriority = ['sql_injection', 'xss_injection', 'jwt_tampering'];
  const mediumPriority = ['missing_rate_limit', 'jwt_expiration'];
  
  if (highPriority.includes(vulnType)) return 'high';
  if (mediumPriority.includes(vulnType)) return 'medium';
  return 'low';
}

// Modificar a exportação no final do arquivo
module.exports = { runSecurityChecks };

// Remover a execução automática
if (require.main === module) {
  runSecurityChecks().catch(console.error);
} 