const axios = require('axios');
const https = require('https');
const { execSync } = require('child_process');

const BASE_URL = process.env.BASE_URL || 'http://localhost:3001';

async function runSecurityChecks() {
  console.log('Iniciando verificações de segurança...\n');
  
  const results = {
    passed: [],
    failed: [],
    warnings: []
  };

  // 1. Verificar HTTPS
  try {
    const response = await axios.get(BASE_URL, {
      httpsAgent: new https.Agent({
        rejectUnauthorized: true
      })
    });
    if (response.protocol === 'https:') {
      results.passed.push('HTTPS está configurado corretamente');
    } else {
      results.failed.push('HTTPS não está habilitado');
    }
  } catch (error) {
    results.failed.push(`Erro na verificação HTTPS: ${error.message}`);
  }

  // 2. Verificar Headers de Segurança
  try {
    const response = await axios.get(`${BASE_URL}/health`);
    const headers = response.headers;
    
    // CORS
    if (!headers['access-control-allow-origin'] || headers['access-control-allow-origin'] === '*') {
      results.warnings.push('CORS está configurado de forma muito permissiva');
    } else {
      results.passed.push('CORS está configurado corretamente');
    }

    // Content Security Policy
    if (headers['content-security-policy']) {
      results.passed.push('CSP está configurado');
    } else {
      results.warnings.push('CSP não está configurado');
    }

    // X-Frame-Options
    if (headers['x-frame-options']) {
      results.passed.push('X-Frame-Options está configurado');
    } else {
      results.warnings.push('X-Frame-Options não está configurado');
    }

    // X-Content-Type-Options
    if (headers['x-content-type-options'] === 'nosniff') {
      results.passed.push('X-Content-Type-Options está configurado corretamente');
    } else {
      results.warnings.push('X-Content-Type-Options não está configurado');
    }
  } catch (error) {
    results.failed.push(`Erro na verificação de headers: ${error.message}`);
  }

  // 3. Verificar Rate Limiting
  try {
    const requests = Array(20).fill().map(() => 
      axios.get(`${BASE_URL}/api/health`)
    );
    
    const responses = await Promise.allSettled(requests);
    const rateLimited = responses.some(r => r.status === 'rejected' && r.reason.response?.status === 429);
    
    if (rateLimited) {
      results.passed.push('Rate limiting está funcionando');
    } else {
      results.failed.push('Rate limiting não está funcionando como esperado');
    }
  } catch (error) {
    results.failed.push(`Erro na verificação de rate limiting: ${error.message}`);
  }

  // 4. Verificar Dependências
  try {
    const npmAudit = execSync('npm audit --json', { encoding: 'utf8' });
    const auditResults = JSON.parse(npmAudit);
    
    if (auditResults.vulnerabilities?.high || auditResults.vulnerabilities?.critical) {
      results.failed.push('Vulnerabilidades críticas encontradas nas dependências');
    } else if (auditResults.vulnerabilities?.moderate || auditResults.vulnerabilities?.low) {
      results.warnings.push('Vulnerabilidades de baixa severidade encontradas nas dependências');
    } else {
      results.passed.push('Nenhuma vulnerabilidade encontrada nas dependências');
    }
  } catch (error) {
    results.warnings.push(`Erro na verificação de dependências: ${error.message}`);
  }

  // 5. Verificar Autenticação
  try {
    const response = await axios.get(`${BASE_URL}/api/protected`);
    if (response.status === 401) {
      results.passed.push('Endpoint protegido está corretamente configurado');
    } else {
      results.failed.push('Endpoint protegido está acessível sem autenticação');
    }
  } catch (error) {
    if (error.response?.status === 401) {
      results.passed.push('Endpoint protegido está corretamente configurado');
    } else {
      results.failed.push(`Erro na verificação de autenticação: ${error.message}`);
    }
  }

  // Gerar relatório
  console.log('\n=== Relatório de Segurança ===\n');
  
  console.log('✅ Testes Passados:');
  results.passed.forEach(msg => console.log(`  - ${msg}`));
  
  console.log('\n⚠️ Avisos:');
  results.warnings.forEach(msg => console.log(`  - ${msg}`));
  
  console.log('\n❌ Falhas:');
  results.failed.forEach(msg => console.log(`  - ${msg}`));

  // Salvar resultados
  const fs = require('fs');
  const reportPath = './security-report.json';
  fs.writeFileSync(reportPath, JSON.stringify(results, null, 2));
  console.log(`\nRelatório detalhado salvo em: ${reportPath}`);

  // Retornar status
  return results.failed.length === 0;
}

// Executar testes
runSecurityChecks()
  .then(success => {
    if (!success) {
      console.log('\n❌ Verificações de segurança falharam!');
      process.exit(1);
    }
    console.log('\n✅ Verificações de segurança concluídas com sucesso!');
  })
  .catch(error => {
    console.error('\n❌ Erro durante as verificações:', error);
    process.exit(1);
  }); 